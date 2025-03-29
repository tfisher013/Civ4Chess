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

DefaultUnitAI = UnitAITypes.NO_UNITAI

class CvCivChessEvents(CvEventManager.CvEventManager):
	
	def __init__(self):
		
		CvEventManager.CvEventManager.__init__(self)
		
		
	def turnChecker(self, iTurn):
		pass
	
	# Determine the start-game state
	def setupGame(self):
		
		# Temporary Measure to turn off 'Feats'		
		# CyMessageControl().sendPlayerOption(PlayerOptionTypes.PLAYEROPTION_ADVISOR_POPUPS, false)
		
		self.initValues()

		# make the entire map visible to all players
		for playerId in range(gc.getMAX_PLAYERS()):
			for width in range(CyMap().getGridWidth()):
				for height in range(CyMap().getGridHeight()):
					CyMap().plot(width, height).setRevealed(playerId, true, true)
	
				
	def initValues(self):
		pass	
				
	def initCity(self, pCity):
		pass
		
###########################################################################################
####################################### MISC EVENTS #######################################
###########################################################################################
		
	def randomizeStartingArmies(self):
		pass
			
	def checkAlignment(self):
		pass	
		
	def alterMilitiaCounters(self):
		pass
					
	def alterCitySpawnUnitCounters(self):
		pass
						
	def checkForUnitSpawning(self, iPlayer, iUnitX, iUnitY, eUnitDomainType):
		pass
									
	def addBritishReinforcements(self, iTurn):
		pass
		
###########################################################################################
####################################### TURN EVENTS #######################################
###########################################################################################
		
	# New American Navy - 2 Privateers
	def Nov_1775(self):
		pass
		
	# Thomas Paine - 1 Minuteman
	def Jan_1776(self):
		pass
		
	# France & Spain support - gold, units, alignment
	def May_1776_1(self):
		pass
		
	# Provincial Governments
	def May_1776_2(self):
		pass
		
	# Independence - France & Spain Alignment
	def Jul_1776(self):
		pass
		
	# France Recognizes American Indepedence - France Alignment
	def Oct_1777(self):
		pass
		
	# Articles of Confederation - Gold and 1 unit
	def Nov_1777(self):
		pass
		
	# Von Steuben's training
	def Feb_1778(self):
		pass
		
	# Peace to Britain
	def Aug_1779(self):
		pass
		
	# French land 3 units
	def Jul_1780(self):
		pass
		
	# Benedict Arnold's Betrayal
	def Aug_1780(self):
		pass
		
	# French navy Appears
	def Aug_1781(self):
		pass
	
###########################################################################################
#################################### UTILITY FUNCTIONS ####################################
###########################################################################################
		
	def getRand(self, iNum):
		
		return CyGame().getSorenRandNum(iNum, "AmRevScenario")
		
	def getScore(self, iPlayerID):
		return 0
		
	def determineValidCities(self, iPlayerID, aiValidCities):
		
		pPlayer = PyPlayer(iPlayerID)
		
		# Loop through Player's cities and see if there are any valid ones
		
		for iValidCity in aiValidCities:
			
			apCityList = pPlayer.getCityList()
			for pCity in apCityList:
				iCityID = pCity.getID()
				
				if (self.getCityIDFromPyPointer(pCity) == iValidCity):
					
					return iCityID
					
		return -1
		
	def isEnemyUnits(self, pThisTeam, iPlotX, iPlotY):
		
		# Check to see if there are any other units already on this plot
		pPlot = CyMap().plot(iPlotX, iPlotY)
		
		if (pPlot.getNumUnits() > 0):
			
			for iUnitLoop in range(pPlot.getNumUnits()):
				
				pLoopUnit = pPlot.getUnit(iUnitLoop)
				
				pUnitOwner = gc.getPlayer(pLoopUnit.getOwner())
				
				# Check to see if this unit belongs to a player that 'our' player is at war with
				if (pThisTeam.isAtWar(pUnitOwner.getTeam())):
					return true
		
		return false
		
	def initUnit(self, pUnit):
		
#		print("Init-ing Unit")
		
		# Militia have a [self.iMilitiaDisbandCounter] turn counter
		aScriptData = [-1]
		
		pUnit.setScriptData(pickle.dumps(aScriptData))
		
###### CITY SCRIPT DATA ######
		
	def getCityID(self, iPlayer, iCity):
		pass
		
	def setCityID(self, iPlayer, iCity, iValue):
		pass
	
	def getCityIDFromPyPointer(self, pCity):
		pass
		
###### UNIT SCRIPT DATA ######
		
			
###### PLAYER SCRIPT DATA ######
		
		
	### EVENTS ###
		
	def displayEventText(self):
		
		if (gc.getPlayer(CyGame().getActivePlayer()).isAlive()):
			
			szTitle = self.szGameDate = CyGameTextMgr().getTimeStr(CyGame().getGameTurn(), false)
			
			popup = PyPopup.PyPopup(-1)
			popup.setHeaderString(szTitle)
			popup.setBodyString(self.szEventText + "\n\n" + self.szResultText)
			popup.launch(true, PopupStates.POPUPSTATE_QUEUED)
		
	def addPopup(self, szText):
		
		szTitle = self.szGameDate = CyGameTextMgr().getTimeStr(CyGame().getGameTurn(), false)
		
		popup = PyPopup.PyPopup(-1)
		popup.setHeaderString(szTitle)
		popup.setBodyString(szText)
		popup.launch(true, PopupStates.POPUPSTATE_QUEUED)
		
###########################################################################################
##################################### EVENT OVERRIDES #####################################
###########################################################################################
	
	def onLoadGame(self, argsList):
		'Called when game is loaded'
		
		self.initValues()
	
	def onGameStart(self, argsList):
		'Called at the start of the game'

		log_file_path = os.path.join(os.getcwd(), "game_start_log.txt")
        
		log_file = open(log_file_path, 'a')
		log_file.write("FLAG 1\n")
		log_file.close()  # Remember to manually close the file
			
		self.setupGame()

		log_file = open(log_file_path, 'a')
		log_file.write("FLAG 2\n")
		log_file.close()  # Remember to manually close the file
		
		for iPlayer in range(gc.getMAX_PLAYERS()):
			player = gc.getPlayer(iPlayer)
			if (player.isAlive() and player.isHuman()):
				popupInfo = CyPopupInfo()
				popupInfo.setButtonPopupType(ButtonPopupTypes.BUTTONPOPUP_PYTHON_SCREEN)
				popupInfo.setText(u"showDawnOfMan")
				popupInfo.addPopup(iPlayer)
		
	def onBeginGameTurn(self, argsList):
		'Called at the beginning of the end of each turn'
		iGameTurn = argsList[0]
		
		# American Revolution events
		self.turnChecker(iGameTurn)
		
	def onUnitMove(self, argsList):
		'unit move'
		
		pPlot,pUnit = argsList
		player = PyPlayer(pUnit.getOwner())
		unitInfo = PyInfo.UnitInfo(pUnit.getUnitType())

	def onUnitLost(self, argsList):
		pass
			
	def onCityAcquired(self, argsList):
		pass
		
	def onCityLost(self, argsList):
		pass
