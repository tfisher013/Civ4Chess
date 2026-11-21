from CvPythonExtensions import *
import sys
import Popup as PyPopup
import pickle
import CvEventManager
from CvScreenEnums import *
from PyHelpers import *
import CvUtil
import CvGameUtils
from ChessUtils import *
from CivUtils import *

import ChessGameState
import chess

# globals
gc = CyGlobalContext()
localText = CyTranslator()

# When True, each human move is answered by a Stockfish move from the bridge server
# (applied to the python-chess board only, see onPathCompleted).
ENGINE_OPPONENT_ENABLED = True


def face_unit_to_direction(pUnit, iDesiredDir):
    """
    Rotates a CyUnit to a specific DirectionType.
    :param pUnit: The CyUnit instance
    :param iDesiredDir: Integer (0-7) representing the target DirectionType
    """
    if iDesiredDir < 0 or iDesiredDir > 7:
        return

    # Keep rotating until the unit's direction matches the target
    # We loop because the API doesn't allow instant setting
    while pUnit.getFacingDirection() != iDesiredDir:
        iCurrentDir = pUnit.getFacingDirection()
        
        # Calculate the clockwise distance
        # (Target - Current) % 8 gives us steps needed in clockwise direction
        diff = (iDesiredDir - iCurrentDir) % 8
        
        if diff <= 4:
            # It's shorter or equal to go clockwise
            pUnit.rotateFacingDirectionClockwise()
        else:
            # It's shorter to go counter-clockwise
            pUnit.rotateFacingDirectionCounterClockwise()


# define piecesets
def getPieceSet(piece_set_key="ANCIENT"):
    """
    Returns the pieceset dictionary indicated by the provided key

    Args:
        piece_set_key: the key to which pieceset dictionary to use

    Returns:
        a pieceset dictionary
    """

    PIECE_SETS = {
        "ANCIENT": {
            "PAWN": CvUtil.findInfoTypeNum(
                gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_WARRIOR"
            ),
            "ROOK": CvUtil.findInfoTypeNum(
                gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_AXEMAN"
            ),
            "KNIGHT": CvUtil.findInfoTypeNum(
                gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_CHARIOT"
            ),
            "BISHOP": CvUtil.findInfoTypeNum(
                gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_ARCHER"
            ),
            "QUEEN": CvUtil.findInfoTypeNum(
                gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_SPY"
            ),
            "KING": CvUtil.findInfoTypeNum(
                gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_PROPHET"
            ),
        }
    }

    return PIECE_SETS[piece_set_key]


def setupPieces(piece_set_key="ANCIENT"):
    """Sets up the pieces on the board"""

    piece_set = getPieceSet(piece_set_key)

    # set up white pieces
    iActivePlayer = 1

    # pawns
    for iX in range(1, 9):
        gc.getPlayer(iActivePlayer).initUnit(
            piece_set["PAWN"],
            iX,
            7,
            UnitAITypes.NO_UNITAI,
            DirectionTypes.DIRECTION_SOUTH,
            ChessPieceTypes.CHESS_PIECE_PAWN,
        )

    # rooks
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["ROOK"],
        1,
        8,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_SOUTH,
        ChessPieceTypes.CHESS_PIECE_ROOK,
    )
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["ROOK"],
        8,
        8,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_SOUTH,
        ChessPieceTypes.CHESS_PIECE_ROOK,
    )

    # knights
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["KNIGHT"],
        2,
        8,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_SOUTH,
        ChessPieceTypes.CHESS_PIECE_KNIGHT,
    )
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["KNIGHT"],
        7,
        8,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_SOUTH,
        ChessPieceTypes.CHESS_PIECE_KNIGHT,
    )

    # bishops
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["BISHOP"],
        3,
        8,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_SOUTH,
        ChessPieceTypes.CHESS_PIECE_BISHOP,
    )
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["BISHOP"],
        6,
        8,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_SOUTH,
        ChessPieceTypes.CHESS_PIECE_BISHOP,
    )

    # king and queen
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["QUEEN"],
        4,
        8,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_SOUTH,
        ChessPieceTypes.CHESS_PIECE_QUEEN,
    )
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["KING"],
        5,
        8,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_SOUTH,
        ChessPieceTypes.CHESS_PIECE_KING,
    )

    # set up black pieces
    iActivePlayer = 0

    # pawns
    for iX in range(1, 9):
        gc.getPlayer(iActivePlayer).initUnit(
            piece_set["PAWN"],
            iX,
            2,
            UnitAITypes.NO_UNITAI,
            DirectionTypes.DIRECTION_NORTH,
            ChessPieceTypes.CHESS_PIECE_PAWN,
        )

    # rooks
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["ROOK"],
        1,
        1,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_NORTH,
        ChessPieceTypes.CHESS_PIECE_ROOK,
    )
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["ROOK"],
        8,
        1,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_NORTH,
        ChessPieceTypes.CHESS_PIECE_ROOK,
    )

    # knights
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["KNIGHT"],
        2,
        1,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_NORTH,
        ChessPieceTypes.CHESS_PIECE_KNIGHT,
    )
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["KNIGHT"],
        7,
        1,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_NORTH,
        ChessPieceTypes.CHESS_PIECE_KNIGHT,
    )

    # bishops
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["BISHOP"],
        3,
        1,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_NORTH,
        ChessPieceTypes.CHESS_PIECE_BISHOP,
    )
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["BISHOP"],
        6,
        1,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_NORTH,
        ChessPieceTypes.CHESS_PIECE_BISHOP,
    )

    # king and queen
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["QUEEN"],
        4,
        1,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_NORTH,
        ChessPieceTypes.CHESS_PIECE_QUEEN,
    )
    gc.getPlayer(iActivePlayer).initUnit(
        piece_set["KING"],
        5,
        1,
        UnitAITypes.NO_UNITAI,
        DirectionTypes.DIRECTION_NORTH,
        ChessPieceTypes.CHESS_PIECE_KING,
    )


