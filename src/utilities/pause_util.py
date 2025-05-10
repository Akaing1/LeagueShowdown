import time
import keyboard
from typing import Callable
from src.config.config import config

logger = config.setup_logger('pause_util')


class GamePauseController:
    @staticmethod
    def wait_for_space(message: str = "Press SPACE to continue..."):
        logger.info(f"\n{message}")
        while True:
            if keyboard.is_pressed('space'):
                time.sleep(0.2)
                break
            time.sleep(0.1)

    @staticmethod
    def timed_prompt(timeout: float, prompt: str, callback: Callable):
        start_time = time.time()
        while time.time() - start_time < timeout:
            if keyboard.is_pressed('space'):
                user_input = input(prompt)
                if callback(user_input.strip()):
                    return True
            time.sleep(0.1)
        return False
