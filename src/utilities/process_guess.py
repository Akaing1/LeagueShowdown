import time
import keyboard
from typing import Callable
from src.config.config import config


class ProcessGuess:

    @staticmethod
    def process_guess(game, interval: int) -> int:
        start_time = time.time()
        points = 0
        while time.time() - start_time < interval:
            if keyboard.is_pressed('space'):
                guess = input("\nYour guess? (or press Enter to continue) ").strip()
                if guess:
                    is_correct, points = game.process_guess(guess)
                    print(f"{'✓ Correct!' if is_correct else '✗ Wrong!'} ({points} points)")
            time.sleep(0.1)
        return points
