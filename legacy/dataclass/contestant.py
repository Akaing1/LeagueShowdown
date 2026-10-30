from dataclasses import dataclass


@dataclass
class Contestant:
    name: str
    score: int = 0
    active: bool = True
