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
# (BridgeServer/bridge_server.py must be running on port 8000). The human is Civ player 0
# and Stockfish is player 1; which of them plays White is chosen in a popup at game start.
ENGINE_OPPONENT_ENABLED = True
HUMAN_PLAYER = 0
ENGINE_PLAYER = 1
# popup context id of the colour choice (the stock events use 4999..5012)
EVENT_CHOOSE_COLOUR = 7001
COLOUR_BUTTON_WHITE = 0
COLOUR_BUTTON_BLACK = 1
COLOUR_BUTTON_RANDOM = 2
ENGINE_THINK_SECONDS = 1.0
# game updates to wait for the human's move to finish before the engine replies anyway
ENGINE_REPLY_MAX_WAIT = 300


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


# pieces on the back rank, files a..h
BACK_RANK = ["ROOK", "KNIGHT", "BISHOP", "QUEEN", "KING", "BISHOP", "KNIGHT", "ROOK"]


def getChessPieceType(piece_name):
    """Returns the ChessPieceTypes value for a piece name such as "ROOK"."""
    return {
        "PAWN": ChessPieceTypes.CHESS_PIECE_PAWN,
        "ROOK": ChessPieceTypes.CHESS_PIECE_ROOK,
        "KNIGHT": ChessPieceTypes.CHESS_PIECE_KNIGHT,
        "BISHOP": ChessPieceTypes.CHESS_PIECE_BISHOP,
        "QUEEN": ChessPieceTypes.CHESS_PIECE_QUEEN,
        "KING": ChessPieceTypes.CHESS_PIECE_KING,
    }[piece_name]


def setupPieces(white_player, piece_set_key="ANCIENT"):
    """
    Sets up the pieces on the board. White (ranks 1-2, facing north) belongs to Civ player
    white_player, Black (ranks 7-8, facing south) to the other player.
    """

    piece_set = getPieceSet(piece_set_key)
    black_player = 1 - white_player

    sides = (
        (white_player, 2, 1, DirectionTypes.DIRECTION_NORTH),
        (black_player, 7, 8, DirectionTypes.DIRECTION_SOUTH),
    )
    for iPlayer, iPawnRank, iBackRank, eFacing in sides:
        pPlayer = gc.getPlayer(iPlayer)
        for iX in range(1, 9):
            pPlayer.initUnit(
                piece_set["PAWN"],
                iX,
                iPawnRank,
                UnitAITypes.NO_UNITAI,
                eFacing,
                ChessPieceTypes.CHESS_PIECE_PAWN,
            )
            piece_name = BACK_RANK[iX - 1]
            pPlayer.initUnit(
                piece_set[piece_name],
                iX,
                iBackRank,
                UnitAITypes.NO_UNITAI,
                eFacing,
                getChessPieceType(piece_name),
            )