class CvCiv4ChessEvents(CvEventManager.CvEventManager):

    def __init__(self):

        self.parent = CvEventManager.CvEventManager
        self.parent.__init__(self)
        self.civ_chess_obj = CivChessObj()

        self.unit_id_map = {}
        self.unit_id_map[0] = set()
        self.unit_id_map[1] = set()

    def onGameStart(self, argsList):
        "Called at the start of the game"
        self.parent.onGameStart(self, argsList)

        # set up the board
        setupPieces()

        # ensure sides are at war
        gc.getTeam(0).declareWar(1, True, WarPlanTypes.NO_WARPLAN)
        gc.getTeam(1).declareWar(0, True, WarPlanTypes.NO_WARPLAN)


        CyInterface().addImmediateMessage("Let's play chess", "")

    def onUnitMove(self, argsList):
        "Unit Moved"
        self.parent.onUnitMove(self, argsList)

        toPlot, movedUnit, fromPlot = argsList

    def onUnitKilled(self, argsList):
        "Unit Killed"
        self.parent.onUnitKilled(self, argsList)
        pUnit, iAttacker = argsList

    def onEndGameTurn(self, argsList):
        "Called at the end of the end of each turn"
        iGameTurn = argsList[0]

    def onBeginGameTurn(self, argsList):
        "Called at the beginning of the end of each turn"
        self.parent.onBeginGameTurn(self, argsList)
        iGameTurn = argsList[0]



    def onPathCompleted(self, argsList):
        moved_unit_id, path_start_x, path_start_y, path_end_x, path_end_y = argsList

        sys.stdout.write("Entering onPathCompleted")

        iActivePlayer = gc.getGame().getActivePlayer()
        pPlayer = gc.getPlayer(iActivePlayer)
        for iUnit in range(pPlayer.getNumUnits()):
            iUnitId = pPlayer.getUnit(iUnit).getID()
            if iUnitId >= 0:
                self.unit_id_map[iActivePlayer].add(iUnitId)

        for iUnitId in self.unit_id_map[iActivePlayer]:
            pPlayer.getUnit(iUnitId).finishMoves()

        # if iActivePlayer == 0:
        #     face_unit_to_direction(pPlayer.getUnit(moved_unit_id), 0)
        # else:
        #     face_unit_to_direction(pPlayer.getUnit(moved_unit_id), 4)

        status = self.civ_chess_obj.process_move(path_start_x, path_start_y, path_end_x, path_end_y)
        if status == GAME_STATUS_IGNORED:
            # duplicate or out-of-sync report from the DLL; nothing more to do
            return 0

        board = self.civ_chess_obj.board
        sys.stdout.write("Board FEN: " + str(board.board_fen()))
        sys.stdout.write("Game id is " + str(ChessGameState.getGameID()))

        if self.checkForCheckmate():
            return 0

        CyInterface().addImmediateMessage("Unit moved... Turn over.", "")
        CyAudioGame().Play3DSound("AS3D_CHESS_MOVE", path_end_x, path_end_y, 0)

        # WIP: ask the engine for a reply. The reply is only applied to the
        # python-chess board; moving the Civ unit (CyGame.setChessMove) is not wired yet.
        if ENGINE_OPPONENT_ENABLED:
            engine_move = make_engine_move(board.fen())
            if engine_move is None:
                sys.stdout.write("No engine move available (is the bridge server running?)")
            else:
                sys.stdout.write("Engine made a move: " + str(engine_move))
                board.push_uci(engine_move)
                self.checkForCheckmate()

        return 0

    def checkForCheckmate(self):
        """Declares the winner if the side to move is checkmated. Returns True on checkmate."""
        board = self.civ_chess_obj.board
        if not board.is_checkmate():
            return False

        # player 0 plays White, player 1 plays Black; the side to move is the one mated
        if board.turn == chess.WHITE:
            iWinner = 1
        else:
            iWinner = 0
        gc.getGame().setWinner(gc.getPlayer(iWinner).getTeam(), gc.getInfoTypeForString("VICTORY_CHECKMATE"))
        return True






