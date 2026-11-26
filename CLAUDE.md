# CLAUDE.md — Civ4Chess

Civilization IV: Beyond the Sword mod that turns the game into a chess board, with work in progress on
Stockfish play and Lichess online play. See `PROJECT_OVERVIEW.md` for the full picture and feature status.

## Components

| Component | Path | Language / runtime |
|---|---|---|
| Game core DLL (rules, movement, combat) | `CvGameCoreDLL/` → built to `Assets/CvGameCoreDLL.dll` | C++ (MSVC 2003 toolkit, Boost.Python 1.32) |
| Mod Python (board setup, board state, events, UI) | `Assets/Python/` | **Python 2.4** (Civ4's embedded interpreter) |
| Bridge server (Stockfish + Lichess proxy) | `BridgeServer/bridge_server.py` | Python 3.13, FastAPI, python-chess 1.x |
| Game data | `Assets/XML/`, `PublicMaps/Civ4Chess.Civ4WorldBuilderSave` | Civ4 XML / WB save |

Data flow: Civ4 engine ↔ DLL ↔ (Boost.Python) mod Python ↔ HTTP `127.0.0.1:8000` ↔ bridge server ↔ Stockfish / lichess.org.

## Entry points

- `Assets/Python/EntryPoints/CvEventInterface.py` — the DLL calls `onEvent` and the custom `onPathCompleted(argsList)`;
  routes to `CvCiv4ChessEvents.CvCiv4ChessEvents` (subclass of the mod's copy of `CvEventManager`).
- `Assets/Python/CvCiv4ChessEvents.py` — `onGameStart` places pieces; `onPathCompleted` syncs the python-chess board.
- `Assets/Python/ChessUtils.py` — `CivChessObj` (python-chess board wrapper), `make_engine_move` (HTTP to bridge).
- DLL hooks that call Python `onPathCompleted(unitId, startX, startY, endX, endY)`:
  `CvSelectionGroup::updateMission` (once the piece stands on its destination), `CvUnit::attack`, `CvGame::update` (applies `setChessMove`).
- **Rules live in python-chess.** After every move Python calls `CyGame.setLegalMoves("e2e4 g1f3 ...")`; `CvUnit::canMoveInto`
  only allows moves on that list (`CvGame::isChessMoveLegal`). A move in progress stays allowed via `setActiveChessMove` until it completes.
  Chess pieces skip the pathfinder: `CvSelectionGroup::groupPathTo` slides them to the destination in one go (or attacks from where they stand).
  Python applies castling (`CyGame.slideChessPiece` for the rook) and en passant (kills the victim) after `process_move`. Promotion is always a queen.
- **Stockfish is the opponent** (`ENGINE_OPPONENT_ENABLED` in `CvCiv4ChessEvents.py`): after a human move the reply is queued and played
  from `onGameUpdate` once the human piece stands on its square (a capture is reported when the attack starts). `playEngineReply`
  removes the captured piece, `slideChessPiece`s the mover, then gives the human's units their moves back (no Civ end-turn needed).
- **Colour choice:** closing Dawn of Man opens a White/Black/Random popup (`showColourChoice`); `startChessGame(white_player)` then
  places the pieces, calls `CyGame.setChessWhitePlayer` (the DLL faces pieces by colour after a move), turns the camera for Black,
  and queues Stockfish's first move if it plays White. Map Civ player ↔ colour only through `playerOfColour` / `white_player`.
- The event manager lives for the whole Civ4 session, not one game: per-game state goes in `resetGameState()` (called from `onGameStart`).
- Bridge: `POST /engine-move`, `POST /challenge/{username}`, `GET /challenge`, `GET /account/playing`.

## Key conventions

- Board = map plots x,y in **1..8** on a 10×10 map (border of 0/9). x 1..8 → files a..h, y → rank directly.
- The human is always Civ player 0 and Stockfish player 1; either can play White. White is always on ranks 1–2 (python-chess WHITE),
  Black on ranks 7–8, so board coordinates never depend on the colour choice. Promotion in the DLL goes by rank (8 or 1).
- A piece's chess role is `CvUnit::m_eChessPieceType` (`ChessPieceTypes` enum in `CvEnums.h`, exposed to Python), set via the
  extra 6th arg of `CyPlayer.initUnit(...)`. Unit art is cosmetic: Warrior=pawn, Axeman=rook, Chariot=knight, Archer=bishop, Spy=queen, Prophet=king.
- All DLL edits are marked with a `// Civ4Chess:` comment. Keep doing this — it is the only way to tell mod code from stock Firaxis code.
- Python in `Assets/` must stay **Python 2.4-compatible**: no `with`, no `x if c else y`, no f-strings, no `json` stdlib (use the vendored `simplejson`),
  `urllib` not `urllib2`/`requests`. `chess.py` is python-chess **0.20.0** hand-patched for 2.4; do not replace it with a newer version.
- Logging: Python uses `sys.stdout.write` (goes to Civ4 PythonDbg.log when logging is enabled); DLL uses `gDLL->logMsg("xml.log", ...)`.

## Build / run

- DLL (verified 2026-11-21, takes ~3 min — run with a long timeout). Civ4 must be closed (check for a `Civ*` process first).
  From PowerShell, in the mod root:
  ```
  cmd /c "call `"C:\Program Files (x86)\Microsoft Visual Studio 10.0\VC\vcvarsall.bat`" x86 >nul && cd /d CvGameCoreDLL && nmake TARGET=Release clean /NOLOGO && nmake TARGET=Release source_list /NOLOGO && nmake TARGET=Release /NOLOGO"
  ```
  VS2010 supplies `nmake`; the compiler is VC++ Toolkit 2003 from `C:\Program Files (x86)\Civ4SDK`. The Makefile copies the result
  to `Assets/CvGameCoreDLL.dll` (lines `COPY "Release\CvGameCoreDLL.dll" "..\Assets\."` = success). The run then ends with
  `NMAKE : fatal error U1077: '--objectextension=pch'` — **expected and harmless**: the trailing `fastdep` step has no `FD` set.
  Treat real `error C`/`LNK` lines, or a missing copy line, as failure. `build_dll.bat` files are gitignored and not used.
- Bridge: from `BridgeServer/`, activate `.venv`, set `STOCKFISH_PATH` and `LICHESS_TOKEN` env vars, then
  `fastapi dev bridge_server.py --port 8000` (mod expects port 8000). See `README.md`.
- Test: `C:Python26python -B Tests	est_chess_utils.py` (out-of-game, Python 2.x, covers rules/castling/en passant/promotion/draws).
  In-game verification is manual: launch BtS → Load mod Civ4Chess → play the `Civ4Chess` public map; `PythonDbg.log` gets `CHESS-SYNC` lines comparing the python-chess board with the map.
  python-chess 0.20.0 needs Python 2.7 `collections.Counter` for repetition checks, which Civ4 lacks: use `CivChessObj` (own repetition counting), never `board.can_claim_*`.

## Warnings

- Secrets (Lichess token) and machine paths (Stockfish) come from env vars in the bridge. Never hard-code them again.
- Don't touch vendored/third-party code without reason: `CvGameCoreDLL/Boost-1.32.0`, `CvGameCoreDLL/Python24`, `Assets/Python/simplejson`,
  `Assets/Python/chess.py`, `BridgeServer/.venv`. Never read or modify the binary DLL/PDB/obj outputs.
- The WB map's `StartingX/StartingY` are deliberately off the 10×10 map: a starting plot on the board gets Civ's free
  settler/worker/scout units. The camera is pointed at the board from Python when Dawn of Man closes (`CvScreensInterface.py`).
- **Never add data members to `CvSelectionGroup`**: two extra ints crashed Civ4 at the main menu (the exe depends on its
  layout). Put new chess state in `CvGame`, which is safe to extend.
- Most files in `CvGameCoreDLL/` are stock Firaxis SDK source; changes ripple into save format and Python bindings.
  New `CvUnit` fields must be added to `read`/`write` (current chess fields are not serialized — saves lose piece types).
- Changing a `Cy*` signature requires updating the matching `Cy*Interface*.cpp` Boost.Python registration.
- Several files contain absolute paths to this install (`ChessUtils.py`, `CvLichessConnection.py`, `Makefile`).
- `ChessUtils.CivChessObj.process_move` ignores moves that are not pseudo-legal on its board (the DLL can report a move twice,
  e.g. promotions) and adds the `q` suffix for pawn promotions. Keep that in mind when adding DLL callbacks.
- The working tree has substantial uncommitted WIP (engine integration, Lichess screen). Never discard or revert it.
