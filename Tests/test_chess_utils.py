"""
Out-of-game tests for ChessUtils.CivChessObj.

Civ4 embeds Python 2.4, so these use only the stdlib unittest and run on any
Python 2.x. Run from the repository root:

    C:\\Python26\\python Tests\\test_chess_utils.py
"""
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "Assets", "Python"))

import chess
import ChessUtils
from ChessUtils import (
    CivChessObj,
    GAME_STATUS_CHECKMATE,
    GAME_STATUS_STALEMATE,
    GAME_STATUS_IN_PROGRESS,
    GAME_STATUS_IGNORED,
    GAME_STATUS_DRAW,
)


class QuietTestCase(unittest.TestCase):
    """ChessUtils logs to stdout; keep test output readable."""

    def setUp(self):
        self._stdout = sys.stdout

        class Sink:
            def write(self, text):
                pass

            def flush(self):
                pass

        sys.stdout = Sink()

    def tearDown(self):
        sys.stdout = self._stdout


def uci_to_coords(uci):
    """'e2e4' -> (5, 2, 5, 4), the way the DLL reports moves."""
    return (
        ord(uci[0]) - ord("a") + 1,
        int(uci[1]),
        ord(uci[2]) - ord("a") + 1,
        int(uci[3]),
    )


def play(obj, uci):
    return obj.process_move(*uci_to_coords(uci))


def with_fen(fen):
    obj = CivChessObj()
    obj.board.set_fen(fen)
    return obj


class LegalMoveTableTests(QuietTestCase):
    def test_start_position_has_twenty_moves(self):
        moves = CivChessObj().legal_moves_string().split(" ")
        self.assertEqual(len(moves), 20)
        self.assertTrue("e2e4" in moves)
        self.assertTrue("g1f3" in moves)

    def test_pinned_piece_cannot_move(self):
        # black rook pins the white knight on e2 to the king on e1
        obj = with_fen("4r2k/8/8/8/8/8/4N3/4K3 w - - 0 1")
        moves = obj.legal_moves_string().split(" ")
        for uci in moves:
            self.assertFalse(uci.startswith("e2"), uci)
        self.assertEqual(play(obj, "e2c3"), GAME_STATUS_IGNORED)

    def test_must_answer_check(self):
        # white king in check from the rook; only king moves / blocks / captures allowed
        obj = with_fen("4r2k/8/8/8/8/8/P7/4K3 w - - 0 1")
        moves = obj.legal_moves_string().split(" ")
        self.assertFalse("a2a3" in moves)
        self.assertTrue("e1d1" in moves)

    def test_empty_table_when_game_over(self):
        obj = CivChessObj()
        for uci in ("f2f3", "e7e5", "g2g4", "d8h4"):
            play(obj, uci)
        self.assertTrue(obj.game_over)
        self.assertEqual(obj.legal_moves_string(), "")


class SpecialMoveTests(QuietTestCase):
    def test_kingside_castling_reports_rook_move(self):
        obj = with_fen("4k3/8/8/8/8/8/8/4K2R w K - 0 1")
        self.assertEqual(play(obj, "e1g1"), GAME_STATUS_IN_PROGRESS)
        self.assertTrue(obj.last_was_castling)
        self.assertEqual(obj.last_rook_move, ((8, 1), (6, 1)))

    def test_queenside_castling_reports_rook_move(self):
        obj = with_fen("r3k3/8/8/8/8/8/8/4K3 b q - 0 1")
        self.assertEqual(play(obj, "e8c8"), GAME_STATUS_IN_PROGRESS)
        self.assertEqual(obj.last_rook_move, ((1, 8), (4, 8)))

    def test_cannot_castle_through_check(self):
        # the rook on f8 attacks f1, which the king would cross
        obj = with_fen("5r1k/8/8/8/8/8/8/4K2R w K - 0 1")
        self.assertEqual(play(obj, "e1g1"), GAME_STATUS_IGNORED)

    def test_en_passant_reports_victim(self):
        obj = with_fen("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1")
        self.assertEqual(play(obj, "e5d6"), GAME_STATUS_IN_PROGRESS)
        self.assertTrue(obj.last_was_en_passant)
        self.assertEqual(obj.last_en_passant_victim, (4, 5))
        self.assertEqual(obj.board.piece_at(chess.D5), None)

    def test_en_passant_victim_for_black(self):
        obj = with_fen("4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1")
        self.assertEqual(play(obj, "d4e3"), GAME_STATUS_IN_PROGRESS)
        self.assertEqual(obj.last_en_passant_victim, (5, 4))

    def test_promotion_is_a_queen(self):
        obj = with_fen("8/4P3/8/8/8/8/k7/4K3 w - - 0 1")
        play(obj, "e7e8")
        self.assertEqual(obj.board.piece_at(chess.E8).piece_type, chess.QUEEN)

    def test_duplicate_report_is_ignored(self):
        obj = CivChessObj()
        self.assertEqual(play(obj, "e2e4"), GAME_STATUS_IN_PROGRESS)
        fen = obj.board.fen()
        self.assertEqual(play(obj, "e2e4"), GAME_STATUS_IGNORED)
        self.assertEqual(obj.board.fen(), fen)


