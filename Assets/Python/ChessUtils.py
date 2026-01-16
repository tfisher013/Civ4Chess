import sys
import chess

# define game status constants
GAME_STATUS_CHECKMATE = 0
GAME_STATUS_STALEMATE = 1
GAME_STATUS_IN_PROGRESS = 2


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

        # input move to board
        self.board.push(chess.Move.from_uci(move_uci_string))

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
