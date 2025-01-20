import logging

LOG = logging.getLogger(__name__)


class GameException(Exception):
    pass


class ProtagonistsLoseException(GameException):
    pass


class Effect:
    def __init__(self, target=None, owner=None):
        self.target = target
        self.owner = owner

    def needs_input(self):
        return False

    def options(self):
        return []

    def validate_choice(self, choice):
        return choice in self.options()

    def execute(self):
        pass


class ProtagonistsLose(Effect):
    def execute(self):
        LOG.info("Protagonists lose")
        raise ProtagonistsLoseException


class KillCharacter(Effect):
    def execute(self):
        LOG.info("{}")
