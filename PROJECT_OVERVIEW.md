# Civ4Chess — Project Overview

_Written 2026-11-21 from a read-through of the source and git history (28 commits, 2025-03-28 → 2026-02-07) plus the
uncommitted working tree (last touched ~2026-07-05). Items marked **(confirmed)** were verified in code; **(hypothesis)** were inferred
and need an in-game check._

---

## 0. Current state and next steps (updated 2026-11-26, Phase 2 working in game)

**Branches** (the maintainer merges PRs, Claude never does): `main` is untouched since Feb 2026. All Claude-assisted work
(Phases 0–2) lives on **`claude-assisted`**, which branches off `main`. New work goes on one feature branch off `claude-assisted`,
with a PR back into it. The old `phase0-stabilize` / `phase1-python-rules` / `phase2-engine` branches were rolled up into it
(PR #1: phase2 → phase1; then phase1 → `claude-assisted`).

**2026-11-26 update (supersedes the Phase 1 notes below where they differ)**
- Phase 1 crashed Civ4 at the main menu: extra fields in `CvSelectionGroup` break the exe. Fixed by keeping that state in `CvGame`
  (`d30ff5f`). Phase 1 then verified in game: legal-move table, slides, captures, en passant, CHESS-SYNC OK.
- Phase 2 (`phase2-engine`): Stockfish plays Black. Verified in game: a full game to checkmate (36 moves) with captures by both
  sides, long-range human captures, en passant by White; CHESS-SYNC OK throughout. Also fixed `CvUnit::attack` reporting the
  attacker's start square after a quick combat had already moved it (showed up as `d4d4`).
- Also verified in game: White kingside castling (rook follows, CHESS-SYNC OK); en passant by White (5.exd6 in the first
  Stockfish game).
- Still unverified in game: queenside castling, castling by Stockfish, en passant by Stockfish, promotion, draws.
  Out-of-game tests: 24, all pass.
- In-game testing by Claude works (launch/menu checks are scripted), but Civ4 does not receive Claude's right-clicks, so the
  maintainer plays the moves and Claude reads `PythonDbg.log`.
- Remaining Phase 2 items: engine HTTP call still blocks the game for ~1 s per reply; difficulty setting; colour choice
  (human is always White); the old `CvGame::update`/`setChessMove` AI path is now unused.

**Done**
- Phase 0: token/Stockfish path moved to env vars, bridge engine kept alive, engine-reply crash fixed, castling/promotion/null-pointer
  bugs fixed, README, `.gitignore`, work committed.
- Phase 1 (coded, DLL built, **not yet verified in the game**): python-chess is the referee. `CivChessObj.legal_moves_string()` →
  `CyGame.setLegalMoves` → `CvUnit::canMoveInto` only allows listed moves; pieces skip the pathfinder (`groupPathTo` slides them in one
  go, or `attack()`s from where they stand); castling rook via `CyGame.slideChessPiece`; en passant victim killed from Python;
  promotion always a queen; draws end the game with a message; `CHESS-SYNC` log lines compare the python-chess board with the map.
- 17 out-of-game tests: `C:\Python26\python -B Tests\test_chess_utils.py` (all pass).

**Decisions made by the maintainer (do not re-ask)**
- Promotion: auto-queen for now (popup later). Draws: message and stop. No save/load/serialization for now: assume a game is
  finished in one sitting. Keep Civ-style walking/slide animations where feasible (castling may be an exception).
- Stockfish mode first, Lichess later. No automated play against real/random Lichess players. Lichess testing will be run past the
  maintainer first, using either a second account they log into or a token + API docs for self-play.
- One feature branch per phase is enough (not one per task).

**Unverified in-game (check these first)**
1. A capture from distance: does the attacker animate acceptably, and does it land on the square afterwards?
2. Castling: rook slides along with the king; black queenside check fixed.
3. Pawn promotion on a capture (the old promotion callback with wrong coordinates was removed).
4. En passant removes the right pawn.
5. Turn flow: how turns advance with two players, and that the other side can move after one side has used its moves.
6. `ENGINE_OPPONENT_ENABLED` is **False** until Phase 2 (the engine's reply must move Civ units first).
Look for `CHESS-SYNC OK` / `CHESS-SYNC MISMATCH` in `Logs/PythonDbg.log`, and `xml.log` for DLL messages.

**Testing:** see the 2026-11-26 update above (Claude launches Civ4 and reads logs; the maintainer plays the moves).

**Next steps**
1. Maintainer does a short in-game check of the list above (or we add a log-only replay hook so one launch produces a full report).
2. Fix what that finds; merge `phase1-python-rules` (maintainer).
3. Phase 2: engine reply moves Civ units. Add one "opponent" interface (Stockfish now, Lichess later); route engine moves through the
   same apply-move path as human moves (including promotion, castling rook, en passant); make the HTTP call non-blocking; fix the
   `CvGame::update` non-human-active-player gating; difficulty/time per move.
4. Phase 3 (needs maintainer sign-off first): Lichess Board API (seek with time control, challenge by username, move streaming, colors).
5. Phase 4: UI screens, clocks, polish.

---

## 1. What the project is

A Civilization IV: Beyond the Sword mod in which two civilizations play chess on an 8×8 region of a 10×10 map. Civ units act as chess
pieces; the game core DLL enforces piece movement, removes Civ mechanics (upkeep, promotions, XP, automation, etc.), and makes every
attack succeed so that "attack" = "capture". A python-chess board, kept in sync from DLL callbacks, detects checkmate and triggers a
custom Checkmate victory.

Work in progress (uncommitted) adds:
- **Stockfish opponent** via a local FastAPI "bridge server".
- **Lichess online play**: a Civ4 Python screen that issues a Lichess challenge through the bridge and polls for acceptance.

---

## 2. Architecture

```
 Civ4 BtS engine (closed source exe)
        │  calls exported DLL functions
        ▼
 CvGameCoreDLL.dll  (C++, CvGameCoreDLL/)
   • movement rules per piece (CvUnit::canMoveInto / canMoveThrough / baseMoves)
   • forced capture-wins combat, disabled Civ actions
   • calls Python CvEventInterface.onPathCompleted(unitId, sx, sy, ex, ey)
   • exposes CyGame.setChessMove(...) and ChessPieceTypes to Python
        │  Boost.Python 1.32 (CyXxx wrappers + Cy*Interface*.cpp registrations)
        ▼
 Mod Python 2.4 (Assets/Python/)
   • CvEventInterface → CvCiv4ChessEvents (event manager subclass)
   • ChessUtils.CivChessObj wraps python-chess 0.20.0 board
   • CvLichessConnection screen (currently not wired up)
        │  urllib HTTP, form-encoded, http://127.0.0.1:8000
        ▼
 BridgeServer (Python 3.13, FastAPI)  BridgeServer/bridge_server.py
   • /engine-move → python-chess 1.x SimpleEngine → local Stockfish exe
   • /challenge/{user}, /challenge, /account/playing → lichess.org REST API (bearer token)
```

**Why a bridge server?** Civ4's embedded Python is 2.4 with no SSL-capable modern HTTP client, no `json`, and it cannot run modern
python-chess or the Lichess API comfortably. The bridge moves all modern-network and engine work out of process. (Inferred design rationale.)

### Languages / frameworks
- C++03-era MSVC 2003 (Civ4 SDK), Boost 1.32, Boost.Python; build via NMake `Makefile` (vcxproj is an NMake wrapper).
- Python 2.4 inside the game; vendored `chess.py` (python-chess 0.20.0, GPL-3, hand-patched to import on 2.4) and `simplejson` (2010-era).
- Python 3.13 + FastAPI 0.135, requests, python-chess 1.11 (venv in `BridgeServer/.venv`).
- Civ4 XML for units, victory, audio, text; WorldBuilder save for the board map.

---

## 3. Key files

### DLL (`CvGameCoreDLL/`, ~200 files, nearly all stock Firaxis source; edits marked `// Civ4Chess:`)
| File | Chess changes |
|---|---|
| `CvEnums.h` | `ChessPieceTypes` enum (NO/PAWN/ROOK/KNIGHT/BISHOP/QUEEN/KING) |
| `CvChessTypes.h` | `ChessMove` struct (start/end x,y) |
| `CvUnit.h/.cpp` | `m_eChessPieceType`, `m_bDeletePromotedUnit`; per-piece rules in `canMoveInto`; rewritten `canMoveThrough` (only knights pass occupied plots); `baseMoves` by piece (pawn/king 1, knight 2, sliders 8); attacker always wins (`getDefenderCombatValues`); promotion-to-queen in `finishMoves`; promoted pawn deleted in `doTurn`; no XP, promotions, upgrades, fortify/sleep/sentry/hold/recon/scrap/explore, great-people actions; visibility 10; combat messages suppressed; `attack()` notifies Python |
| `CvSelectionGroup.h/.cpp` | records `pathStartPlot` on MOVE_TO/ROUTE_TO; on mission completion: `finishMoves`, face N/S, call Python `onPathCompleted`; pawn double-step treated as one atomic move |
| `CvGame.h/.cpp` | `m_chessMove` + `setChessMove`; `CvGame::update` applies a queued move for a non-human active player via `setXY` and notifies Python |
| `CvPlayer.h/.cpp` | `initUnit(..., ChessPieceTypes)`; unit cost/supply forced to 0; removed debug popup |
| `CvUnitAI.cpp` | `AI_update` short-circuits to `MISSION_SKIP` — AI never moves pieces itself |
| `Cy*.cpp/.h`, `Cy*Interface*.cpp` | Python exposure: `CyGame.setChessMove`, `CyUnit.getChessPieceType`, `ChessPieceTypes` enum, 6-arg `CyPlayer.initUnit` |
| `Makefile` | Civ4SDK NMake makefile; WIP: `CIV4_PATH` points to this mod's dir (Boost/Python24 live in `CvGameCoreDLL/`), fastdep disabled, `/NODEFAULTLIB:libcmt` |

### Mod Python (`Assets/Python/`)
| File | Role | Tracked? |
|---|---|---|
| `EntryPoints/CvEventInterface.py` | DLL→Python entry; uses `CvCiv4ChessEvents` as event manager; adds `onPathCompleted` | yes (modified) |
| `CvCiv4ChessEvents.py` | `setupPieces` (ANCIENT pieceset), war declaration at start, `onPathCompleted` board sync + WIP engine call + checkmate victory + move sound | yes (modified) |
| `ChessUtils.py` | `CivChessObj` (board, `process_move` builds UCI from coords), `make_engine_move` (WIP) | yes (modified) |
| `CivUtils.py` | plot/unit equality helpers (currently unused) | yes |
| `chess.py` | vendored python-chess 0.20.0 | yes |
| `ChessGameState.py` | module-global Lichess game id | **untracked** |
| `CvEventManager.py` | copy of BtS file; Dawn of Man shown via direct call; commented-out Lichess screen popup; winner unit rotation on victory | **untracked** |
| `EntryPoints/CvScreensInterface.py` | copy of BtS file; imports `CvLichessConnection`; registration commented out | **untracked** |
| `Screens/CvScreenEnums.py` | adds `LICHESS_CONNECTION = 101` | **untracked** |
| `Screens/CvLichessConnection.py` | Lichess challenge screen (Dawn-of-Man layout clone, username edit box, polling in `update`) | **untracked** |
| `simplejson/` | vendored JSON lib (includes macOS `._*` junk files and `.pyc`s) | **untracked** |

### XML / assets
- `Units/CIV4UnitInfos.xml` — all units `iCombat=1`, `iCombatLimit=100` (so every piece can capture); promotions/abilities/upgrades stripped.
- `GameInfo/CIV4VictoryInfo.xml` + `Text/CIV4GameText_Victories.xml` — `VICTORY_CHECKMATE`.
- `Audio/*` + `sounds/ambient/chess_move.wav` — `AS3D_CHESS_MOVE` sound.
- `Units/CIV4PromotionInfos.xml`, `Civilizations/CIV4TraitInfos.xml` — early full-visibility promotion and trait tweaks.
- `XML/Art/CIV4ArtDefines_Unit.xml` — **untracked, byte-identical to the BtS original** (no effect; probably a start on custom piece art).
- `PublicMaps/Civ4Chess.Civ4WorldBuilderSave` — 10×10 map; units are placed by Python, not the save.
- `Civ4Chess.ini` — mod config (name still "TestBtsDll"/"Generic Mod"). `.ini.bak` / `.ini.txt` are leftovers.

### Bridge server (`BridgeServer/`, entirely untracked)
- `bridge_server.py` — FastAPI app; form-encoded endpoints; global Stockfish `SimpleEngine` started at import; Lichess bearer token and
  Stockfish path hard-coded.
- `requirements.txt` — fastapi, requests, python-chess (pins the transitional `python-chess==1.999` package). uvicorn/fastapi-cli present in venv but not listed.

---

## 4. Execution paths

**Game start.** Civ4 loads the mod → `CvEventInterface` instantiates `CvCiv4ChessEvents` (creates a fresh `chess.Board()`) →
`onGameStart` → `setupPieces()` calls `CyPlayer.initUnit(unitType, x, y, NO_UNITAI, facing, ChessPieceType)` for 32 units → teams 0/1
declare war → message "Let's play chess".

**Human move.** Player selects a unit and right-clicks a plot → `CvSelectionGroup::pushMission(MISSION_MOVE_TO)` stores `pathStartPlot`
→ pathfinder consults `canMoveThrough` / `canMoveInto` (piece rules) → unit moves → `updateMission` on completion: `finishMoves()`, set
facing, call Python `onPathCompleted(id, sx, sy, ex, ey)` → Python finishes moves of all active-player units (one move per turn),
`CivChessObj.process_move` builds a UCI string from coords and `board.push()`es it → checkmate? `setWinner(activePlayer, 0)` : message + sound.

**Capture.** Moving onto an enemy → `CvUnit::attack` → `updateCombat` (attacker always wins) → also calls `onPathCompleted` with the attacker's
current coords and target plot.

**Promotion.** `finishMoves` on a pawn on the last rank spawns a Spy (`CHESS_PIECE_QUEEN`) on the same plot, flags the pawn for deletion in
`doTurn`, and calls `onPathCompleted` (see bugs below).

**Engine move (WIP, uncommitted).** After the human move is pushed, `make_engine_move(board.fen())` POSTs to `/engine-move` → bridge runs
Stockfish → returns `{"san", "uci"}` → Python pushes it onto its own board. The intended second half — telling the DLL to physically move
the Civ unit via `CyGame.setChessMove(...)` → `CvGame::update` — is **not wired** in the current code (an earlier committed version only
had a hard-coded test call `setChessMove(5,7,5,5)` in `onEndGameTurn`).

**Lichess challenge (WIP, disabled).** `CvLichessConnection` would show a screen; clicking the button (widget data 555) POSTs
`/challenge/kroger12` (username hard-coded, edit box ignored), saves the challenge id in `ChessGameState`; `update()` polls every 2 s
`/account/playing` (accepted → close) and `/challenge` (gone → declined). The screen registration is commented out in
`CvScreensInterface.py` and `CvEventManager.py`. No move streaming/sending to Lichess exists yet.

### Representation
- **Board state:** two copies — physical Civ units on plots (DLL) and a python-chess `Board` held in the `CvCiv4ChessEvents` instance
  (Python). They are synced only by `onPathCompleted` callbacks; no reconciliation exists.
- **Players/colors:** Civ player 0 = White (ranks 1–2), player 1 = Black (ranks 7–8); hard-coded in DLL (`m_eOwner == 0`) and Python.
- **Identity:** Lichess identity = whoever owns the hard-coded token in the bridge. No user accounts/config in the mod.
- **Game id:** `ChessGameState.lichessGameID` (module global, not persisted).

---

## 5. Git history and milestones

| Date | Milestone |
|---|---|
| 2025-03-28 | Initial commit: map, unit XML, king art, first Python event file (pure Python/XML mod) |
| 2025-03-30 → 04-05 | Full-board visibility promotion, dynamic piece placement, movement/XP tweaks |
| 2025-04-20 | **"Refactored for BtS"** — imported the full BtS SDK DLL source (~210 files, 263k lines); renamed ini/map; switched to `CvCiv4ChessEvents` |
| 2025-04-25 | python-chess 0.20.0 vendored and patched for Python 2.4 |
| 2025-04-27 → 04-29 | First DLL rules: no stacking, `ChessPieceTypes` on units, knight hopping; Python cleanup (`ChessUtils`, `CivUtils`) |
| 2025-07-05 → 07-19 | Strip Civ mechanics (upkeep, promotions, upgrades, skip/recon); piece-specific move counts and limitations |
| 2025-12-26 → 12-29 | More movement constraints; AI movement disabled |
| 2026-01-10 → 01-19 | DLL → Python `onPathCompleted` callback; `setChessMove` "manual move" path for AI; knight/pawn fixes; **Checkmate victory + move sound** |
| 2026-02-07 | Pawn promotion "sort of working"; all units can attack (last commit) |
| 2026-02 → 07 (uncommitted) | Lichess screen, `ChessGameState`, simplejson, BridgeServer (Stockfish + Lichess), engine call in `onPathCompleted`, unit id in callbacks, Makefile path fixes |

Abandoned/unfinished evidence: commented-out `face_unit_to_direction` calls; commented-out Lichess screen registration;
empty "check for castling / en passant" stubs in `finishMoves`; untracked identical ArtDefines copy; `normalEventManager` unused;
`pickle`, `CivUtils` imported but unused; ini still named "TestBtsDll".

---

## 6. Feature status

**Complete (confirmed in code; in-game behaviour not re-verified)**
- Board setup with piece roles; per-piece movement geometry incl. knight jumps and blocking for sliders.
- One move per turn; captures always succeed; Civ mechanics stripped; AI never moves on its own.
- python-chess mirror of human moves; checkmate → Checkmate victory; move sound.

**Partial**
- Castling: king may move two squares if path empty and rook present, but the rook never moves; no "has moved"/through-check rules.
- Promotion: auto-queen only; Python sync for it is broken (below).
- AI/engine moves: DLL `setChessMove` path exists; Stockfish call exists; the two are not connected.
- Lichess: challenge + polling prototype only; screen disabled; no game streaming, move submission, clocks, or color handling.

**Missing**
- En passant; check/pin legality (DLL lets you leave your king in check); stalemate/draw handling in the game; resign/draw offers.
- Time controls, random color assignment, seek/random-opponent pairing, username challenge UI.
- Save/load support for chess state.

---

## 7. Known bugs and technical debt

> **Phase 0 status (2026-11-21, uncommitted, DLL not yet rebuilt):** fixed #1, #2, #3 (coords + `q` suffix + duplicate-report
> guard), #4, #6, #8 (parsing/URLs; username still hard-coded), #9, #10 (token and Stockfish path now env vars — the old token
> must still be revoked on lichess.org). Checkmate now picks the winner from the side to move instead of the active player.
> Still open: #5, #7 (partly mitigated by the pseudo-legal guard), and the engine reply not moving Civ units.

