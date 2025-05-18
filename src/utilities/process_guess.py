import time
from typing import Tuple

import keyboard
from src.config.config import config

logger = config.setup_logger('process_guess')


class ProcessGuess:

    @staticmethod
    def process_guess(game, interval: int) -> Tuple[bool, int]:
        start_time = time.time()
        points = 0
        is_correct = False
        while time.time() - start_time < interval:
            if keyboard.is_pressed('space'):
                guess = input("\nYour guess? (or press Enter to continue) ").strip()
                if guess:
                    is_correct, points = game.process_guess(guess)
                    logger.info(f"{'Correct!' if is_correct else 'Wrong!'} ({points} points)")
            time.sleep(0.1)
        return is_correct, points