class CvCiv4ChessEvents(CvEventManager.CvEventManager):

    def __init__(self):

        self.parent = CvEventManager.CvEventManager
        self.parent.__init__(self)
        self.resetGameState()

        # the camera's base turn before it was ever turned for Black (kept across games)
        self.default_camera_turn = None

        self.Events[EVENT_CHOOSE_COLOUR] = ('ChooseColour', self.applyChooseColour, self.beginChooseColour)
        # no "DEBUG Event" message on screen for this popup
        if EVENT_CHOOSE_COLOUR not in CvUtil.SilentEvents:
            CvUtil.SilentEvents.append(EVENT_CHOOSE_COLOUR)

    def resetGameState(self):
        """
        Clears everything that belongs to one game. Civ4 creates this event manager once per
        session, not once per game, so a new game started from the main menu must reset it.
        """
        self.civ_chess_obj = CivChessObj()

        # square (x, y) of a human move that the engine still has to answer, see onGameUpdate
        self.engine_reply_square = None
        self.engine_reply_wait = 0
        # True when the engine plays White and still has to make the first move
        self.engine_first_move_pending = False

        # Civ player who plays White; None until the colour has been chosen
        self.white_player = None

    def onGameStart(self, argsList):
        "Called at the start of the game"
        # before the parent call, which opens the Dawn of Man screen
        self.resetGameState()
        self.parent.onGameStart(self, argsList)

        # ensure sides are at war
        gc.getTeam(0).declareWar(1, True, WarPlanTypes.NO_WARPLAN)
        gc.getTeam(1).declareWar(0, True, WarPlanTypes.NO_WARPLAN)

        # The pieces are placed once the human has chosen a colour: the popup opens when the
        # Dawn of Man screen closes (CvScreensInterface.Civ4ChessDawnOfMan).

    def showColourChoice(self):
        """Asks the human which colour to play, unless the pieces are already on the board."""
        if self.white_player is None:
            self.beginEvent(EVENT_CHOOSE_COLOUR)

    def beginChooseColour(self, argsList):
        popup = PyPopup.PyPopup(EVENT_CHOOSE_COLOUR, EventContextTypes.EVENTCONTEXT_ALL)
        popup.setHeaderString("Choose your colour")
        popup.setBodyString("Stockfish plays the other side. White moves first.")
        # the button order must match the COLOUR_BUTTON_* values
        popup.addButton("White")
        popup.addButton("Black")
        popup.addButton("Random")
        popup.launch(False)

    def applyChooseColour(self, playerID, userData, popupReturn):
        iButton = popupReturn.getButtonClicked()
        if iButton == COLOUR_BUTTON_RANDOM:
            if gc.getGame().getSorenRandNum(2, "Civ4Chess colour") == 0:
                iButton = COLOUR_BUTTON_WHITE
            else:
                iButton = COLOUR_BUTTON_BLACK

        if iButton == COLOUR_BUTTON_BLACK:
            self.startChessGame(ENGINE_PLAYER)
        else:
            # White, or the popup was closed without a choice
            self.startChessGame(HUMAN_PLAYER)

    def startChessGame(self, white_player):
        """Places the pieces with Civ player white_player as White and starts the game."""
        if self.white_player is not None:
            return
        self.white_player = white_player

        setupPieces(white_player)

        # tell the DLL which moves White may play first
        self.sendLegalMoves()
        self.lookAtBoard()

        if self.isHumanWhite():
            CyInterface().addImmediateMessage("Let's play chess - you play White", "")
        else:
            CyInterface().addImmediateMessage("Let's play chess - you play Black", "")
            if ENGINE_OPPONENT_ENABLED:
                # played from onGameUpdate, so the board is drawn before the engine thinks
                self.engine_first_move_pending = True

    def isHumanWhite(self):
        return self.white_player == HUMAN_PLAYER

    def playerOfColour(self, colour):
        """The Civ player who plays the python-chess colour (chess.WHITE or chess.BLACK)."""
        if colour == chess.WHITE:
            return self.white_player
        return 1 - self.white_player

    def lookAtBoard(self):
        """Points the camera at the board from the human's side."""
        # The turn is set absolutely, so it is right whether or not the camera kept the turn
        # of an earlier game in this session.
        if self.default_camera_turn is None:
            self.default_camera_turn = CyCamera().GetBaseTurn()

        if self.isHumanWhite():
            CyCamera().SetBaseTurn(self.default_camera_turn)
            CyCamera().JustLookAtPlot(CyMap().plot(4, 4))
        else:
            # seen from Black's side: turned half way round, centred on the mirrored square
            CyCamera().SetBaseTurn(self.default_camera_turn + 180.0)
            CyCamera().JustLookAtPlot(CyMap().plot(5, 5))

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

    def sendLegalMoves(self):
        """Gives the DLL the legal moves for the side to move; it refuses every other move."""
        gc.getGame().setLegalMoves(self.civ_chess_obj.legal_moves_string())

    def onPathCompleted(self, argsList):
        """
        Called by the DLL when a piece has made a move (and when a capture starts). python-chess
        decides whether the move is legal; the DLL only lets legal moves through, so a move
        that is rejected here is a duplicate report of one that was already applied.
        """
        moved_unit_id, path_start_x, path_start_y, path_end_x, path_end_y = argsList

        chess_obj = self.civ_chess_obj
        mover = self.playerOfColour(chess_obj.board.turn)

        status = chess_obj.process_move(path_start_x, path_start_y, path_end_x, path_end_y)
        if status == GAME_STATUS_IGNORED:
            # duplicate report from the DLL; the move was already applied
            return 0

        # one move per turn: use up the movement of every piece of the side that just moved
        for pUnit in PyPlayer(mover).getUnitList():
            pUnit.finishMoves()

        # castling: the rook goes along with the king
        self.slideCastlingRook()

        # en passant: the captured pawn is not on the destination square
        if chess_obj.last_en_passant_victim is not None:
            victim_x, victim_y = chess_obj.last_en_passant_victim
            self.removePiecesAt(victim_x, victim_y)

        # from now on only the moves that are legal in the new position are allowed
        self.sendLegalMoves()
        self.logBoardState("after " + str(chess_obj.last_move))

        if self.handleGameEnd(status):
            return 0

        CyAudioGame().Play3DSound("AS3D_CHESS_MOVE", path_end_x, path_end_y, 0)

        if ENGINE_OPPONENT_ENABLED and mover == HUMAN_PLAYER:
            # A capture is reported when the attack starts, before the captured piece is gone
            # and the attacker has moved in. The reply is played from onGameUpdate once the
            # human's piece stands on its destination.
            self.engine_reply_square = (path_end_x, path_end_y)
            self.engine_reply_wait = 0
        else:
            CyInterface().addImmediateMessage("Unit moved... Turn over.", "")

        return 0

    def onGameUpdate(self, argsList):
        """Called by the game many times per second; plays a queued engine reply when ready."""
        self.parent.onGameUpdate(self, argsList)

        if self.engine_first_move_pending:
            self.engine_first_move_pending = False
            self.playEngineReply()
            return

        if self.engine_reply_square is None:
            return

        x, y = self.engine_reply_square
        self.engine_reply_wait += 1
        if not self.isOnlyHumanPieceAt(x, y) and self.engine_reply_wait < ENGINE_REPLY_MAX_WAIT:
            return

        if self.engine_reply_wait >= ENGINE_REPLY_MAX_WAIT:
            sys.stdout.write("Engine reply: gave up waiting for the move to finish at "
                             + str(self.engine_reply_square) + "\n")
        self.engine_reply_square = None
        self.playEngineReply()

    def isOnlyHumanPieceAt(self, x, y):
        """True when plot (x, y) holds the human's piece and no piece of the engine's side,
        i.e. the human's move (or capture) has finished on the map."""
        pPlot = gc.getMap().plot(x, y)
        bHuman = False
        for i in range(pPlot.getNumUnits()):
            pUnit = pPlot.getUnit(i)
            if pUnit.getOwner() == ENGINE_PLAYER:
                return False
            if pUnit.getOwner() == HUMAN_PLAYER:
                bHuman = True
        return bHuman

    def playEngineReply(self):
        """
        Asks Stockfish (through the bridge server) for a reply and plays it on the map with the
        same steps as a human move: capture, slide, castling rook, promotion. Afterwards the
        human's pieces get their movement back, so the next move can be made without ending
        the Civ turn.
        """
        chess_obj = self.civ_chess_obj

        uci = make_engine_move(chess_obj.board.fen(), ENGINE_THINK_SECONDS)
        if uci is None:
            CyInterface().addImmediateMessage("Stockfish is not available - is the bridge server running?", "")
            return

        san = uci
        try:
            san = chess_obj.board.san(chess.Move.from_uci(uci))
        except Exception:
            pass

        status = chess_obj.push_uci_move(uci)
        if status == GAME_STATUS_IGNORED:
            sys.stdout.write("Engine move " + uci + " is not legal here; ignored\n")
            CyInterface().addImmediateMessage("Stockfish sent an illegal move (" + uci + ")", "")
            return

        (from_x, from_y), (to_x, to_y) = chess_obj.last_move_coords

        # a capture removes the captured piece first (for en passant it is not on the destination)
        if chess_obj.last_capture_coords is not None:
            capture_x, capture_y = chess_obj.last_capture_coords
            self.removePiecesAt(capture_x, capture_y)

        # the DLL promotes a pawn that reaches the last rank to a queen when the slide finishes
        gc.getGame().slideChessPiece(from_x, from_y, to_x, to_y)
        self.slideCastlingRook()

        self.sendLegalMoves()
        self.logBoardState("after engine " + uci)
        CyAudioGame().Play3DSound("AS3D_CHESS_MOVE", to_x, to_y, 0)
        CyInterface().addImmediateMessage("Stockfish plays " + san, "")

        if self.handleGameEnd(status):
            return

        # the human moves next: give their pieces their movement back
        for pUnit in PyPlayer(HUMAN_PLAYER).getUnitList():
            pUnit.setMoves(0)

    def slideCastlingRook(self):
        """After a castling move, slides the rook to its new square."""
        chess_obj = self.civ_chess_obj
        if chess_obj.last_rook_move is not None:
            rook_from, rook_to = chess_obj.last_rook_move
            gc.getGame().slideChessPiece(rook_from[0], rook_from[1], rook_to[0], rook_to[1])

    def removePiecesAt(self, x, y):
        """Removes every unit standing on plot (x, y): a captured piece, and a promoted pawn
        that is still waiting to be deleted."""
        pPlot = gc.getMap().plot(x, y)
        for i in range(pPlot.getNumUnits()):
            if pPlot.getNumUnits() == 0:
                break
            pPlot.getUnit(0).kill(False, PlayerTypes.NO_PLAYER)

    def handleGameEnd(self, status):
        """Shows the result of a finished game. Returns True if the game is over."""
        board = self.civ_chess_obj.board

        if status == GAME_STATUS_CHECKMATE:
            # the side to move is the one mated
            iWinner = self.playerOfColour(not board.turn)
            gc.getGame().setWinner(gc.getPlayer(iWinner).getTeam(), gc.getInfoTypeForString("VICTORY_CHECKMATE"))
            return True

        if status == GAME_STATUS_STALEMATE:
            CyInterface().addImmediateMessage("Stalemate - the game is a draw.", "")
            return True

        if status == GAME_STATUS_DRAW:
            CyInterface().addImmediateMessage("The game is a draw.", "")
            return True

        return False

    def logBoardState(self, tag):
        """
        Debug aid: logs the python-chess position and compares it with the pieces that are
        really on the map, so a desync between the two shows up in PythonDbg.log.
        """
        board = self.civ_chess_obj.board
        # python-chess piece types (pawn..king = 1..6) for each ChessPieceTypes value
        civ_to_chess = {
            ChessPieceTypes.CHESS_PIECE_PAWN: chess.PAWN,
            ChessPieceTypes.CHESS_PIECE_ROOK: chess.ROOK,
            ChessPieceTypes.CHESS_PIECE_KNIGHT: chess.KNIGHT,
            ChessPieceTypes.CHESS_PIECE_BISHOP: chess.BISHOP,
            ChessPieceTypes.CHESS_PIECE_QUEEN: chess.QUEEN,
            ChessPieceTypes.CHESS_PIECE_KING: chess.KING,
        }

        problems = []
        for x in range(1, 9):
            for y in range(1, 9):
                square = chess.square(x - 1, y - 1)
                expected = board.piece_at(square)

                found = None
                pPlot = gc.getMap().plot(x, y)
                for i in range(pPlot.getNumUnits()):
                    pUnit = pPlot.getUnit(i)
                    if civ_to_chess.has_key(pUnit.getChessPieceType()):
                        found = (civ_to_chess[pUnit.getChessPieceType()], pUnit.getOwner() == self.white_player)

                if expected is None:
                    if found is not None:
                        problems.append(chess.SQUARE_NAMES[square] + ": board empty, map has a piece")
                elif found is None:
                    problems.append(chess.SQUARE_NAMES[square] + ": board has " + expected.symbol() + ", map is empty")
                elif found != (expected.piece_type, expected.color):
                    problems.append(chess.SQUARE_NAMES[square] + ": board has " + expected.symbol() + ", map has a different piece")

        sys.stdout.write("CHESS-SYNC [" + tag + "] fen=" + board.fen() + "\n")
        if len(problems) == 0:
            sys.stdout.write("CHESS-SYNC OK\n")
        else:
            sys.stdout.write("CHESS-SYNC MISMATCH: " + "; ".join(problems) + "\n")