class GameEndTests(QuietTestCase):
    def test_checkmate(self):
        obj = CivChessObj()
        for uci in ("f2f3", "e7e5", "g2g4"):
            self.assertEqual(play(obj, uci), GAME_STATUS_IN_PROGRESS)
        self.assertEqual(play(obj, "d8h4"), GAME_STATUS_CHECKMATE)

    def test_stalemate(self):
        obj = with_fen("7k/5Q2/8/8/8/8/8/K7 w - - 0 1")
        self.assertEqual(play(obj, "f7g6"), GAME_STATUS_STALEMATE)
        self.assertTrue(obj.game_over)

    def test_insufficient_material_draw(self):
        obj = with_fen("7k/8/8/8/8/8/4q3/4K3 w - - 0 1")
        self.assertEqual(play(obj, "e1e2"), GAME_STATUS_DRAW)

    def test_threefold_repetition_draw(self):
        obj = with_fen("4k1n1/8/8/8/8/8/8/1N2K3 w - - 0 1")
        shuffle = ["b1c3", "g8f6", "c3b1", "f6g8"]
        status = GAME_STATUS_IN_PROGRESS
        for _ in range(3):
            for uci in shuffle:
                status = play(obj, uci)
                if status != GAME_STATUS_IN_PROGRESS:
                    break
            if status != GAME_STATUS_IN_PROGRESS:
                break
        self.assertEqual(status, GAME_STATUS_DRAW)

    def test_no_moves_after_game_over(self):
        obj = with_fen("7k/5Q2/8/8/8/8/8/K7 w - - 0 1")
        play(obj, "f7g6")
        self.assertEqual(play(obj, "h8g8"), GAME_STATUS_IGNORED)


class RandomGameTests(QuietTestCase):
    def test_random_games_stay_consistent(self):
        """
        Plays random legal games through process_move using map coordinates and
        checks that every move in the legal table is accepted and that the board
        always matches an independently maintained python-chess board.
        """
        rng = random.Random(12345)
        for game in range(25):
            obj = CivChessObj()
            reference = chess.Board()
            for ply in range(300):
                table = obj.legal_moves_string()
                if table == "":
                    break
                expected = []
                for move in reference.legal_moves:
                    if move.promotion is not None and move.promotion != chess.QUEEN:
                        continue
                    expected.append(move.uci())
                self.assertEqual(sorted(table.split(" ")), sorted(expected))

                uci = rng.choice(expected)
                status = play(obj, uci)
                self.assertNotEqual(status, GAME_STATUS_IGNORED, uci)
                reference.push(chess.Move.from_uci(uci))
                self.assertEqual(obj.board.fen(), reference.fen())


class EngineMoveTests(QuietTestCase):
    """push_uci_move applies Stockfish's replies; the event handler mirrors them on the map
    from last_move_coords / last_capture_coords / last_rook_move."""

    def test_quiet_move_reports_squares_and_no_capture(self):
        obj = CivChessObj()
        play(obj, "e2e4")
        self.assertEqual(obj.push_uci_move("e7e5"), GAME_STATUS_IN_PROGRESS)
        self.assertEqual(obj.last_move_coords, ((5, 7), (5, 5)))
        self.assertEqual(obj.last_capture_coords, None)

    def test_capture_reports_captured_square(self):
        obj = with_fen("4k3/8/8/3p4/4P3/8/8/4K3 b - - 0 1")
        self.assertEqual(obj.push_uci_move("d5e4"), GAME_STATUS_IN_PROGRESS)
        self.assertEqual(obj.last_move_coords, ((4, 5), (5, 4)))
        self.assertEqual(obj.last_capture_coords, (5, 4))

    def test_en_passant_capture_square_is_the_victim(self):
        obj = with_fen("4k3/8/8/8/3pP3/8/8/4K3 b - e3 0 1")
        self.assertEqual(obj.push_uci_move("d4e3"), GAME_STATUS_IN_PROGRESS)
        self.assertEqual(obj.last_move_coords, ((4, 4), (5, 3)))
        self.assertEqual(obj.last_capture_coords, (5, 4))

    def test_castling_reports_rook_and_no_capture(self):
        obj = with_fen("r3k3/8/8/8/8/8/8/4K3 b q - 0 1")
        self.assertEqual(obj.push_uci_move("e8c8"), GAME_STATUS_IN_PROGRESS)
        self.assertEqual(obj.last_rook_move, ((1, 8), (4, 8)))
        self.assertEqual(obj.last_capture_coords, None)

    def test_underpromotion_becomes_a_queen(self):
        obj = with_fen("4k3/8/8/8/8/8/p7/4K3 b - - 0 1")
        self.assertEqual(obj.push_uci_move("a2a1n"), GAME_STATUS_IN_PROGRESS)
        piece = obj.board.piece_at(chess.A1)
        self.assertEqual(piece.piece_type, chess.QUEEN)

    def test_illegal_or_garbage_move_is_ignored(self):
        obj = CivChessObj()
        fen = obj.board.fen()
        self.assertEqual(obj.push_uci_move("e2e5"), GAME_STATUS_IGNORED)
        self.assertEqual(obj.push_uci_move("zz"), GAME_STATUS_IGNORED)
        self.assertEqual(obj.board.fen(), fen)

    def test_engine_checkmate(self):
        # fool's mate: Black mates with Qh4#
        obj = CivChessObj()
        play(obj, "f2f3")
        obj.push_uci_move("e7e5")
        play(obj, "g2g4")
        self.assertEqual(obj.push_uci_move("d8h4"), GAME_STATUS_CHECKMATE)
        self.assertEqual(obj.legal_moves_string(), "")


if __name__ == "__main__":
    unittest.main()
