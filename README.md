# Civ4Chess

A Civilization IV: Beyond the Sword mod that turns the game into chess: two civilizations, 32 units acting as chess pieces
on an 8×8 board, with movement rules enforced in a custom game core DLL and the position mirrored in python-chess so that
checkmate ends the game. Work in progress: a Stockfish opponent and online play through Lichess, both via a small local
"bridge server".

See [PROJECT_OVERVIEW.md](PROJECT_OVERVIEW.md) for architecture, feature status and roadmap.

## Requirements

- Civilization IV: Beyond the Sword (Steam install; the mod lives in `Beyond the Sword/Mods/Civ4Chess`).
- To rebuild the DLL: the Civ4 SDK toolchain in `C:\Program Files (x86)\Civ4SDK` (Microsoft Visual C++ Toolkit 2003 +
  Windows SDK), plus Boost 1.32 and Python 2.4 headers/libs in `CvGameCoreDLL/Boost-1.32.0` and `CvGameCoreDLL/Python24`
  (not tracked in git).
- For the bridge server: Python 3.13 and a Stockfish executable.

## Building the DLL

Open `CvGameCoreDLL/CvGameCoreDLL.sln` and build the **Release** configuration (an NMake project that runs the
`CvGameCoreDLL/Makefile`). The Makefile copies the result to `Assets/CvGameCoreDLL.dll`. Close Civ4 first, otherwise the
DLL cannot be overwritten.

## Running the bridge server

The mod talks to the bridge at `http://127.0.0.1:8000`. Configuration comes from environment variables:

| Variable | Purpose |
|---|---|
| `STOCKFISH_PATH` | Full path to the Stockfish executable (needed for `/engine-move`) |
| `LICHESS_TOKEN` | Lichess personal API token (needed for the `/challenge` and `/account` endpoints) |

```powershell
cd BridgeServer
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:STOCKFISH_PATH = "C:\path\to\stockfish.exe"
$env:LICHESS_TOKEN = "<your token>"
fastapi dev bridge_server.py --port 8000
```

Never put the token in source files.

## Playing

1. Start the bridge server (optional; without it the engine reply is skipped).
2. Launch Beyond the Sword → **Advanced → Load a Mod → Civ4Chess**.
3. Start a game on the `Civ4Chess` public map. After the Dawn of Man screen, choose White, Black or Random; Stockfish plays
   the other side.

Python output goes to Civ4's `PythonDbg.log` when logging is enabled in `CivilizationIV.ini`.

## License

MIT (see `LICENSE`). `Assets/Python/chess.py` is python-chess 0.20.0 (GPL-3.0) and `Assets/Python/simplejson`
is simplejson (MIT); they keep their own licenses.
