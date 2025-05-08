from dataclasses import dataclass
from typing import List, Dict, Tuple
from config import config
import re

logger = config.setup_logger('emogg')


@dataclass
class EmoGGRound:
    item_type: str
    item_name: str
    emoji_sequence: str


class EmoGG:
    name = "EmoGG - League Emoji Guessing Game"
    ROUNDS_FILE = "resources/emogg.txt"

    def __init__(self):
        self.current_round_index = -1
        self.rounds: List[EmoGGRound] = self._load_rounds_data()
        logger.info(f"Initialized {self.name} with {len(self.rounds)} rounds")

    def _load_rounds_data(self) -> List[EmoGGRound]:
        rounds = []
        round_pattern = re.compile(r'\[(items|champions):(.*?)](.*?)(?=\[|$)', re.DOTALL)

        try:
            with open(self.ROUNDS_FILE, 'r', encoding='utf-8') as f:
                content = f.read()

            for match in round_pattern.finditer(content):
                item_type = match.group(1).strip()
                item_name = match.group(2).strip()
                emoji_sequence = match.group(3).strip()

                if item_type and item_name and emoji_sequence:
                    rounds.append(EmoGGRound(
                        item_type=item_type,
                        item_name=item_name,
                        emoji_sequence=emoji_sequence
                    ))

            logger.info(f"Loaded {len(rounds)} rounds from {self.ROUNDS_FILE}")

        except FileNotFoundError:
            logger.error(f"Rounds file not found: {self.ROUNDS_FILE}")
            # Fallback to default rounds
            rounds = [
                EmoGGRound("items", "Infinity Edge", "♾️ ⚔️"),
                EmoGGRound("champions", "Ashe", "🏹 ❄️"),
                EmoGGRound("items", "Bloodthirster", "🩸 🗡️")
            ]

        return rounds

    def init_round(self) -> Dict:
        self.current_round_index += 1

        if self.current_round_index >= len(self.rounds):
            logger.error("No more rounds available")
            raise ValueError("All rounds completed")

        current_round = self.rounds[self.current_round_index]

        logger.info(
            f"Round {self.current_round_index + 1}/{len(self.rounds)} started | "
            f"Type: {current_round.item_type} | "
            f"Item: {current_round.item_name}"
        )

        return {
            'round': self.current_round_index + 1,
            'total_rounds': len(self.rounds),
            'emoji_sequence': current_round.emoji_sequence,
            'item_type': current_round.item_type,
            'item_name': current_round.item_name,
            'scoring': {
                'correct': 200,
                'wrong': -100
            }
        }

    def process_guess(self, guess: str) -> Tuple[bool, int, str]:
        if not 0 <= self.current_round_index < len(self.rounds):
            raise ValueError("No active round")

        current_round = self.rounds[self.current_round_index]
        is_correct = guess.strip().lower() == current_round.item_name.lower()
        points = 200 if is_correct else -100

        logger.info(
            f"Round {self.current_round_index + 1} | "
            f"{'Correct' if is_correct else 'Wrong'} guess | "
            f"Points: {points} | "
            f"Answer: {current_round.item_name}"
        )

        return is_correct, points, current_round.item_name

    def get_game_state(self) -> Dict:
        if not 0 <= self.current_round_index < len(self.rounds):
            return {'status': 'no_active_round'}

        return {
            'current_round': self.current_round_index + 1,
            'total_rounds': len(self.rounds),
            'last_result': None,
            'score': None
        }
