import sys
import chess
import urllib

sys.path.append(r"C:\Program Files (x86)\Steam\steamapps\common\Sid Meier's Civilization IV Beyond the Sword\Beyond the Sword\Mods\Civ4Chess\Assets\Python")
import simplejson as json 

# define game status constants
GAME_STATUS_CHECKMATE = 0
GAME_STATUS_STALEMATE = 1
GAME_STATUS_IN_PROGRESS = 2
GAME_STATUS_IGNORED = 3

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


class CivChessObj:
    """
    A wrapper class for the python-chess 0.20.0 API with included functionality
    for interfacing with Civ 4 gameplay
    """

    def __init__(self):
        """Instantiates a ChessUtils object"""

        self.board = chess.Board()

    def process_move(self, start_x, start_y, end_x, end_y):
        """ 
        Updates board state with a valid move
        """

        # assemble UCI move
        move_uci_string = convert_x_coord_to_file(start_x)
        sys.stdout.write("\tFrom util: move_uci_string = " + move_uci_string)
        move_uci_string += str(start_y)
        sys.stdout.write("\tFrom util: move_uci_string = " + move_uci_string)
        move_uci_string += convert_x_coord_to_file(end_x)
        sys.stdout.write("\tFrom util: move_uci_string = " + move_uci_string)
        move_uci_string += str(end_y)
        sys.stdout.write("\tFrom util: move_uci_string = " + move_uci_string)

        from_square = chess.SQUARE_NAMES.index(move_uci_string[0:2])
        to_square = chess.SQUARE_NAMES.index(move_uci_string[2:4])

        # the DLL always promotes pawns to a queen, so mirror that here
        piece = self.board.piece_at(from_square)
        if piece is not None and piece.piece_type == chess.PAWN:
            if chess.square_rank(to_square) in (0, 7):
                move_uci_string += "q"

        move = chess.Move.from_uci(move_uci_string)

        # The DLL can report the same move more than once (e.g. a promotion is
        # reported by both the move and the promotion code). Ignore reports that
        # cannot apply to the current position instead of corrupting the board.
        if not self.board.is_pseudo_legal(move):
            sys.stdout.write("\tFrom util: ignoring move " + move_uci_string + " (not applicable to current board)")
            return GAME_STATUS_IGNORED

        # input move to board
        self.board.push(move)

        # return game status code
        if self.board.is_checkmate():
            sys.stdout.write("\tFrom util: checkmate")
            return GAME_STATUS_CHECKMATE
        elif self.board.is_stalemate():
            sys.stdout.write("\tFrom util: stalemate")
            return GAME_STATUS_STALEMATE
        else:
            sys.stdout.write("\tFrom util: in progress")
            return GAME_STATUS_IN_PROGRESS

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