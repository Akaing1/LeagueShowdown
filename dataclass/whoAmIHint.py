from dataclasses import dataclass


@dataclass
class WhoAmIHint:
    text: str
    revealed: bool = False
    reveal_order: int = 0