Confirmed by reading code (original list):
1. **`onPathCompleted` crashes after the engine call**: `make_engine_move` returns `result["uci"]` (a string), then the caller does
   `engine_move["uci"]` → `TypeError`. Every human move currently raises in Python after the move is pushed.
2. **Bridge kills Stockfish after one move**: `engine.quit()` inside `/engine-move`; the global engine is unusable for later requests.
3. **Promotion callback args wrong**: `finishMoves` passes `(id, Y∓1, Y, X, Y)` instead of `(id, X, Y∓1, X, Y)`; and `process_move` never adds
   a promotion suffix (`e7e8` vs `e7e8q`), so the python-chess board diverges. Log line prints the piece type after it was reset.
4. **Black queenside castling** checks `plot(1, 1)->isUnit()` instead of `plot(1, 8)` (`CvUnit::canMoveInto`).
5. **Chess fields not serialized**: `m_eChessPieceType`, `m_bDeletePromotedUnit` missing from `CvUnit::read/write`; Python board not pickled.
   Saving/loading a game will break rules and board sync.
6. `CvSelectionGroup::pathStartPlot` is never initialised in the constructor/reset; dereferenced in `updateMission`.
7. python-chess `board.push()` does not validate legality, so any DLL/Python disagreement silently corrupts the mirror board.
8. `CvLichessConnection.update`: `list_games()`/`list_challenges()` return raw strings but are indexed as dicts → `TypeError`.
   URLs with trailing slashes (`/challenge/`, `/account/playing/`) don't match the FastAPI routes (FastAPI would redirect — urllib on
   Py2.4 may not follow a 307; **hypothesis**). Username hard-coded to `kroger12`.
