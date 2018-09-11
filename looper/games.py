import logging
from typing import Dict, List, Set, Callable, NamedTuple
from collections import defaultdict
from itertools import chain

from looper.characters import Character
from looper.locations import Location
from looper.incidents import Incident
from looper.constants import *
from looper.utils import hashit

LOG = logging.getLogger(__name__)


class Snapshot(NamedTuple):
    loop: int = 0
    day: int = 0
    extra_gauge: int = 0
    effects_used_day: Set[str] = None
    effects_used_loop: Set[str] = None
    leader: int = None
    phase: str = None


class Game:
    def __init__(self, tragedy_sets: Dict, character_definitions: Dict):
        self.tragedy_sets = {
            ts['name']: ts.copy() for ts in tragedy_sets['tragedy-sets']
        }
        self.character_definitions = {
            c['name']: c.copy() for c in character_definitions['characters']
        }

        # This is a full list of characters
        self.characters_all: List[Character] = [
            Character(self, c['name'])
            for c in self.character_definitions.values()
        ]

        self.forbid_intrigue_limit = 2

        # This is just the characters in a given script
        self._characters: Dict[str: Character] = {}
        self.script: Dict = None
        self.tragedy_set_def: Dict = None

        self.loops: int = 0
        self.days_per_loop: int = 0

        # 0 = Mastermind
        # 1-3 = Protagonists
        self.leader = 1
        self.player_turn = 0
        self.protagonist_order: List[int] = [1, 2, 3]

        self.extra_gauge = 0
        self.loop = 0
        self.day = 0
        self.history = []

        self.cards_played: List[Set[str]] = [
            set(), set(), set(), set()]
        self.effects_used_day: Set[str] = set()
        self.effects_used_loop: Set[str] = set()
        self.locations: Dict[str, Location] = {
            name: Location(self, name) for name in LOCATION_DIRECTIONS.keys()
        }
        self.incidents: Dict[int, Incident] = {}

        # plot defs
        self.main_plot: Dict = {}
        # TODO: Second main plot for Cosmic Evil
        self.sub_plots: Dict[str: Dict] = {}
        self.revealed_sub_plots: Dict[str: bool] = {}
        self.roles: Dict[str: Dict] = {}

        self.protagonists_have_lost: bool = False
        self.protagonists_have_died: bool = False

        self.phase: str = None

        self.passives: Dict = defaultdict(list)
        self.abilities: List[Dict] = []
        self.validations: List[Callable] = []

        self.ability_stack: List = []
        self.decision_stack: List = []
        self.action_stack: List = []
        self.choice_stack: List = []

    @property
    def incident(self) -> [Incident, None]:
        # DONE

        return self.incidents.get(self.day)
    
    @property
    def incidents_occurred(self) -> List[str]:
        return [
            i.incident for i in self.incidents.values() if i.occurred
        ]
    
    @property
    def characters(self) -> Dict:
        return {
            k: c for k, c in self._characters.items()
            if not c.dead and c.location
        }

    @property
    def mortals(self) -> Dict:
        # DONE

        return {
            k: c for k, c in self._characters.items()
            if not c.dead and c.location and
            not self.roles[c.role].get('unkillable', False)
        }

    @property
    def unkillable(self) -> Dict:
        # DONE

        return {
            k: c for k, c in self._characters.items()
            if not c.dead and c.location and
            self.roles[c.role].get('unkillable', False)
        }

    @property
    def corpses(self) -> Dict:
        # DONE

        return {
            k: c for k, c in self._characters.items()
            if c.dead and c.location
        }

    @property
    def state(self) -> Dict:
        # TODO State!
        # TODO Veil information depending on player
        state = {
            'game': {
                'day': self.day,
                'days_per_loop': self.days_per_loop,
                'loop': self.loop,
                'loops': self.loops,
                'leader': self.leader,
                'extra_gauge': self.extra_gauge,
                'phase': self.phase,
                'protagonists_have_lost': self.protagonists_have_lost,
                'protagonists_have_died': self.protagonists_have_died,
                'effects_used_day': list(self.effects_used_day),
                'effects_used_loop': list(self.effects_used_loop),
                # TODO: Snapshots
            },
            'plots': {
                'main_plot': self.main_plot['name'],
                'sub_plots': list(self.sub_plots.keys()),
                'revealed_sub_plots': list([
                    k for k, v in self.revealed_sub_plots.items() if v]),
            },
            'characters': {
                char.name: {
                    'starting_role': char.starting_role,
                    'location': char.location,
                    'intrigue': char.intrigue,
                    'paranoia': char.paranoia,
                    'goodwill': char.goodwill,
                    'extra': char.extra,
                    'panicked': char.panicked,
                    'dead': char.dead,
                    'revealed': char.revealed,
                    'role': char.role,
                    'revealed_role': char.revealed_role,
                    'mastermind_card': char.mastermind_card,
                    'protagonist_card': char.protagonist_card,
                    # TODO: Shapshots
                } for char in self.characters_all
            },
            'locations': {
                l: {
                    'intrigue': loc.intrigue,
                    'paranoia': loc.paranoia,
                    'goodwill': loc.goodwill,
                    'extra': loc.extra,
                    'mastermind_card': loc.mastermind_card,
                    'protagonist_card': loc.protagonist_card,
                    # TODO: Snapshots
                } for l, loc in self.locations.items()
            },
        }

        return state

    @property
    def categorical_catalog(self) -> Dict:
        # Should be complete for all tragedy sets
        
        catalog = {
            'characters': [c.name for c in self.characters_all],
            'locations': list(LOCATION_DIRECTIONS.keys()) + ['None'],
            'refusal': ['allow', 'refuse'],
            'tokens': TOKENS[:],
            'cards': CARDS[:] + ['card'],
            'tragedy-sets': [ts['name'] for ts in self.tragedy_sets.values()],
            'main-plots': [
                plot['name'] for plot in
                chain.from_iterable([
                    ts['main-plots'] for ts in self.tragedy_sets.values()])
            ],
            'sub-plots': [
                plot['name'] for plot in
                chain.from_iterable([
                    ts['sub-plots'] for ts in self.tragedy_sets.values()])
            ],
            'incidents': [
                i['name'] for i in
                chain.from_iterable([
                    ts['incidents'] for ts in self.tragedy_sets.values()])
            ],
            'roles': [
                role['name'] for role in
                chain.from_iterable([
                    ts['roles'] for ts in self.tragedy_sets.values()])
            ],
            'abilities': [a['id'] for a in self.abilities],
            'pass': ['pass'],
            'amounts': AMOUNTS,
            'days': [1, 2, 3, 4, 5, 6, 7, 8],
            'loops': [1, 2, 3, 4, 5, 6, 7, 8],
            'phases': PHASES,
        }
    
        return catalog

    def role(self, role: str) -> List[Character]:
        return [c for c in self._characters.values() if c.role == role]

    def location(self, location: str) -> List[Character]:
        return [c for c in self.characters if c.location == location]

    def same_location(self, character: [str, Character], role: str=None,
                      include_self: bool=False, trait: str=None
                      ) -> List[Character]:
        name = character if type(character) is str else character.name
        location = self._characters[name].location
        return [
            c for c in self.characters
            if c.location == location and
            (include_self or c.name != name) and
            (not trait or trait in c.traits) and
            (not role or c.role == role)
        ]

    def location_and_characters(self, character: [str, Character],
                                role: str=None, include_self: bool=False,
                                trait: str=None) -> List:
        name = character if type(character) is str else character.name
        location = self._characters[name].location
        return [
            c for c in self.characters
            if c.location == location and
            (include_self or c.name != name) and
            (not trait or trait in c.traits) and
            (not role or c.role == role)
        ] + [self.location(location)]

    @staticmethod
    def attribute_last_loop(target, attribute) -> [bool, int]:
        # DONE

        if not target.history:
            return None

        return getattr(target.history[-1], attribute)

    def alter_token(self, target=None, token: str=None, amount: int=0,
                    character: [Character, str]=None,
                    location: [Location, str]=None, **_):
        if type(character) is str:
            character = self._characters[character]
        elif type(location) is str:
            location = self.location(location)
        target = target or character or location

        current = getattr(target, token, 0)
        if amount < 0:
            amount = current - abs(amount)
            LOG.info(f'Removed {amount} {token} from {target.name}')
        else:
            LOG.info(f'Added {amount} {token} to {target.name}')

        setattr(target, token, current + amount)
        
    def alter_intrigue(self, character: [Character, str]=None,
                       location: [Location, str]=None, amount: int=0,
                       **kwargs):

        self.alter_token(character=character, location=location,
                         token='intrigue', amount=amount, **kwargs)

    def alter_goodwill(self, character: [Character, str]=None,
                       location: [Location, str]=None, amount: int=0,
                       **kwargs):

        self.alter_token(character=character, location=location,
                         token='goodwill', amount=amount, **kwargs)

    def alter_paranoia(self, character: [Character, str]=None,
                       location: [Location, str]=None, amount: int=0,
                       **kwargs):

        self.alter_token(character=character, location=location,
                         token='paranoia', amount=amount, **kwargs)

    def alter_extra(self, character: [Character, str]=None,
                    location: [Location, str]=None, amount: int=0,
                    **kwargs):

        self.alter_token(character=character, location=location,
                         token='extra', amount=amount, **kwargs)

    def alter_extra_gauge(self, amount, **_):
        if (self.extra_gauge + amount) < 0:
            amount = -self.extra_gauge

        if amount > 0:
            LOG.info(f'Added {amount} to extra gauge')
        elif amount < 0:
            LOG.info(f'Remove {-amount} from extra gauge')

        self.extra_gauge += amount

    def move_character(self, character: [str, Character], location: str, **_):
        character = (
            self._characters[character]
            if type(character) is str else character
        )
        char = self.character_definitions[character.name]
        if character.unrestricted_movement:
            prohibited = []
        else:
            prohibited = char['prohibited_locations']

        if location not in prohibited:
            LOG.info(f'The {character.name} moved to the {location}')
            character.location = location
        else:
            LOG.info(f'The {character.name} cannot move to the {location}')

    def free_movement(self, character: [str, Character], **_):
        # DONE

        character = (
            self._characters[character]
            if type(character) is str else character
        )
        character.unrestricted_movement = True
        LOG.info(f'The {character.name} can move freely')

    def do_not_trigger_incidents(self, character: [str, Character], **_):
        # DONE

        character = (
            self._characters[character]
            if type(character) is str else character
        )
        character.do_not_trigger_incidents = True
        LOG.info(f'The {character.name} will not trigger incidents')

    def place_card(self, player_idx, card: str, target: str):
        # TODO: separate player & mastermind cards
        # TODO: log cards played in snapshot history
        
        if player_idx:
            player = f'Protagonist #{player_idx}'
        else:
            player = 'The Mastermind'

        target = self._characters.get(
            target, self.locations.get(target))

        target.cards.append(card)
        if player_idx:
            target.protagonist_card = card
        else:
            target.mastermind_card = card

        LOG.info(f'{player} played {card} on the {target}')

        self.cards_played[player_idx].add(card)

    def reveal_role(self, character: [str, Character], revealed_role: str=None,
                    **_):
        character = (
            self._characters[character]
            if type(character) is str else character
        )
        role = self.apply_passives(character, 'characters', 'role')

        # Lie about Ninja role
        character.revealed_role = revealed_role if revealed_role else role

        if not character.revealed:
            LOG.info(f'The {character.name} is revealed to be a '
                     f'{character.revealed_role}')
            character.revealed = True

    def reveal_culprit(self, day: int, **_):
        # DONE
        if day not in self.incidents:
            return

        incident = self.incidents[day]
        incident.revealed = True
        LOG.info(f'{incident.incident} on day {day}'
                 f'culprit is the {incident.culprit}')

    def reveal_sub_plot(self, sub_plot: str=None, **_):
        # TODO: Technically the Mastermind can choose which sub_plot
        # to reveal if named sub_plot isn't in use
        for sp in self.sub_plots.keys():
            if sp != sub_plot and not self.revealed_sub_plots.get(sp, False):
                LOG.info(f'Revealed sub_plot {sp}')
                self.revealed_sub_plots[sp] = True

    def protection_flag(self, character: [str, Character], **_):
        # DONE

        character = (
            self._characters[character]
            if type(character) is str else character
        )
        
        if character.protection_flag:
            return
        
        character.protection_flag = True
        self.alter_extra(character=character, amount=1)

    def mark_character_for_death(self, character: [str, Character], **_):
        # DONE

        character = (
            self._characters[character]
            if type(character) is str else character
        )
        if self.roles[character.role].get('unkillable', False):
            return

        if character.extra >= 1 and character.protection_flag:
            LOG.info(f'The {character.name} is saved from death')
            character.protection_flag = False
            self.alter_extra(character=character, amount=-1)
            return

        if character.dead or character.pending_death:
            return

        character.dead = True
        character.pending_death = True
        character.died_on_day = self.day

        LOG.info(f'The {character.name} is dead')

    def clear_pending_deaths(self):
        for character in self._characters.values():
            character.pending_death = False

    def resurrect_character(self, character: [str, Character], **_):
        # DONE

        character = (
            self._characters[character]
            if type(character) is str else character
        )
        if not character.dead:
            return

        character.dead = False
        character.pending_death = False

        LOG.info(f'The {character.name} is resurrected')

    def protagonists_die(self, **_):
        # DONE
        if self.protagonists_have_died:
            return

        self.protagonists_have_died = True
        self.protagonists_have_lost = True
        LOG.info('The protagonists have died')

    def protagonists_lose(self, **_):
        # DONE
        
        if self.protagonists_have_lost:
            return

        self.protagonists_have_lost = True
        LOG.info('The protagonists have lost')

    def return_once_per_loop_card(self, card: str, **_):
        # DONE

        self.cards_played[self.leader].remove(card)
        LOG.info(f'Protagonist #{self.leader} regained {card}')

    def remove_from_board(self, character: [str, Character], **_):
        # DONE
        character = (
            self._characters[character]
            if type(character) is str else character
        )
        if not character.location:
            return
        
        character.location = None
        LOG.info(f'{character.name} removed from the board')

    def resolve_cards(self):
        """
        The Mastermind reveals them all at the same time. Then, he resolves
        them all in the following order :
        1) Forbid Movement cards.
        2) Movements cards.
        3) Other Forbid cards.
        4) Other remaining action cards.
        """
        
        # TODO: Fix ordering

        self.ignore_multiple_forbid_intrigue_cards()
        self.forbid_cards()
        self.resolve_movement()
        self.resolve_tokens()

    def resolve_tokens(self):
        # DONE

        tokens = [
            'intrigue', 'goodwill', 'paranoia'
        ]
        for k, c in self._characters.items():
            if c.location and self.character_definitions[c].get('use-location-cards'):
                cards = self.locations[c.location].cards[:]
            else:
                cards = c.cards

            for token in tokens:
                amount = 0
                for card in cards:
                    card_type, _, card_amount = card.partition(' ')
                    if card_type == token:
                        amount += card_amount
            
                if amount:
                    self.alter_token(c, token, amount)

        for k, l in self.locations.items():
            for token in tokens:
                amount = 0
                for card in l.cards:
                    card_type, _, card_amount = card.partition(' ')
                    if card_type == token:
                        amount += card_amount

                if amount:
                    self.alter_token(l, token, amount)

    def resolve_movement(self):
        # DONE

        for k, c in self._characters.items():
            if not c.location:
                continue

            if c.location and self.character_definitions[c].get(
                    'use-location-cards', False):
                cards = self.locations[c.location].cards
            else:
                cards = c.cards

            moves = {c for c in cards if c.startswith('MOVEMENT')}
            if not moves:
                continue
                
            move = '|'.join(sorted(set(moves)))

            self.move_character(
                c, LOCATION_DIRECTIONS[c.location][move])

    def forbid_cards(self):
        forbid = [
            'movement', 'forbid', 'goodwill', 'paranoia'
        ]
        
        for f in forbid:
            for k, c in self._characters.items():
                # Time Traveler, Cultist ignore certain forbids
                # TODO: Cultist ignore is technically optional
                # TODO: Cultist ignore also applies to other characters
                # in location
                if f in self.roles[c.role].get('ignore-forbid', []):
                    continue

                if f'forbid {f}' in c.cards:
                    for card in c.cards[:]:
                        if card.startswith(f):
                            c.cards.remove(card)
    
            for k, l in self.locations.items():
                # Cultist ignore forbid intrigues in same location
                # TODO: This is also optional
                ignore_card = False
                for c in self.location(l.name):
                    if f in self.roles[c.role].get(
                            'ignore-forbid-location', []):
                        ignore_card = True
                if ignore_card:
                    continue

                if f'forbid {f}' in l.cards:
                    for card in l.cards[:]:
                        if card.startswith(f):
                            l.cards.remove(card)

    def ignore_multiple_forbid_intrigue_cards(self):
        """ check if forbid intrigue is played twice """
    
        forbid_intrigue_count = 0
        for k, c in self._characters.items():
            if 'forbid intrigue' in c.cards:
                forbid_intrigue_count += 1
        for k, l in self.locations.items():
            if 'forbid intrigue' in l.cards:
                forbid_intrigue_count += 1
    
        # TODO: Passive to bypass forbid intrigue limit
        
        forbid_intrigue_limit = self.apply_passives(
            self, "game", "forbid_intrigue_limit")

        if forbid_intrigue_count >= forbid_intrigue_limit:
            LOG.info('Too many Forbid Intrigue cards')
            for k, c in self._characters.items():
                if 'forbid intrigue' in c.cards:
                    try:
                        c.cards.remove('forbid intrigue')
                    except ValueError:
                        pass
        
            for k, l in self.locations.items():
                if 'forbid intrigue' in l.cards:
                    try:
                        l.cards.remove('forbid intrigue')
                    except ValueError:
                        pass

    def check_for_incident(self):
        # TODO: Actually do incident
        # TODO: Check for apply_passives
    
        incident = self.incidents.get(self.day)

        if incident:
            char = self._characters[incident.culprit]
            char_def = self.character_definitions[char.name]

            paranoia_incident = self.apply_passives(
                char, 'characters', 'paranoia_incident')
            paranoia_limit = self.apply_passives(
                char, 'characters', 'paranoia_limit'
            )

            if paranoia_incident < paranoia_limit:
                LOG.info(f'{incident.name} did not occur')
                incident.did_not_occur = True

    def apply_passives(self, target, context: str, attribute: str):
        value = getattr(target, attribute)

        funcs = self.passives.get((context, attribute), [])

        # TODO: fix passive functions
        for func in funcs:
            value = func(value, self, )

        return value
    
    def get_effects(self, phase: str):
        pass

    def setup_script(self, script: Dict, skill: str='normal'):
        """ Setup characters, roles, plots """
        self.script = script
        self.tragedy_set_def = self.tragedy_sets[script['tragedy-set']]

        self.main_plot = [
            plot for plot in self.tragedy_set_def['main-plots']
            if script['main-plot'] == plot['name']
        ][0]
        self.sub_plots = {
            plot['name']: plot for plot in self.tragedy_set_def['sub-plots']
            if plot['name'] in script['sub-plots']
        }
        roles = set(script['roles'].values())
        self.roles = {
            role['name']: role for role in self.tragedy_set_def['roles']
            if role['name'] in roles
        }

        self.loops = script['skill'][skill]['loops']
        self.days_per_loop = script['days']

        for i in script.get('incidents', []):
            self.incidents[i['day']] = Incident(self, i)

        for c in self.characters_all:
            c.starting_role = None
            c.starting_location = None
    
            if c.name in script['roles']:
                c.starting_role = script['roles'][c.name]
                # Get starting location, fall back to script spec
                # ie: Henchman
                c.starting_location = \
                    self.character_definitions[c.name].get(
                        'starting-location',
                        script.get('starting-locations', {}).get(
                            c.name
                        )
                    )

        # The _characters dict only has characters used in the script
        self._characters = {
            c.name: c for c in self.characters_all if c.starting_role
        }
        
        all_effects = []

        # TODO: Collect all effects from all tragedy sets

        for name, char_def in self.character_definitions.items():
            for effect in char_def.get('effects', []):
                effect['character'] = name
                effect['id'] = hashit(effect)
                all_effects.append(effect)
                
        for ts in self.tragedy_sets.values():
            for mp in ts.get('main-plots', []):
                mp['tragedy-set'] = ts['name']
        
                for effect in mp.get('effects', []):
                    effect['main-plot'] = mp['name']
                    effect['tragedy-set'] = ts['name']
                    effect['id'] = hashit(effect)
                    all_effects.append(effect)
                mp['id'] = hashit(mp)

            for sp in ts.get('sub-plots', []):
                sp['tragedy-set'] = ts['name']
        
                for effect in sp.get('effects', []):
                    effect['sub-plot'] = sp['name']
                    effect['tragedy-set'] = ts['name']
                    effect['id'] = hashit(effect)
                    all_effects.append(effect)
                sp['id'] = hashit(sp)

            for r in ts.get('roles', []):
                r['tragedy-set'] = ts['name']
    
                for effect in r.get('effects', []):
                    effect['role'] = r['name']
                    effect['goodwill_refusal'] = r.get('goodwill_refusal')
                    effect['tragedy-set'] = ts['name']
                    effect['id'] = hashit(effect)
                    all_effects.append(effect)
                r['id'] = hashit(r)

            ts['id'] = hashit(ts)

        self.passives.clear()
        self.abilities.clear()
        self.validations.clear()

        for e in all_effects:
            if e['phase'] == 'passive':
                key = (e['context'], e['attribute'])
                func = self.compile_passive(e)
                self.passives[key].append(func)
            elif e['phase'] == 'validation':
                self.validations.append(self.compile_validation(e))
            else:
                self.abilities.append(self.compile_ability(e))

    def compile_validation(self, effect: Dict) -> Callable:
        pass

    def compile_passive(self, effect: Dict) -> Callable:
        """
        Passive functions are passed
        item = from looping through collection of characters, locations, etc
        v = value being altered
        g = Game
        c = Character (owner of the ability, culprit, etc)
        l = Location
        p = Plot

        """
        effect_id = hashit(effect)

        actions = [
            eval('lambda v, g, c, l, p: ' + a['eval']
                 ) for a in effect['actions']
        ]

        condition = self.compile_condition(effect)
        plot = effect.get('main-plot', effect.get('sub-plot'))

        def passive(value, character: Character=None, location: Location=None):
            if condition(self, character, location, plot, effect_id):
                for action in actions:
                    value = action(
                        value, self, character, location, plot, effect_id)
            return value

        return passive

    def compile_ability(self, effect: Dict) -> Dict:
        cannot_be_refused = effect.get('cannot-be-refused', False)
        phase = (
            'mandatory_' if effect.get('mandatory', False)
            else 'optional_'
        ) + effect['phase']

        condition = self.compile_condition(effect)
        choices = self.compile_choices(effect)
        actions = self.compile_actions(effect)

        compiled = {
            'id': effect['id'],
            'phase': phase,
            'condition': condition,
            'cannot_be_refused': cannot_be_refused,
            'choices': choices,
            'actions': actions,
        }

        return compiled

    def compile_choices(self, effect: Dict) -> List[Dict]:
        return [
            self.compile_choice(effect, decision)
            for decision in effect.get('decision', [])
        ]

    @staticmethod
    def compile_choice(effect: Dict, decision: Dict) -> Dict:
        """
        Decision functions are passed
        item = from looping through collection of characters, locations, etc
        d = list of decisions (each a list of str) so far
        g = Game
        c = Character (owner of the ability, culprit, etc)

        choices is one of
            characters
            roles
            locations
            cards
            plots
            incidents
            tokens
        
        """

        condition_str = effect.get('condition')
        if condition_str:
            condition = eval(
                f'lambda item, d, g, c: {condition_str}')
        else:
            # default to select them all
            condition = (lambda item, d, g, c, l, p: True)

        decision = {
            # choice == false means everyone who matches will be used
            'choice': decision.get('choice', True),
            'type': decision['type'],
            'condition': condition,
        }

        return decision

    def compile_actions(self, effect: Dict):
        """
        Action items have
            decision = which decision to iterate over
            action = which action to execute
            arguments to eval for the action
                token: str
                amount: int
                character: str
                location: str
                card: str
                day: int
                main_plot: str
                sub_plot: str

        action functions are passed
            item = from looping through decisions
            d = list of all decisions (each a list of str)
            g = Game
        """

        action_map = {
            'alter_token': self.alter_token,
            'alter_intrigue': self.alter_intrigue,
            'alter_goodwill': self.alter_goodwill,
            'alter_paranoia': self.alter_paranoia,
            'alter_extra': self.alter_extra,
            'alter_extra_gauge': self.alter_extra_gauge,
            'move_character': self.move_character,
            'free_movement': self.free_movement,
            'do_not_trigger_incidents': self.do_not_trigger_incidents,
            'reveal_role': self.reveal_role,
            'reveal_culprit': self.reveal_culprit,
            'reveal_sub_plot': self.reveal_sub_plot,
            'protection_flag': self.protection_flag,
            'mark_character_for_death': self.mark_character_for_death,
            'resurrect_character': self.resurrect_character,
            'protagonists_die': self.protagonists_die,
            'protagonists_lose': self.protagonists_lose,
            'return_once_per_loop_card': self.return_once_per_loop_card,
            'remove_from_board': self.remove_from_board,
        }

        args = [
            'token', 'amount', 'character', 'location', 'card',
            'day', 'main_plot', 'sub_plot', 'target',
        ]

        compiled = []
        for action in effect.get('actions', []):
            # default to iterating over first decision
            decision = action.get('decision', 0)
            action_func = action_map[action['action']]
            kwargs_funcs = {}

            for arg in args:
                if arg in action:
                    string = action.pop(arg)
                    kwargs_funcs[arg] = eval(
                        f'lambda item, d, g: {string}')
                elif arg in ['target', 'character', 'location', 'day']:
                    # If not specified, default to item
                    kwargs_funcs[arg] = eval(
                        f'lambda item, d, g: item')

            def execute_action(decisions):
                if decisions:
                    for item in decisions[decision]:
                        # evaluate arguments
                        kwargs = {
                            k: v(item, decisions, self)
                            for k, v in kwargs_funcs.items()
                        }
                        action_func(**kwargs)
                else:
                    kwargs = {
                        k: v(None, [], self)
                        for k, v in kwargs_funcs.items()
                    }
                    action_func(**kwargs)

            compiled.append(execute_action)

        return compiled

    @staticmethod
    def compile_condition(effect: Dict) -> Callable:
        """
        Condition functions are passed
        g = Game
        c = Character (owner of the ability, culprit, etc)
        l = Location
        p = Plot
        They'll be passed as none if they're not applicable

        """
        effect_id = effect['id']

        funcs = []

        phase = (
            ('mandatory_' if effect.get('mandatory') else 'optional_') +
            effect['phase']
        )
        funcs.append(
            lambda g, c, l, p: g.phase == phase
        )

        character = effect.get('character')
        if character:
            funcs.append(
                lambda g, c, l, p: c and c.name == character
            )

        role = effect.get('role')
        if role:
            funcs.append(
                lambda g, c, l, p:
                c and g.apply_passives(c, "characters", "role") == role
            )

        # Cosmic Evil subplot allows swapping out the main plot
        main_plot = effect.get('main-plot')
        if main_plot:
            funcs.append(
                lambda g, c, l, p:
                g.apply_passives(g, "game", "main_plot") == main_plot
            )

        sub_plot = effect.get('sub-plot')
        if sub_plot:
            funcs.append(
                lambda g, c, l, p:
                sub_plot in [p['name'] for p in g.sub_plots]
            )

        tragedy_set = effect.get('tragedy-set')
        if tragedy_set:
            funcs.append(
                lambda g, c, l, p:
                tragedy_set == g.tragedy_set['name']
            )

        must_be_alive = effect.get('must-be-alive', True)
        if must_be_alive:
            # c will be none if it's a plot/set effect
            funcs.append(
                lambda g, c, l, p: not c or not c.dead
            )

        goodwill_threshold = effect.get('goodwill-required', 0)
        if goodwill_threshold:
            funcs.append(
                lambda g, c, l, p: c.goodwill >= goodwill_threshold)

        once_per_loop = effect.get('once-per-loop', False)
        if once_per_loop:
            funcs.append(
                lambda g, c, l, p: effect_id not in g.effects_used_loop
            )

        funcs.append(
            lambda g, c, l, p: effect_id not in g.effects_used_day
        )

        # Character must be on the board
        funcs.append(
            lambda g, c, l, p: not c or c.location
        )

        # Finally the specific condition
        condition_str = effect.get('condition')
        if condition_str:
            funcs.append(
                eval('lambda g, c, l, p: ' + condition_str)
            )

        # Combine them all into one function
        condition = (lambda g, c, l, p: all([
            func(g, c, l, p) for func in funcs]))

        return condition

    def validate_script(self, script: Dict) -> bool:
        """
        Check whether the script is internally consistent with rules
        """

        passed = True
        for func in self.validations:
            msg = func(script)

            if msg:
                LOG.info(msg)
                passed = False

        return passed

    def time_spiral(self):
        LOG.info('TIME SPIRAL')
        # TODO: test for predictions?

    def reset_character(self, character: Character):
        """ Return to starting location, remove tokens, reset role """

        if not character.starting_role:
            return

        character.dead = False
        character.pending_death = False
        character.died_on_day = 0
        character.protection_flag = False

        character.unrestricted_movement = False
        character.do_not_trigger_incidents = False

        # Godly Being
        enter_on_loop = self.script.get(
            'enter-on-loop', {}).get(character.name, 0)

        # Transfer Student
        enter_on_day = self.script.get(
            'enter-on-day', {}).get(character.name, 0)

        if self.loop >= enter_on_loop and not enter_on_day:
            character.location = character.starting_location

        if self.loop == enter_on_loop:
            LOG.info(f'The {character.name} appears'
                     f'in the {character.location}')

        character.role = character.starting_role
        character.paranoia = 0
        character.intrigue = 0
        character.goodwill = 0
        character.extra = 0
        character.cards.clear()

    @staticmethod
    def reset_location(location: Location):
        # DONE

        location.paranoia = 0
        location.intrigue = 0
        location.goodwill = 0
        location.extra = 0
        location.cards.clear()
        
    @staticmethod
    def reset_incident(incident: Incident):
        # DONE

        incident.occurred = False
        incident.did_not_occur = False

    def start_of_loop(self):
        self.loop += 1
        LOG.info(f'Start of loop {self.loop}')
        self.protagonists_have_lost = False
        self.protagonists_have_died = False

        if self.tragedy_set_def.get('reset-extra-gauge', True):
            self.extra_gauge = 0
        self.day = 0

        for c in self._characters.values():
            self.reset_character(c)

        for l in self.locations.values():
            self.reset_location(l)

        for i in self.incidents.values():
            self.reset_incident(i)

        for played in self.cards_played:
            played.clear()
            
        self.effects_used_loop.clear()

        # TODO: Henchman choice

    def start_of_day(self):
        self.day += 1
        LOG.info(f'Start of day {self.day}')

        for char, day in self.script.get('enter-on-day', {}).items():
            character = self._characters[char]
            if self.day == day and not character.location:
                self.move_character(character, character.starting_location)
                LOG.info(
                    f'The {character.name} appears'
                    f'in the {character.location}')

        for char in self.characters_all:
            char.mastermind_card = None
            char.protagonist_card = None

        for loc in self.locations.values():
            loc.mastermind_card = None
            loc.protagonist_card = None

        self.effects_used_day.clear()

    def end_of_day(self):
        self.rotate_leader()

    def end_of_loop(self):
        self.take_snapshots()

    def take_snapshots(self):
        # DONE

        for k, c in self._characters.items():
            c.take_snap_shot()

        for k, l in self.locations.items():
            l.take_snap_shot()

        for k, i in self.incidents.items():
            i.take_snapshot()

        self.take_snapshot()
        
    def clear_history(self):
        # DONE

        for c in self._characters.values():
            c.history.clear()
            c.revealed = False
            c.revealed_role = None
    
        for l in self.locations.values():
            l.history.clear()
    
        for i in self.incidents.values():
            i.history.clear()
    
        self.history.clear()

    def take_snapshot(self):
        # DONE

        self.history.append(Snapshot(
            self.loop,
            self.day,
            self.extra_gauge,
            self.effects_used_day.copy(),
            self.effects_used_loop.copy(),
            self.leader,
            self.phase,
        ))

    def rotate_leader(self):
        # DONE

        self.leader += 1
        if self.leader > 3:
            self.leader = 1

        if self.leader == 1:
            self.protagonist_order = [1, 2, 3]
        elif self.leader == 2:
            self.protagonist_order = [2, 3, 1]
        elif self.leader == 3:
            self.protagonist_order = [3, 1, 2]

        LOG.info(f'Protagonist #{self.leader} is now Leader')

    def reset(self, script=None):
        LOG.info('Resetting environment')
        if script:
            self.setup_script(script)

        if not self.script:
            raise ValueError

        for c in self._characters.values():
            c.history.clear()
            c.revealed = False
            c.revealed_role = None

        for l in self.locations.values():
            l.history.clear()

        for i in self.incidents.values():
            i.history.clear()

        self.history.clear()
        self.ability_stack.clear()
        self.choice_stack.clear()
        self.decision_stack.clear()
        self.action_stack.clear()
        
        self.phase = 'reset'
        self.extra_gauge = 0
        self.loop = 0
        self.day = 0
        self.leader = 1

        self.revealed_sub_plots.clear()

        return self.step(None)

    def process_stacks(self, action: Dict):
        if self.action_stack and not self.choice_stack:
            # execute all actions
            pass

        if self.choice_stack:
            # send back choices
            pass

        if self.ability_stack:
            # ask for choice of ability
            # or pass
            
            if action.get('pass') == 'pass':
                self.ability_stack.clear()
                self.choice_stack.clear()
                self.decision_stack.clear()
                self.action_stack.clear()

    def step(self, action: [Dict, None]):
        """
        Step through each phase
        Collect relevant effects
            mandatory
            optional
        pass back state for decisions
           even if they just have one choice
        process decisions
        check for refusal
        run actions
        check for deaths
        check for protagonists lose
        
        go to next step
        
        
        Gets prefixed with mandatory/optional
        probably build a list of phases to step through
        have queue for effects, decisions, actions
        
        If queues are empty, step through next phase
        if queue has item, process first
        """
        # TODO: main loop

        return self.state
