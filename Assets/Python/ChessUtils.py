import sys
import chess
import urllib

sys.path.append(r"C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\Mods\Civ4Chess\Assets\Python")
import simplejson as json

# game status constants returned by CivChessObj.process_move
GAME_STATUS_CHECKMATE = 0
GAME_STATUS_STALEMATE = 1
GAME_STATUS_IN_PROGRESS = 2
GAME_STATUS_IGNORED = 3
GAME_STATUS_DRAW = 4  # insufficient material, fifty-move rule or threefold repetition

BRIDGE_URL = "http://127.0.0.1:8000"


def convert_x_coord_to_file(x_coord):
    """
    Converts an x coordinate from the map into a chessboard file [a-h].

    Args:
        x_coord: an integer with domain [1, 8]

    Returns:
        The chessboard file corresponding to the provided x coordinate from the map
    """

    if x_coord > 0 and x_coord < 9 and type(x_coord) == int:
        return chess.FILE_NAMES[x_coord - 1]
    else:
        raise Exception(
            "Invalid map x coordinate input: "
            + str(x_coord)
            + " ("
            + str(type(x_coord))
            + ")"
        )


def square_to_map_coords(square):
    """Converts a python-chess square index to (x, y) map coordinates, both in [1, 8]."""
    return chess.square_file(square) + 1, chess.square_rank(square) + 1


class CivChessObj:
    """
    A wrapper class for the python-chess 0.20.0 API with included functionality
    for interfacing with Civ 4 gameplay.

    python-chess is the single source of truth for the rules. After every move the
    caller should send legal_moves_string() to the DLL so that the game only lets
    the player make legal moves.
    """

    def __init__(self):
        """Instantiates a ChessUtils object"""

        self.board = chess.Board()
        self.game_over = False

        # How often each position has occurred, for threefold repetition. python-chess
        # 0.20.0 does this with collections.Counter, which Python 2.4 does not have.
        self.position_counts = {}
        self._count_position()

        # details of the most recent move applied by process_move, for the caller
        # to mirror on the Civ map (castling rook, en passant victim)
        self.last_move = None
        self.last_was_castling = False
        self.last_was_en_passant = False
        self.last_rook_move = None  # ((from_x, from_y), (to_x, to_y)) when castling
        self.last_en_passant_victim = None  # (x, y) of the captured pawn

    def get_status(self):
        """Returns the GAME_STATUS_* code for the current position."""
        board = self.board
        if board.is_checkmate():
            return GAME_STATUS_CHECKMATE
        if board.is_stalemate():
            return GAME_STATUS_STALEMATE
        if (
            board.is_insufficient_material()
            or board.halfmove_clock >= 100  # fifty-move rule (mate/stalemate were handled above)
            or self.position_counts.get(board._transposition_key(), 0) >= 3
        ):
            # the mod ends the game on any draw instead of waiting for a claim
            return GAME_STATUS_DRAW
        return GAME_STATUS_IN_PROGRESS

    def _count_position(self):
        key = self.board._transposition_key()
        self.position_counts[key] = self.position_counts.get(key, 0) + 1

    def legal_moves_string(self):
        """
        Returns the legal moves for the side to move as space separated UCI
        strings (e.g. "e2e4 g1f3"), or "" once the game is over. This is what
        the DLL uses to decide which moves a player may make.
        """
        if self.game_over:
            return ""
        moves = []
        for move in self.board.legal_moves:
            # pawns always promote to a queen for now, so leave out underpromotions
            if move.promotion is not None and move.promotion != chess.QUEEN:
                continue
            moves.append(move.uci())
        return " ".join(moves)

    def process_move(self, start_x, start_y, end_x, end_y):
        """
        Updates board state with a move reported by the DLL.

        Returns:
            A GAME_STATUS_* code. GAME_STATUS_IGNORED means the report did not
            describe a legal move in the current position (for example a duplicate
            report) and the board was not changed.
        """

        # assemble UCI move
        move_uci_string = (
            convert_x_coord_to_file(start_x)
            + str(start_y)
            + convert_x_coord_to_file(end_x)
            + str(end_y)
        )

        from_square = chess.SQUARE_NAMES.index(move_uci_string[0:2])
        to_square = chess.SQUARE_NAMES.index(move_uci_string[2:4])

        # the DLL always promotes pawns to a queen, so mirror that here
        piece = self.board.piece_at(from_square)
        if piece is not None and piece.piece_type == chess.PAWN:
            if chess.square_rank(to_square) in (0, 7):
                move_uci_string += "q"

        move = chess.Move.from_uci(move_uci_string)

        # The DLL can report the same move more than once (e.g. a capture is reported
        # by the attack and by the end of the move mission). Ignore reports that are
        # not legal in the current position instead of corrupting the board.
        if self.game_over or not self.board.is_legal(move):
            sys.stdout.write("\tFrom util: ignoring move " + move_uci_string + " (not legal in current position)")
            return GAME_STATUS_IGNORED

        self._record_special_moves(move)
        self.board.push(move)
        self._count_position()

        status = self.get_status()
        if status != GAME_STATUS_IN_PROGRESS:
            self.game_over = True
        return status

    def _record_special_moves(self, move):
        """Notes castling / en passant details; must be called before the move is pushed."""
        self.last_move = move
        self.last_was_castling = self.board.is_castling(move)
        self.last_was_en_passant = self.board.is_en_passant(move)
        self.last_rook_move = None
        self.last_en_passant_victim = None

        rank = chess.square_rank(move.from_square)
        if self.last_was_castling:
            if self.board.is_kingside_castling(move):
                rook_from_file, rook_to_file = 7, 5
            else:
                rook_from_file, rook_to_file = 0, 3
            self.last_rook_move = (
                square_to_map_coords(chess.square(rook_from_file, rank)),
                square_to_map_coords(chess.square(rook_to_file, rank)),
            )

        if self.last_was_en_passant:
            # the captured pawn sits beside the capturing pawn's origin, on the destination file
            victim = chess.square(chess.square_file(move.to_square), rank)
            self.last_en_passant_victim = square_to_map_coords(victim)

    def push_uci_move(self, uci):
        """
        Applies a move given in UCI notation (e.g. from the engine). Returns the
        GAME_STATUS_* code, or GAME_STATUS_IGNORED if the move is not legal.
        """
        move = chess.Move.from_uci(uci)
        if self.game_over or not self.board.is_legal(move):
            return GAME_STATUS_IGNORED
        self._record_special_moves(move)
        self.board.push(move)
        self._count_position()
        status = self.get_status()
        if status != GAME_STATUS_IN_PROGRESS:
            self.game_over = True
        return status


def make_engine_move(fen, time_limit=1.0):
    """
    Asks the bridge server for an engine move.

    Returns:
        The engine's move as a UCI string (e.g. "e7e5"), or None if the
        bridge server could not be reached or returned an error.
    """
    params = {
        "fen": str(fen),
        "time_limit": time_limit,
    }
    body = urllib.urlencode(params)
    try:
        response = urllib.urlopen(BRIDGE_URL + "/engine-move", body)
        result = json.loads(response.read())
    except Exception, e:
        sys.stdout.write("make_engine_move failed: " + str(e))
        return None

    sys.stdout.write("make_engine_move response: " + str(result))
    if not isinstance(result, dict) or not result.has_key("uci"):
        return None
    return result["uci"]
