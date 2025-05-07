from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from config import config

logger = config.setup_logger('emo_gg')


@dataclass
class EmoRound:
    answer: str
    emoticons: List[str]
    hints_used: int = 0

    def __init__(self):
        self.emoticicons = None

    def __post_init__(self):
        logger.debug(f"Round loaded: {self.answer}")


class EmoGG:
    def __init__(self, rounds_data: List[Dict]):
        self.current_round = None
        self.logger = config.setup_logger('emo_gg.core')
        self.rounds = [EmoRound() for r in rounds_data[:10]]  # Take first 10 rounds
        self.current_round_index = -1
        self.score = 0
        self.logger.info(f"Initialized with {len(self.rounds)} rounds")

    def start_next_round(self) -> Optional[Dict]:
        """Progress to next round and return emoji data"""
        self.current_round_index += 1

        if self.current_round_index >= len(self.rounds):
            self.logger.info("All rounds completed")
            return None

        self.current_round = self.rounds[self.current_round_index]
        self.logger.info(
            f"Round {self.current_round_index + 1}/10 started | "
            f"Answer: {self.current_round.answer}"
        )
        return {
            "round_number": self.current_round_index + 1,
            "total_rounds": 10,
            "emoticons": self.current_round.emoticicons,
            "scoring": {
                "correct": +200,
                "wrong": -100
            }
        }

    def guess(self, attempt: str) -> Tuple[bool, int]:
        if not self.current_round:
            self.logger.warning("Guess attempted with no active round")
            return False, 0

        is_correct = attempt.lower() == self.current_round.answer.lower()
        points = 200 if is_correct else -100
        self.score += points

        log_msg = (
            f"Round {self.current_round_index + 1} | "
            f"{'CORRECT' if is_correct else 'WRONG'} | "
            f"Score: {points} | "
            f"Total: {self.score} | "
            f"Answer: {self.current_round.answer}"
        )
        self.logger.info(log_msg)

        return is_correct, points

    def get_hint(self) -> str:
        if not self.current_round:
            self.logger.warning("Hint requested with no active round")
            return "No active round"

        if self.current_round.hints_used >= len(self.current_round.emoticons):
            self.logger.debug("All hints revealed")
            return "No more hints!"

        hint = self.current_round.emoticons[self.current_round.hints_used]
        self.current_round.hints_used += 1

        self.logger.info(
            f"Round {self.current_round_index + 1} | "
            f"Hint {self.current_round.hints_used}/"
            f"{len(self.current_round.emoticons)} revealed"
        )
        return hint

    def get_state(self) -> Dict:
        return {
            "current_round": self.current_round_index + 1,
            "total_rounds": 10,
            "score": self.score,
            "hints_used": self.current_round.hints_used if self.current_round else 0
        }
