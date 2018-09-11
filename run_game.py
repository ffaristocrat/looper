import json

from looper.games import Game


tragedy_sets = json.load(open('definitions/tragedy-sets.json'))
character_definitions = json.load(open('definitions/characters.json'))
scripts = json.load(open('definitions/scripts.json'))

script = scripts['scripts'][0]

game = Game(
    tragedy_sets=tragedy_sets,
    character_definitions=character_definitions
)

print(game.reset(script=script))
print(game.categorical_catalog)

