from typing import NamedTuple, List, Dict


class Snapshot(NamedTuple):
    loop: int
    day: int
    occurred: bool
    no_effect: bool
    revealed: bool


class Incident:
    def __init__(self, game, incident_def: Dict):
        self.game = game
        self.incident_def = incident_def
        self.day = incident_def["day"]
        self.incident = incident_def["incident"]
        self.culprit = incident_def["culprit"]
        self.fake_name = incident_def.get("fake-name")

        self.history: List[Snapshot] = []
        self.revealed: bool = False

        self.occurred: bool = False
        self.no_effect: bool = False

    def take_snapshot(self):
        snapshot = Snapshot(
            self.game.loop, self.day, self.occurred, self.no_effect, self.revealed
        )

        self.history.append(snapshot)
