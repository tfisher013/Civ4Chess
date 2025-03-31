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

class CvCiv4ChessEventManager(CvEventManager.CvEventManager):
	def __init__(self):
		# initialize base class
		sys.stdout.write("We are initializing\n")

		self.parent = CvEventManager.CvEventManager
		self.parent.__init__(self)

		sys.stdout.write("Registering onGameStart\n")
		#self.EventHandlerMap['GameStart'] = self.onGameStart
		
	def onGameStart(self, argsList):
		'Called at the start of the game'
		# display welcome message
		self.parent.onGameStart(self, argsList)

		CyInterface().addImmediateMessage("Let's play chess", "")

		CyInterface().addImmediateMessage("The map has " + str(CyMap().numPlots()) + " number of plots", "")

		for width in range(gc.getMap().getGridWidth()):
			for height in range(gc.getMap().getGridHeight()):
				CyInterface().addImmediateMessage("Setting plot ("+str(width)+","+str(height)+")", "")
				#plot = CyMap().plot(width, height)
				plot = gc.getMap().plot(width, height)
				CyInterface().addImmediateMessage("We did get the plot, right?", "")
				CyInterface().addImmediateMessage("val: "+str(plot)+", type: "+str(type(plot)), "")
				
				if plot is not None:
					plot.setRevealed(0, True, False, 0)
					plot.setRevealed(1, True, False, 1)
					plot.updateVisibility()
					sys.stdout.write("Revealing plot ("+str(width)+", "+str(height)+")\n")
				# if plot.isUnit() and plot.getUnit(0).getOwner() == 0:
				# 	plot.getUnit(0).rotateFacingDirectionClockwise()
				# 	plot.getUnit(0).rotateFacingDirectionClockwise()

		for iPlayer in range(2):
			player = gc.getPlayer(iPlayer)
			for iUnit in range(player.getNumUnits()):
				player.getUnit(iUnit).setHasPromotion(0, True)

		CyInterface().addImmediateMessage("Done", "")

		
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

	def onGoodyReceived(self, argsList):
		'Goody received'
		self.parent.onGoodyReceived(self, argsList)
		
	def onGreatPersonBorn(self, argsList):
		'Unit Promoted'
		self.parent.onGreatPersonBorn(self, argsList)
		
	def onReligionSpread(self, argsList):
		'Religion Has Spread to a City'
		self.parent.onReligionSpread(self, argsList)
		
	def onGoldenAge(self, argsList):
		self.parent.onGoldenAge(self, argsList)
				
	def onSetPlayerAlive(self, argsList):
		'Set Player Alive Event'
		self.parent.onSetPlayerAlive(self, argsList)
		iPlayerID = argsList[0]
		bNewValue = argsList[1]
		
	def onCityBuilt(self, argsList):
		'City Built'
		self.parent.onCityBuilt(self, argsList)

	def onCityAcquired(self, argsList):
		'City Acquired'
		self.parent.onCityAcquired(self, argsList)

	def onVictory(self, argsList):
		'Victory'
		self.parent.onVictory(self, argsList)

