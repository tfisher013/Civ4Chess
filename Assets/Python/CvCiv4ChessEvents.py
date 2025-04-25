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
import chess

# globals
gc = CyGlobalContext()
localText = CyTranslator()

def getPieceSet(pieceSetKey="ANCIENT"):
    return {
		"PAWN": CvUtil.findInfoTypeNum(gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_WARRIOR"),
		"ROOK": CvUtil.findInfoTypeNum(gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_AXEMAN"),
		"KNIGHT": CvUtil.findInfoTypeNum(gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_CHARIOT"),
		"BISHOP": CvUtil.findInfoTypeNum(gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_ARCHER"),
		"QUEEN": CvUtil.findInfoTypeNum(gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_SPY"),
		"KING": CvUtil.findInfoTypeNum(gc.getUnitInfo, gc.getNumUnitInfos(), "UNIT_PROPHET")
	}

def setupPieces(pieceSetKey="ANCIENT"):
    """ Sets up the pieces on the board
    """

    pieceSet = getPieceSet(pieceSetKey=pieceSetKey)

	# set up white pieces
    iActivePlayer = 1

	# pawns
    for iX in range(1, 9):
        gc.getPlayer(iActivePlayer).initUnit(pieceSet["PAWN"], iX, 7, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
	
	# rooks
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["ROOK"], 1, 8, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["ROOK"], 8, 8, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)

	# knights
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["KNIGHT"], 2, 8, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["KNIGHT"], 7, 8, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)

	# bishops
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["BISHOP"], 3, 8, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["BISHOP"], 6, 8, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)   

	# king and queen
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["QUEEN"], 5, 8, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["KING"], 4, 8, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_SOUTH)

	# set up black pieces
    iActivePlayer = 0

	# pawns
    for iX in range(1, 9):
        gc.getPlayer(iActivePlayer).initUnit(pieceSet["PAWN"], iX, 2, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)

    # rooks
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["ROOK"], 1, 1, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["ROOK"], 8, 1, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)
	
    # knights
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["KNIGHT"], 2, 1, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["KNIGHT"], 7, 1, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)
	
    # bishops
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["BISHOP"], 3, 1, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["BISHOP"], 6, 1, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)

	# king and queen
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["QUEEN"], 5, 1, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)
    gc.getPlayer(iActivePlayer).initUnit(pieceSet["KING"], 4, 1, UnitAITypes.NO_UNITAI, DirectionTypes.DIRECTION_NORTH)


def areUnitsEqual(unit1, unit2):
    """
    Determines whether the two provided CyUnit objects represent the same unit in play

    Args:
        unit1: a CyUnit object
        unit2: a CyUnit object

    Returns:
        True if the objects represent the same unit in play; False otherwise
    """

    if unit1.getID() != unit2.getID():
        return False
    if unit1.getMoves() != unit2.getMoves():
        return False
    if unit1.movesLeft() != unit2.movesLeft():
        return False
    if unit1.getOwner() != unit2.getOwner():
        return False
    if unit1.getX() != unit2.getX():
        return False
    if unit2.getY() != unit2.getY():
        return False
    
    return True

class CvCiv4ChessEvents(CvEventManager.CvEventManager):
	
    def __init__(self):
		
        self.parent = CvEventManager.CvEventManager
        self.parent.__init__(self)
		
    def onGameStart(self, argsList):
        'Called at the start of the game'
        self.parent.onGameStart(self, argsList)

        setupPieces()

        # give all units the ability to view the entire board			
        for iPlayer in range(gc.getGame().countCivPlayersAlive()):
            player = gc.getPlayer(iPlayer)
            for iUnit in range(player.getNumUnits()):
                player.getUnit(iUnit).setHasPromotion(0, True)

        # test import of python-chess
        board = chess.Board()
        sys.stdout.write(str(board))

        CyInterface().addImmediateMessage("Let's play chess", "")

    def onUnitMove(self, argsList):
        'Unit Moved'
        self.parent.onUnitMove(self, argsList)

        fromPlot, movedUnit, toPlot = argsList

		# end turn after moving a unit
        iActivePlayer = gc.getGame().getActivePlayer()
        for iUnit in range(gc.getPlayer(iActivePlayer).getNumUnits()):
            currentUnit = gc.getPlayer(iActivePlayer).getUnit(iUnit)
            if not areUnitsEqual(currentUnit, movedUnit):
                currentUnit.finishMoves()
                
        CyInterface().addImmediateMessage("Unit moved... Turn over.", "")

    def onUnitKilled(self, argsList):
        'Unit Killed'
        self.parent.onUnitKilled(self, argsList)
        pUnit, iAttacker = argsList
			
    def onEndGameTurn(self, argsList):
        'Called at the end of the end of each turn'
        iGameTurn = argsList[0]
			
    def onBeginGameTurn(self, argsList):
        'Called at the beginning of the end of each turn'
        self.parent.onBeginGameTurn(self, argsList)
        iGameTurn = argsList[0]
		