from dataclasses import dataclass


@dataclass(frozen=True)
class Card:
    number: str


@dataclass(frozen=True)
class Account:
    id: str