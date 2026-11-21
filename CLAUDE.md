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
  `CvSelectionGroup::updateMission`, `CvUnit::attack`, `CvUnit::finishMoves` (pawn promotion), `CvGame::update` (applies `setChessMove`).
- Bridge: `POST /engine-move`, `POST /challenge/{username}`, `GET /challenge`, `GET /account/playing`.

## Key conventions

- Board = map plots x,y in **1..8** on a 10×10 map (border of 0/9). x 1..8 → files a..h, y → rank directly.
- Player 0 starts on ranks 1–2 (python-chess WHITE); player 1 on ranks 7–8. (`setupPieces` comments say the opposite — comments are wrong.)
- A piece's chess role is `CvUnit::m_eChessPieceType` (`ChessPieceTypes` enum in `CvEnums.h`, exposed to Python), set via the
  extra 6th arg of `CyPlayer.initUnit(...)`. Unit art is cosmetic: Warrior=pawn, Axeman=rook, Chariot=knight, Archer=bishop, Spy=queen, Prophet=king.
- All DLL edits are marked with a `// Civ4Chess:` comment. Keep doing this — it is the only way to tell mod code from stock Firaxis code.
- Python in `Assets/` must stay **Python 2.4-compatible**: no `with`, no `x if c else y`, no f-strings, no `json` stdlib (use the vendored `simplejson`),
  `urllib` not `urllib2`/`requests`. `chess.py` is python-chess **0.20.0** hand-patched for 2.4; do not replace it with a newer version.
- Logging: Python uses `sys.stdout.write` (goes to Civ4 PythonDbg.log when logging is enabled); DLL uses `gDLL->logMsg("xml.log", ...)`.

## Build / run

- DLL: open `CvGameCoreDLL/CvGameCoreDLL.sln` (NMake project) → Release, or run `nmake` with the `Makefile` (needs Civ4SDK in
  `C:\Program Files (x86)\Civ4SDK`: VC++ Toolkit 2003 + WindowsSDK; `YOURMOD=..` copies the DLL to `Assets/`).
  `build_dll.bat` files exist but are gitignored and not the canonical path. **Ask before building**; Civ4 must be closed to overwrite the DLL.
- Bridge: from `BridgeServer/`, activate `.venv`, set `STOCKFISH_PATH` and `LICHESS_TOKEN` env vars, then
  `fastapi dev bridge_server.py --port 8000` (mod expects port 8000). See `README.md`.
- Test: no automated tests. Verification is manual: launch BtS → Load mod Civ4Chess → play the `Civ4Chess` public map.

## Warnings

- Secrets (Lichess token) and machine paths (Stockfish) come from env vars in the bridge. Never hard-code them again.
- Don't touch vendored/third-party code without reason: `CvGameCoreDLL/Boost-1.32.0`, `CvGameCoreDLL/Python24`, `Assets/Python/simplejson`,
  `Assets/Python/chess.py`, `BridgeServer/.venv`. Never read or modify the binary DLL/PDB/obj outputs.
- Most files in `CvGameCoreDLL/` are stock Firaxis SDK source; changes ripple into save format and Python bindings.
  New `CvUnit` fields must be added to `read`/`write` (current chess fields are not serialized — saves lose piece types).
- Changing a `Cy*` signature requires updating the matching `Cy*Interface*.cpp` Boost.Python registration.
- Several files contain absolute paths to this install (`ChessUtils.py`, `CvLichessConnection.py`, `Makefile`).
- `ChessUtils.CivChessObj.process_move` ignores moves that are not pseudo-legal on its board (the DLL can report a move twice,
  e.g. promotions) and adds the `q` suffix for pawn promotions. Keep that in mind when adding DLL callbacks.
- The working tree has substantial uncommitted WIP (engine integration, Lichess screen). Never discard or revert it.
