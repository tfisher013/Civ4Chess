# American Revolution
# Civilization 4 (c) 2005 Firaxis Games

# Created by -	Jon 'Trip' Shafer
# Have fun!

from CvPythonExtensions import *
import sys
import Popup as PyPopup
from PyHelpers import PyPlayer
import pickle
import CvEventManager
from CvScreenEnums import *
from PyHelpers import *
import CvUtil
import os

# globals
gc = CyGlobalContext()
localText = CyTranslator()

BOARD_LENGTH = 8

PIECE_SETS = {
	"ANCIENT": {
		"PAWN": gc.getInfoTypeForString("UNIT_WARRIOR"),
		"ROOK": gc.getInfoTypeForString("UNIT_AXEMAN"),
		"KNIGHT": gc.getInfoTypeForString("UNIT_CHARIOT"),
		"BISHOP": gc.getInfoTypeForString("UNIT_ARCHER"),
		"QUEEN": gc.getInfoTypeForString("UNIT_SPY"),
		"KING": gc.getInfoTypeForString("UNIT_PROPHET")
	}
}

def setupPieces(pieceSet="ANCIENT"):
	""" Sets up the pieces on the board
	"""

	# set up white pieces
	iActivePlayer = 1

	# pawns
	for iX in range(1, 9):
		gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["PAWN"], iX, 7, UnitAITypes.UNITAI_ATTACK)
	
	# rooks
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["ROOK"], 1, 8, UnitAITypes.UNITAI_ATTACK)
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["ROOK"], 8, 8, UnitAITypes.UNITAI_ATTACK)

	# knights
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["KNIGHT"], 2, 8, UnitAITypes.UNITAI_ATTACK)
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["KNIGHT"], 7, 8, UnitAITypes.UNITAI_ATTACK)

	# bishops
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["BISHOP"], 3, 8, UnitAITypes.UNITAI_ATTACK)
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["BISHOP"], 6, 8, UnitAITypes.UNITAI_ATTACK)

	# king and queen
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["QUEEN"], 5, 8, UnitAITypes.UNITAI_ATTACK)
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["KING"], 4, 8, UnitAITypes.UNITAI_ATTACK)

	# set up black pieces
	iActivePlayer = 0

	# pawns
	for iX in range(1, 9):
		gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["PAWN"], iX, 2, UnitAITypes.UNITAI_ATTACK)
	
	# rooks
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["ROOK"], 1, 1, UnitAITypes.UNITAI_ATTACK)
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["ROOK"], 8, 1, UnitAITypes.UNITAI_ATTACK)

	# knights
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["KNIGHT"], 2, 1, UnitAITypes.UNITAI_ATTACK)
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["KNIGHT"], 7, 1, UnitAITypes.UNITAI_ATTACK)
	# bishops
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["BISHOP"], 3, 1, UnitAITypes.UNITAI_ATTACK)
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["BISHOP"], 6, 1, UnitAITypes.UNITAI_ATTACK)

	# king and queen
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["QUEEN"], 5, 1, UnitAITypes.UNITAI_ATTACK)
	gc.getPlayer(iActivePlayer).initUnit(PIECE_SETS[pieceSet]["KING"], 4, 1, UnitAITypes.UNITAI_ATTACK)


def areUnitsEqual(unitA, unitB):
	""" Returns True if the two provided units represent the same unit in gameplay

        Args:
            unitA: A CyUnit object
            unitB: A CyUnit object

        Returns:
            True if the two units are the same units in gameplay, False otherwise
	"""

	if unitA.getID() != unitB.getID():
		return False
	if unitA.getOwner() != unitB.getOwner():
		return False
	if unitA.getX() != unitB.getX():
		return False
	if unitA.getY() != unitB.getY():
		return False
	if unitA.getUnitType() != unitB.getUnitType():
		return False
	if unitA.hasMoved() != unitB.hasMoved():
		return False


	return True

class CvCiv4ChessEventManager(CvEventManager.CvEventManager):
	def __init__(self):
		# initialize base class
		self.parent = CvEventManager.CvEventManager
		self.parent.__init__(self)
		
	def onGameStart(self, argsList):
		'Called at the start of the game'
		# display welcome message
		self.parent.onGameStart(self, argsList)

		setupPieces()

		CyInterface().addImmediateMessage("Let's play chess", "")

		# give all units the ability to view the entire board			
		for iPlayer in range(gc.getGame().getReplayInfo().getNumPlayers()):
			player = gc.getPlayer(iPlayer)
			for iUnit in range(player.getNumUnits()):
				player.getUnit(iUnit).setHasPromotion(0, True)
		
	def onBeginGameTurn(self, argsList):
		'Called at the beginning of a players turn'
		self.parent.onBeginGameTurn(self, argsList)
		iGameTurn = argsList[0]

	def onBeginPlayerTurn(self, argsList):
		'Called at the beginning of a players turn'
		self.parent.onBeginPlayerTurn(self, argsList)
		iGameTurn, iPlayer = argsList
	
	def onCombatResult(self, argsList):
		'Combat Result'
		self.parent.onCombatResult(self, argsList)

		CyInterface().addImmediateMessage("Combat occurred", "")
		sys.stdout.write("fight\n")

		# disable gaining experience
		attacker, defender = argsList
		defender.setExperience(0, 0)
		attacker.setExperience(0, 0)

		defender.setLevel(0)
		attacker.setLevel(0)

		defender.setPromotionReady(False)
		attacker.setPromotionReady(False)

		# end attacker's movement after combat
		attacker.finishMoves()
		attacker.rotateFacingDirectionClockwise()
		
	def onUnitCreated(self, argsList):
		'Unit Completed'
		self.parent.onUnitCreated(self, argsList)

	def onUnitBuilt(self, argsList):
		'Unit Completed'
		self.parent.onUnitBuilt(self, argsList)
	
	def onUnitKilled(self, argsList):
		'Unit Killed'
		self.parent.onUnitKilled(self, argsList)
	
	def onUnitLost(self, argsList):
		'Unit Lost'
		self.parent.onUnitLost(self, argsList)

	def onUnitMove(self, argsList):
		'Unit Moved'
		self.parent.onUnitMove(self, argsList)

		plot, movedUnit = argsList

		# end turn after moving a unit
		iActivePlayer = gc.getGame().getActivePlayer()
		if movedUnit.getMoves() < 100:
			for iUnit in range(gc.getPlayer(iActivePlayer).getNumUnits()):
				currentUnit = gc.getPlayer(iActivePlayer).getUnit(iUnit)

				if not areUnitsEqual(movedUnit, currentUnit):
					currentUnit.finishMoves()
				
		CyInterface().addImmediateMessage("Unit moved... Turn over.", "")

	def onEndGameTurn(self, argsList):
		'Turn Ended'

		# rotate camera?
				
	def onSetPlayerAlive(self, argsList):
		'Set Player Alive Event'
		self.parent.onSetPlayerAlive(self, argsList)

	def onVictory(self, argsList):
		'Victory'
		self.parent.onVictory(self, argsList)

