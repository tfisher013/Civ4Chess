import os
from contextlib import asynccontextmanager
from typing import Annotated, Optional

from fastapi import FastAPI, Form, HTTPException
from pydantic import BaseModel, Field
import requests
import chess
import chess.engine

# Configuration comes from the environment so that secrets and machine-specific
# paths never live in source control.
#   LICHESS_TOKEN   - personal API token from https://lichess.org/account/oauth/token
#   STOCKFISH_PATH  - full path to the Stockfish executable
LICHESS_TOKEN = os.environ.get("LICHESS_TOKEN")
STOCKFISH_PATH = os.environ.get("STOCKFISH_PATH")

LICHESS_API = "https://lichess.org/api"

# The Stockfish process is started once and shared by all requests.
engine: Optional[chess.engine.SimpleEngine] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global engine
    if STOCKFISH_PATH:
        engine = chess.engine.SimpleEngine.popen_uci(STOCKFISH_PATH)
    else:
        print("STOCKFISH_PATH is not set; /engine-move is disabled.")
    yield
    if engine is not None:
        engine.quit()
        engine = None


app = FastAPI(lifespan=lifespan)


class ChallengeRequest(BaseModel):
    # Use Field(alias=...) to handle the dot notation in form keys
    clock_limit: Optional[int] = Field(None, alias="clock.limit")
    clock_increment: Optional[int] = Field(None, alias="clock.increment")
    rated: bool = False
    color: str = "random"
    variant: str = "standard"
    fen: str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
    rules: Optional[str] = None


class MoveRequest(BaseModel):
    fen: str
    time_limit: float = 1.0


def lichess_headers() -> dict:
    if not LICHESS_TOKEN:
        raise HTTPException(status_code=500, detail="LICHESS_TOKEN is not set on the bridge server")
    return {"Authorization": f"Bearer {LICHESS_TOKEN}"}


@app.post("/engine-move")
def get_stockfish_move(data: Annotated[MoveRequest, Form()]):
    if engine is None:
        raise HTTPException(status_code=503, detail="Stockfish is not running (set STOCKFISH_PATH)")

    try:
        # Validate FEN and set up board
        board = chess.Board(data.fen)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid FEN string")

    if board.is_game_over():
        raise HTTPException(status_code=400, detail="The game is already over")

    try:
        result = engine.play(board, chess.engine.Limit(time=data.time_limit))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"san": board.san(result.move), "uci": result.move.uci()}


@app.post("/challenge/{username}")
def challenge(
    username: str,
    # Annotated[ChallengeRequest, Form()] tells FastAPI to parse Form data into the model
    data: Annotated[ChallengeRequest, Form()],
):
    payload = data.model_dump(by_alias=True, exclude_none=True)
    # Manually fix the boolean fields for the Lichess API
    for key, value in payload.items():
        if isinstance(value, bool):
            payload[key] = str(value).lower()
    print(str(payload))

    headers = lichess_headers()
    headers["Content-Type"] = "application/x-www-form-urlencoded"
    return requests.post(
        f"{LICHESS_API}/challenge/{username}",
        headers=headers,
        data=payload,
    ).json()


@app.get("/challenge")
def list_challenges():
    return requests.get(f"{LICHESS_API}/challenge", headers=lichess_headers()).json()


@app.get("/account/playing")
def get_games():
    return requests.get(f"{LICHESS_API}/account/playing", headers=lichess_headers()).json()
