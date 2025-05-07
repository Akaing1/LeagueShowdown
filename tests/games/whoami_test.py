import unittest
from unittest.mock import patch, mock_open
from games.whoami import WhoAmI, WhoAmIHint
import logging

# Updated test data with Ezreal and Annie
TEST_FILE_CONTENT = """
[Champion: Ezreal]
- I never miss!
- I love double rainbows
- Your museum is not safe with me
- Twinkies

[Champion: Annie]
- I can count to four!
- Fire is not my best friend
- I am a little older than I can count
- Jax's lover
"""


class TestWhoAmIHint(unittest.TestCase):
    """Tests for the WhoAmIHint dataclass"""

    def test_hint_initialization(self):
        hint = WhoAmIHint(text="Test Hint", revealed=True, reveal_order=1)
        self.assertEqual(hint.text, "Test Hint")
        self.assertTrue(hint.revealed)
        self.assertEqual(hint.reveal_order, 1)


class TestWhoAmIFileLoading(unittest.TestCase):
    """Tests for file loading functionality"""

    @patch('builtins.open', mock_open(read_data=TEST_FILE_CONTENT))
    def test_load_champions_data_success(self):
        game = WhoAmI()
        self.assertEqual(len(game.rounds), 2)
        self.assertEqual(game.rounds[0]['champion'], "Ezreal")
        self.assertEqual(game.rounds[0]['hints'], [
            "I never miss!",
            "I love double rainbows",
            "Your museum is not safe with me",
            "Twinkies"
        ])
        self.assertEqual(game.rounds[1]['champion'], "Annie")

    @patch('builtins.open', side_effect=FileNotFoundError())
    @patch('logging.Logger.error')
    def test_file_not_found_fallback(self, mock_log, mock_file):
        game = WhoAmI()
        self.assertEqual(len(game.rounds), 1)  # Falls back to default
        mock_log.assert_called()


class TestWhoAmIGameLogic(unittest.TestCase):
    """Tests for core game logic with Ezreal/Annie data"""

    def setUp(self):
        self.patcher = patch('builtins.open', mock_open(read_data=TEST_FILE_CONTENT))
        self.mock_file = self.patcher.start()
        self.game = WhoAmI()
        self.log_patcher = patch.object(logging.Logger, 'info')
        self.mock_logger = self.log_patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.log_patcher.stop()

    def test_ezreal_round(self):
        round_data = self.game.init_data()  # First round (Ezreal)
        self.assertEqual(round_data['champion'], "Ezreal")

        # Test hints
        self.assertEqual(self.game.reveal_hint(), "I never miss!")
        self.assertEqual(self.game.reveal_hint(), "I love double rainbows")

        # Test guessing
        correct, points = self.game.process_guess("Ezreal")
        self.assertTrue(correct)
        self.assertEqual(points, 100)

    def test_annie_round(self):
        self.game.init_data()  # First round
        self.game.init_data()  # Second round (Annie)

        # Test hints
        self.assertEqual(self.game.reveal_hint(), "I can count to four!")
        self.assertEqual(self.game.reveal_hint(), "Fire is not my best friend")

        # Test case-insensitive guess
        correct, points = self.game.process_guess("aNnIe")
        self.assertTrue(correct)
        self.assertEqual(points, 100)

    def test_hint_reveal_sequence(self):
        self.game.init_data()  # Ezreal round
        hints = [self.game.reveal_hint() for _ in range(4)]
        self.assertEqual(hints, [
            "I never miss!",
            "I love double rainbows",
            "Your museum is not safe with me",
            "Twinkies"
        ])


class TestWhoAmIEdgeCases(unittest.TestCase):
    """Edge case tests"""

    @patch('builtins.open', mock_open(read_data=TEST_FILE_CONTENT))
    def test_all_hints_revealed(self):
        game = WhoAmI()
        game.init_data()
        for _ in range(4): game.reveal_hint()
        self.assertEqual(game.reveal_hint(), "No more hints available")

    @patch('builtins.open', mock_open(read_data="[Champion: Malformed]"))
    def test_malformed_data(self):
        game = WhoAmI()
        self.assertEqual(len(game.rounds), 0)


if __name__ == '__main__':
    unittest.main()
