from dataclasses import dataclass
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








