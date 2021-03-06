from abc import abstractmethod
from ai.domain import *
from ai.strategy import *
import logging
import random

class Bot:
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger('bot.%s' % self.name)

    def get_action(self, game_state):
        state = State.from_game_state(game_state)
        return self.get_action_from_state(state)

    @abstractmethod
    def get_action_from_state(self, state):
        pass


class BotRandom(Bot):
    def get_action_from_state(self, state):
        return random.choice(state.get_available_actions())


class BotHaywired(Bot):
    def get_action_from_state(self, state):
        blackboard = Blackboard()
        blackboard.set('state', state)

        def build(build_action):
            build_behavior = Sequence(
                SetSafestBuildingLocation(),
                Selector(
                    Sequence(
                        Inverter(AtLocation()),
                        Inverter(MoveToLocation())
                    ),
                    SetAction(build_action)
                )
            )
            return build_behavior

        behavior = Selector(
            Sequence(
                IsStartingRound(),
                SetAction(SHOOT)
            ),
            Sequence(
                Inverter(HasShip()),
                SetAction(NOTHING)
            ),
            Sequence(
                InDanger(),
                SearchBestAction(4, True)
            ),
            Sequence(
                Selector(
                    Sequence(
                        HasSpareLives(),
                        Inverter(HasAllBuildings()),
                        Selector(
                            Sequence(
                                KillTracer(wait=False)
                            ),
                            Sequence(
                                Inverter(HasMissileController()),
                                build(BUILD_MISSILE_CONTROLLER)
                            ),
                            Sequence(
                                Inverter(HasAlienFactory()),
                                build(BUILD_ALIEN_FACTORY)
                            )
                        )
                    ),
                    KillTracer()
                ),
                Sequence(
                    IsMoveDangerous(),
                    SearchBestAction(4, True)
                )
            )
        )

        flow = []
        behavior.run(blackboard, flow)
        action = blackboard.get('action')
        self.logger.debug('Flow: %s' % ' '.join(str(f) for f in flow))

        if not action:
            action = NOTHING
        return action

class BotVex(BotHaywired):
    def get_action_from_state(self, state):
        if random.random() < 0.2:
            return random.choice(state.get_available_actions())

        return BotHaywired.get_action_from_state(self, state)

BOTS = {'haywired': BotHaywired(), 'random': BotRandom(), 'vex': BotVex()}