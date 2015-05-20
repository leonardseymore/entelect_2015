from abc import abstractmethod
from ai.domain import *
from ai.strategy import *


class Bot:
    def __init__(self):
        self.name = self.__class__.__name__

    @abstractmethod
    def get_action(self, game_state):
        pass

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

        standard_behavior = Sequence(
            AlwaysTrue(Selector(
                Sequence(
                    Inverter(HasShip()),
                    SetAction(NOTHING)
                ),
                Sequence(
                    InDanger(),
                    SearchBestAction(4)
                ),
                Sequence(
                    HasSpareLives(),
                    Selector(
                        Sequence(
                            Inverter(FirstWaveKilled()),
                            KillTracer()
                        ),
                        KillTracerNoWait(),
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
                )
            )),
            Sequence(
                IsMoveDangerous(),
                SearchBestAction(4)
            )
        )
        behavior = Selector(
            Sequence(
                IsAlienTooClose(),
                SearchBestAction(4, True)
            ),
            standard_behavior
        )

        standard_behavior.run(blackboard)
        action = blackboard.get('action')

        if not action:
            action = NOTHING
        return action

all_bots = [BotHaywired()]