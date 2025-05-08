from dataclass.whoAmIHint import WhoAmIHint
from typing import List, Dict, Tuple
from config import config
import re

logger = config.setup_logger('whoami')


class WhoAmI:
    name = "Who is this Champion?"
    CHAMPIONS_FILE = "resources/champions.txt"

    def __init__(self):
        self.current_champion = None
        self.rounds = self._load_champions_data()
        self.current_round = -1
        self.hints: List[WhoAmIHint] = []
        self.next_hint_index = 0
        logger.info(f"Initialized {self.name} with {len(self.rounds)} rounds")

    def _load_champions_data(self) -> List[Dict]:
        rounds = []

        try:
            with open(self.CHAMPIONS_FILE, 'r', encoding='utf-8') as file:
                content = file.read()

            champion_blocks = re.split(r'\[Champion:\s*(.*?)]', content)[1:]

            for i in range(0, len(champion_blocks), 2):
                champion = champion_blocks[i].strip()
                hints_text = champion_blocks[i + 1].strip()

                hints = [hint.strip('- ').strip()
                         for hint in hints_text.split('\n')
                         if hint.startswith('-')]

                if champion and hints:
                    rounds.append({
                        "champion": champion,
                        "hints": hints
                    })

            logger.info(f"Loaded {len(rounds)} champions from {self.CHAMPIONS_FILE}")

        except FileNotFoundError:
            logger.error(f"Champions file not found: {self.CHAMPIONS_FILE}")
            rounds = [
                {
                    "champion": "Default Champion 1",
                    "hints": [
                        "Hint 1",
                        "Hint 2",
                        "Hint 3"
                    ]
                }
            ]

        return rounds

    def init_data(self) -> Dict:
        self.current_round += 1

        if self.current_round >= len(self.rounds):
            logger.error("No more rounds available")
            raise ValueError("All rounds completed")

        current_data = self.rounds[self.current_round]
        self.current_champion = current_data["champion"]
        self.hints = [WhoAmIHint(text=hint, reveal_order=i)
                      for i, hint in enumerate(current_data["hints"])]
        self.next_hint_index = 0

        logger.info(
            f"Round {self.current_round + 1}/{len(self.rounds)} started | "
            f"Champion: {self.current_champion} | "
            f"Total hints: {len(self.hints)}"
        )
        return {
            'round': self.current_round + 1,
            'total_rounds': len(self.rounds),
            'hints': [hint.text for hint in self.hints],
            'scoring': {
                'correct': +100,
                'wrong': -100
            },
            'theme': 'league_of_legends',
            'champion': self.current_champion
        }

    def process_guess(self, guess: str) -> Tuple[bool, int]:
        clean_guess = guess.strip().lower()
        is_correct = clean_guess == self.current_champion.lower()

        if is_correct:
            logger.info(
                f"Round {self.current_round + 1} | Correct guess | "
                f"Champion: {self.current_champion} | +100 points"
            )
            return True, 100

        logger.info(
            f"Round {self.current_round + 1} | Wrong guess | "
            f"Champion: {self.current_champion} | -100 points"
        )
        return False, -100

    def reveal_hint(self) -> str:
        if self.next_hint_index >= len(self.hints):
            logger.warning(
                f"Round {self.current_round + 1} | "
                "All hints already revealed"
            )
            return "No more hints available"

        hint = self.hints[self.next_hint_index]
        hint.revealed = True
        self.next_hint_index += 1

        logger.info(
            f"Round {self.current_round + 1} | "
            f"hint {self.next_hint_index}/{len(self.hints)} revealed | "
            f"Champion: {self.current_champion} | "
            f"hint: '{hint.text}'"
        )
        return hint.text

    def get_round_state(self) -> Dict:
        return {
            'round_number': self.current_round + 1,
            'total_rounds': len(self.rounds),
            'champion': self.current_champion,
            'revealed_hints': [
                hint.text for hint in
                sorted(filter(lambda c: c.revealed, self.hints),
                       key=lambda x: x.reveal_order)
            ],
            'remaining_hints': len(self.hints) - self.next_hint_index
        }
