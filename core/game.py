import time
from typing import List, Dict, Tuple
from config import config

from games import EmoGG
from games.whoami import WhoAmI
from dataclass.contestant import Contestant

logger = config.setup_logger('gameshow')


class GameShow:
    def __init__(self, contestants: List[str]):
        self.contestants = [Contestant(name) for name in contestants]
        self.games = [WhoAmI(), EmoGG()]

        self.currentGameIndex = 0
        logger.info(f"Initialized game show with {len(contestants)} contestants")

    def start_game(self, gameIndex: int) -> Dict:
        if gameIndex >= len(self.games):
            raise ValueError("No more games")

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
                logger.info(f"No games left!")
        return {}

    def runWhoAmI(self, index: int):
        game = self.games[index]
        gameState = game.get_game_state()

        for rounds in range(gameState['total_rounds']):
            game.init_round_data()
            while game.get_game_state()['remaining_hints']:
                game.reveal_hint()
                time.sleep(5)

    def runEmoGG(self, index: int):
        game = self.games[index]
        gameState = game.get_game_state()

        for rounds in range(gameState['total_rounds']):
            game.init_round_data()
            time.sleep(5)
