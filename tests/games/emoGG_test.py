import unittest
from unittest.mock import patch, mock_open
from games.emogg import EmoGG, EmoGGRound


class TestEmoGG(unittest.TestCase):
    def setUp(self):
        self.sample_data = """
        [items:Infinity Edge]
        ♾️ ⚔️

        [champions:Ashe]
        🏹 ❄️

        [items:Bloodthirster]
        🩸 🗡️
        """

        self.expected_rounds = [
            EmoGGRound("items", "Infinity Edge", "♾️ ⚔️"),
            EmoGGRound("champions", "Ashe", "🏹 ❄️"),
            EmoGGRound("items", "Bloodthirster", "🩸 🗡️")
        ]

        # Patch the file opening in the class
        self.file_patcher = patch(
            'builtins.open',
            mock_open(read_data=self.sample_data)
        )
        self.mock_open = self.file_patcher.start()

        self.game = EmoGG()

    def tearDown(self):
        self.file_patcher.stop()

    def test_initialization(self):
        self.assertEqual(len(self.game.rounds), 3)
        self.assertEqual(self.game.current_round_index, -1)
        self.assertEqual(self.game.rounds[0].item_name, "Infinity Edge")
        self.assertEqual(self.game.rounds[1].emoji_sequence, "🏹 ❄️")

    def test_file_loading(self):
        self.mock_open.assert_called_once_with(
            "resources/emogg.txt", 'r', encoding='utf-8'
        )

        rounds = self.game.rounds
        self.assertEqual(len(rounds), 3)
        self.assertEqual(rounds[0].item_type, "items")
        self.assertEqual(rounds[1].item_name, "Ashe")
        self.assertEqual(rounds[2].emoji_sequence, "🩸 🗡️")

    def test_init_round_data(self):
        round_data = self.game.init_round_data()

        self.assertEqual(self.game.current_round_index, 0)
        self.assertEqual(round_data['round'], 1)
        self.assertEqual(round_data['total_rounds'], 3)
        self.assertEqual(round_data['emoji_sequence'], "♾️ ⚔️")
        self.assertEqual(round_data['item_type'], "items")
        self.assertEqual(round_data['scoring']['correct'], 200)

    def test_process_guess_correct(self):
        self.game.init_round_data()
        is_correct, points, answer = self.game.process_guess("Infinity Edge")

        self.assertTrue(is_correct)
        self.assertEqual(points, 200)
        self.assertEqual(answer, "Infinity Edge")

    def test_process_guess_incorrect(self):
        self.game.init_round_data()
        is_correct, points, answer = self.game.process_guess("Wrong Guess")

        self.assertFalse(is_correct)
        self.assertEqual(points, -100)
        self.assertEqual(answer, "Infinity Edge")

    def test_case_insensitive_guess(self):
        self.game.init_round_data()
        is_correct, _, _ = self.game.process_guess("iNfInItY eDgE")
        self.assertTrue(is_correct)

    def test_round_progression(self):
        round1 = self.game.init_round_data()
        self.assertEqual(round1['item_name'], "Infinity Edge")

        round2 = self.game.init_round_data()
        self.assertEqual(round2['item_name'], "Ashe")

        round3 = self.game.init_round_data()
        self.assertEqual(round3['item_name'], "Bloodthirster")

    def test_no_more_rounds(self):
        for i in range(3):
            self.game.init_round_data()

        with self.assertRaises(ValueError):
            self.game.init_round_data()

    def test_process_guess_no_active_round(self):
        with self.assertRaises(ValueError):
            self.game.process_guess("Test Guess")

    def test_get_game_state(self):
        state = self.game.get_game_state()
        self.assertEqual(state['status'], 'no_active_round')

        self.game.init_round_data()
        state = self.game.get_game_state()
        self.assertEqual(state['current_round'], 1)
        self.assertEqual(state['total_rounds'], 3)

    def test_file_not_found(self):
        with patch('builtins.open', side_effect=FileNotFoundError()):
            game = EmoGG()
            self.assertGreater(len(game.rounds), 0)
            self.assertEqual(game.rounds[0].item_name, "Infinity Edge")


if __name__ == '__main__':
    unittest.main()
