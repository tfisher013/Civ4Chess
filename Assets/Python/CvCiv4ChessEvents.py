from CvPythonExtensions import *
import sys
import Popup as PyPopup
from PyHelpers import PyPlayer
import pickle
import CvEventManager
from CvScreenEnums import *
from PyHelpers import *
import CvUtil
import CvGameUtils
from ChessUtils import *
from CivUtils import *

# globals
gc = CyGlobalContext()
localText = CyTranslator()


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

        # used for storing the first plot of multihop moves
        self.path_start_plot = None

    def onGameStart(self, argsList):
        "Called at the start of the game"
        self.parent.onGameStart(self, argsList)

        # set up the board
        setupPieces()

        # ensure sides are at war
        gc.getTeam(0).declareWar(1, True, WarPlanTypes.NO_WARPLAN)

        CyInterface().addImmediateMessage("Let's play chess", "")

    def onUnitMove(self, argsList):
        "Unit Moved"
        self.parent.onUnitMove(self, argsList)

        toPlot, movedUnit, fromPlot = argsList

        if self.path_start_plot is None:
            self.path_start_plot = fromPlot

        # if the unit has moved to the final plot of its path, do the following
        # a) finish the moves all of the other units of the same team
        # b) push the move to the game board
        if are_plots_equal(toPlot, movedUnit.getPathEndTurnPlot()):

            # end all units' movement after one has finished its move
            iActivePlayer = gc.getGame().getActivePlayer()
            for iUnit in range(gc.getPlayer(iActivePlayer).getNumUnits()):
                currentUnit = gc.getPlayer(iActivePlayer).getUnit(iUnit)
                currentUnit.finishMoves()

            # get game status after move
            game_status = self.civ_chess_obj.process_move(self.path_start_plot, toPlot)

            self.path_start_plot = None

            CyInterface().addImmediateMessage("Unit moved... Turn over.", "")

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
