MAX_DAYS = 8
MAX_LOOPS = 8


CHOICE_TYPES = [
    "characters",
    "locations",
    "characters+locations",
    "roles",
    "main-plots",
    "sub-plots",
    "cards",
    "days",
    "amounts",
]

AMOUNTS = ["+1", "-1"]

PHASES = [
    "reset",
    "start_of_game",
    "time_spiral",
    "start_of_loop",
    "start_of_day",
    "mastermind_play_cards",
    "protagonist_play_cards",
    "resolve_cards",
    "mastermind_abilities",
    "goodwill_abilities",
    "goodwill_refusal",
    "incidents",
    "incidents_resolve",
    "end_of_day",
    "end_of_loop",
    "final_guess",
    "death",
]

TOKENS = [
    "intrigue",
    "goodwill",
    "paranoia",
    "extra",
]

CARDS = [
    "movement vertical",
    "movement horizontal",
    "movement x",
    "forbid movement",
    "paranoia +1",
    "paranoia -1",
    "forbid paranoia",
    "goodwill +1",
    "goodwill +2",
    "forbid goodwill",
    "intrigue +1",
    "intrigue +2",
    "forbid intrigue",
]


ONCE_PER_LOOP = {
    "movement x",
    "intrigue +2",
    "paranoia -1",
    "goodwill +2",
    "forbid movement",
}

LOCATION_DIRECTIONS = {
    "Shrine": {
        "movement vertical": "School",
        "movement horizontal": "Hospital",
        "movement x": "City",
        "movement horizontal|movement vertical": "City",
        "movement vertical|movement x": "Hospital",
        "movement horizontal|movement x": "School",
    },
    "City": {
        "movement vertical": "Hospital",
        "movement horizontal": "School",
        "movement x": "Shrine",
        "movement horizontal|movement vertical": "Shrine",
        "movement vertical|movement x": "School",
        "movement horizontal|movement x": "Hospital",
    },
    "Hospital": {
        "movement vertical": "City",
        "movement horizontal": "Shrine",
        "movement x": "School",
        "movement horizontal|movement vertical": "School",
        "movement vertical|movement x": "Shrine",
        "movement horizontal|movement x": "City",
    },
    "School": {
        "movement vertical": "Shrine",
        "movement horizontal": "City",
        "movement x": "Hospital",
        "movement horizontal|movement vertical": "Hospital",
        "movement vertical|movement x": "City",
        "movement horizontal|movement x": "Shrine",
    },
}
