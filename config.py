import os
import logging
from pathlib import Path


class Config:
    BASE_DIR = Path(__file__).parent
    LOG_DIR = BASE_DIR / "logs"

    LOG_DIR.mkdir(exist_ok=True)

    # SERVER_SECRET = os.getenv('GAMESHOW_SECRET', 'dev-secret-123')
    PORT = 8008
    MAX_PLAYERS = 3

    @staticmethod
    def setup_logger(name: str, level=logging.INFO):
        logger = logging.getLogger(name)
        logger.setLevel(level)

        # File handler
        log_file = Config.LOG_DIR / f"{name}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))

        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter(
            '%(levelname)s - %(message)s'
        ))

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        return logger


config = Config()