9. Victory text key mismatch: XML references `TXT_KEY_VICTORY_CHECKMATE_PEDIA`, text file defines `TXT_KEY_VICTORY_PEDIA_CHECKMATE`.
10. **Secret in source**: Lichess API token hard-coded in `bridge_server.py` (untracked so far). Should be revoked/rotated and moved to an env var before any commit.

Hypotheses needing an in-game check:
- `CvGame::update` only applies `m_chessMove` when `getActivePlayer()` is non-human. In single-player `getActivePlayer()` is normally the
  local human, so this path may never fire outside hotseat/autoplay.
- A capture may call `onPathCompleted` twice (from `attack()` and again when the move mission completes), double-pushing to the board.
- `onPathCompleted` uses `getActivePlayer()` to end moves; when triggered by an AI/engine move it would act on the human's units.

Technical debt:
- Hard-coded absolute paths (`sys.path.append(...)` in two Python files, Makefile `CIV4_PATH`, Stockfish path).
- Duplicate rook/queen/bishop slide logic in `canMoveInto`; large copy of `canMoveInto` pasted into `canMoveThrough`.
- Color logic hard-coded as player 0/1 throughout DLL and Python.
- Debug output everywhere (`sys.stdout.write`, `xml.log` on every `doTurn`).
- `.gitignore` ignores `*.bat` (build scripts never tracked); `simplejson/` contains `._*` and `.pyc` files; `__pycache__` not ignored.
- No tests; no README content.
- GPL-3 `chess.py` vendored into an MIT-licensed repo — licensing worth a look before distribution.

