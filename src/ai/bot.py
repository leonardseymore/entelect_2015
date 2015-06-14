from abc import abstractmethod
from ai.domain import *
from ai.strategy import *
import logging
import random

class Bot:
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger('bot.%s' % self.name)

    @abstractmethod
    def get_action(self, game_state):
        pass


class BotRandom(Bot):
    def get_action(self, game_state):
        state = State.from_game_state(game_state)
        return random.choice(state.get_available_actions())


class BotHaywired(Bot):
    def get_action(self, game_state):
        state = State.from_game_state(game_state)

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
                        Selector(
                            Sequence(
                                # Inverter(IsSoleSurvivor()),
                                KillTracerNoWait()
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
                    Sequence(
                        KillTracer(),
                    ),
                ),
                Sequence(
                    IsMoveDangerous(),
                    SearchBestAction(4)
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

BOTS = {'haywired': BotHaywired(), 'random': BotRandom()}