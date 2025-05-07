from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from pathlib import Path
from config import config

logger = config.setup_logger('emo_gg')


@dataclass
class EmoRound:
    answer: str
    emoticons: List[str]
    hints_used: int = 0

    def __post_init__(self):
        logger.debug(f"Loaded round: {self.answer}")


class EmoGG:
    ROUNDS_FILE = "emo_gg_rounds.txt"  # Path to your data file

    def __init__(self):
        self.logger = config.setup_logger('emo_gg.core')
        self.rounds = self._load_rounds()
        self.current_round_index = -1
        self.score = 0
        self.logger.info(f"Game initialized with {len(self.rounds)} rounds")

    def _load_rounds(self) -> List[EmoRound]:
        rounds = []
        try:
            with open(self.ROUNDS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    try:
                        answer, emojis = line.split("|", 1)
                        rounds.append(EmoRound(
                            answer=answer.strip(),
                            emoticons=[e.strip() for e in emojis.split(",")]
                        ))
                    except ValueError as e:
                        self.logger.error(f"Invalid line format: {line} | Error: {e}")
                        continue

            if len(rounds) < 10:
                self.logger.warning(f"Only {len(rounds)} rounds loaded (minimum 10 required)")

        except FileNotFoundError:
            self.logger.critical(f"Rounds file not found: {self.ROUNDS_FILE}")
            raise

        return rounds[:10]  # Use first 10 rounds

    def start_next_round(self) -> Optional[Dict]:
        self.current_round_index += 1

        if self.current_round_index >= min(len(self.rounds), 10):
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
            "emoticons": self.current_round.emoticons,
            "scoring": {"correct": 200, "wrong": -100}
        }

    def guess(self, attempt: str) -> Tuple[bool, int]:
        if not self.current_round:
            self.logger.warning("Guess attempted with no active round")
            return False, 0

        is_correct = attempt.lower() == self.current_round.answer.lower()
        points = 200 if is_correct else -100
        self.score += points

        self.logger.info(
            f"Round {self.current_round_index + 1} | "
            f"{'CORRECT' if is_correct else 'WRONG'} | "
            f"Score: {points} | "
            f"Total: {self.score}"
        )
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
            "hints_remaining": (
                len(self.current_round.emoticons) - self.current_round.hints_used
                if self.current_round else 0
            )
        }