---

## 8. Recommended roadmap

**Phase 0 — Stabilise the baseline (small, do first)**
1. Rotate the Lichess token; load it (and Stockfish path) from env/config in the bridge. Fix `.gitignore` (`__pycache__`, `*.pyc`, `._*`).
2. Commit the WIP in logical chunks (DLL arg change, bridge, Lichess screen, engine call) so there is a recoverable baseline.
3. Fix the confirmed bugs 1–4, 6, 9; remove `engine.quit()`.
4. Write a short README: prerequisites, build, run bridge, launch mod.

**Phase 1 — Make Python (python-chess) the single source of truth for rules**
- On every callback, validate the move with `board.is_legal()` before pushing; reject/undo illegal Civ moves.
- Better: have the DLL ask Python for legal destinations (or expose a "can move" Python callback) so check, pins, castling, en passant and
  promotion come from python-chess instead of re-implementing them in C++.
- Implement the rook move for castling, en-passant removal, and promotion choice (popup) driven by the python-chess move.
- Persist chess state: serialise the chess fields in the DLL and store FEN/move list in Civ script data.

**Phase 2 — Local engine opponent end-to-end**
- Engine reply → `CyGame.setChessMove` → DLL moves/captures the Civ unit → callback ignored for already-applied moves.
- Fix/replace the `isHuman` gating in `CvGame::update`; make the engine call non-blocking (the game freezes during the HTTP call today).
- Difficulty / time-per-move settings.

**Phase 3 — Online play via Lichess Board API**
- Bridge: OAuth/token per user, `POST /api/board/seek` (random opponent + time control), challenge by username, stream
  `/api/board/game/stream/{id}` and push moves with `/api/board/game/{id}/move/{uci}`; expose a simple polling endpoint for Civ.
- Mod: random/assigned color → map Lichess color to Civ player 0/1 (and flip the camera); show clocks; resign/draw/abort.
- Robust polling in a screen `update()` loop (Civ Python cannot stream).

**Phase 4 — Interface polish**
- Proper "Play chess" menu/screen (seek with time control, challenge by username, incoming challenges), in-game clock HUD, move list,
  game-over screen, piece art set (ArtDefines), cleaner mod name/ini.

---

## 9. Open questions for the maintainer
- Is the intended model "Civ client plays as you against a Lichess opponent" (Board API), or something else?
- Has the `setChessMove` AI-move path ever worked in-game, and in which game setup (SP vs hotseat)?
- Which DLL build route do you actually use (VS NMake project, `nmake` directly, or `build_dll.bat`)?
- Is the Lichess token in `bridge_server.py` a real account token (it should be rotated)?
- Should the uncommitted WIP be committed as-is, or reviewed and split first?
