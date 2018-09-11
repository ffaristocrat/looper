from typing import NamedTuple, List


class Snapshot(NamedTuple):
    loop: int = 0
    day: int = 0
    revealed: bool = False
    dead: bool = False
    died_on_day: int = None
    role: str = None
    location: str = None
    paranoia: int = 0
    intrigue: int = 0
    goodwill: int = 0
    extra: int = 0
    mastermind_card: str = None
    protagonist_card: str = None


class Character:
    def __init__(self, game, name):
        self.game = game
        self.name = name
        self.char_def = self.game.character_definitions[name]

        self.paranoia_limit = self.char_def['paranoia-limit']
        self._traits = self.char_def.get('traits', [])[:]
        self.no_action_cards = self.char_def.get('no-action-cards', False)

        self.starting_role: str = None
        self.starting_location: str = None

        self.history: List[Snapshot] = []

        self.revealed: bool = False
        self.revealed_role: str = None
        self.dead: bool = False
        self.protection_flag: bool = False
        self.pending_death: bool = False
        self.died_on_day: int = None

        self.location: str = None
        self.unrestricted_movement: bool = False

        self.do_not_trigger_incidents: bool = False

        self.role = None
        self.paranoia = 0
        self.intrigue = 0
        self.goodwill = 0
        self.extra = 0
        self.cards: List[str] = []
        self.mastermind_card: str = None
        self.protagonist_card: str = None

    @property
    def traits(self):
        traits = self._traits[:]
        if self.paranoia >= self.paranoia_limit:
            traits.append('panicked')
        if self.dead:
            traits.append('corpse')
        
        return traits
    
    @property
    def panicked(self):
        return self.paranoia >= self.paranoia_limit

    @property
    def paranoia_incident(self):
        return self.paranoia
    
    @property
    def same(self):
        return self.game.same_location(self)

    def take_snap_shot(self):
        snapshot = Snapshot(
            self.game.loop,
            self.game.day,
            self.revealed,
            self.dead,
            self.died_on_day,
            self.role,
            self.location,
            self.paranoia,
            self.intrigue,
            self.goodwill,
            self.extra,
            self.mastermind_card,
            self.protagonist_card,
        )

        self.history.append(snapshot)

    def render(self, mastermind=True):
        string = f'{self.name}: '
        string += 'G' * self.goodwill
        string += 'I' * self.intrigue
        string += 'P' * self.paranoia
        string += 'X' * self.extra
        
        if mastermind:
            string += f"({self.role})"

        return string
