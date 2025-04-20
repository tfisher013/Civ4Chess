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

        CyInterface().addImmediateMessage("Let's play chess", "")

					
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
		