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

		# disable gaining experience
		defender, attacker = argsList
		defender.setExperience(0, 0)
		attacker.setExperience(0, 0)
		
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
		iPlayerID = argsList[0]
		bNewValue = argsList[1]

	def onVictory(self, argsList):
		'Victory'
		self.parent.onVictory(self, argsList)

