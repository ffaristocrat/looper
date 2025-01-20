import logging
from typing import NamedTuple, Dict, List, Set

LOG = logging.getLogger(__name__)


class Snapshot(NamedTuple):
    loop: int = 0
    day: int = 0
    paranoia: int = 0
    intrigue: int = 0
    goodwill: int = 0
    extra: int = 0
    mastermind_card: str = None
    protagonist_card: str = None


class Location:
    name = "TEST"

    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.history = []

        self.paranoia = 0
        self.intrigue = 0
        self.goodwill = 0
        self.extra = 0
        self.cards: List[str] = []
        self.mastermind_card: str = None
        self.protagonist_card: str = None

    def take_snap_shot(self):
        snapshot = Snapshot(
            self.game.loop,
            self.game.day,
            self.paranoia,
            self.intrigue,
            self.goodwill,
            self.extra,
            self.mastermind_card,
            self.protagonist_card,
        )

        self.history.append(snapshot)

    def render(self):
        string = f"{self.name}: "
        string += "G" * self.goodwill
        string += "I" * self.intrigue
        string += "P" * self.paranoia
        string += "X" * self.extra

        return string
