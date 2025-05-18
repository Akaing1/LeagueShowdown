import time
from typing import List
from threading import Event

from src.games import EmoGG
from src.games.who_am_i import WhoAmI

from src.config.config import config
from src.dataclass.contestant import Contestant
from src.utilities.pause_util import GamePauseController
from src.utilities.process_guess import ProcessGuess

logger = config.setup_logger('gameshow')


class GameShow:
    def __init__(self, contestants: List[str]):
        self.contestants = [Contestant(name) for name in contestants]

        self.games = [WhoAmI(), EmoGG()]
        self.currentGameIndex = 0

        self.pause_event = Event()
        self.interval = 4

        logger.info(f"Initialized game show with {len(contestants)} contestants")

    def start_game(self, gameIndex: int) -> []:
        match gameIndex:
            case 0:
                logger.info(f"Running Who am I?")
                self.runWhoAmI(gameIndex)
            case 1:
                logger.info(f"Running Emo-GG")
                self.runEmoGG(gameIndex)
            case 2:
                logger.info(f"placeholder")
            case 3:
                logger.info(f"placeholder")
            case _:
                raise ValueError("No more games")
        return self.contestants

    def runWhoAmI(self, index: int):
        game = self.games[index]
        game_state = game.get_game_state()

        for round_num in range(game_state['total_rounds']):
            game.init_round_data()

            self.interval = 10

            for _ in range(4):
                game.reveal_hint()

                correct_guess, points = ProcessGuess.process_guess(game, self.interval)

                if correct_guess:
                    self.interval = 0
                    logger.info("Here are the rest of the hints...")
                time.sleep(self.interval)

            if round_num < game_state['total_rounds'] - 1:
                GamePauseController.wait_for_space("Press SPACE for next round...")

    def runEmoGG(self, index: int):
        game = self.games[index]
        gameState = game.get_game_state()

        for rounds in range(gameState['total_rounds']):
            game.init_round_data()
            time.sleep(5)
