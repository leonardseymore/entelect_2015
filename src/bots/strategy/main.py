from ai.domain import *
from ai.strategy import *

game_state = load_state()
state = State.from_game_state(game_state)

blackboard = Blackboard()
blackboard.set('state', state)

def build(build_action):
    build_behavior = Sequence(
        SetSafestBuildingLocation(),
        Selector(
            Sequence(
                Inverter(AtSafestBuildingLocation()),
                MoveToSafestBuildingLocation()
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
        SearchBestAction()
    ),
    Sequence(
        Selector(
            IsStartingRound(),
            CanKill()
        ),
        HasMissile(),
        SetAction(SHOOT)
    ),
    Sequence(
        HasSpareLives(),
        Selector(
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
        Selector(
            Sequence(
                MoveAcrossBoard(),
                IsMoveDangerous(),
                SearchBestAction(5)
            )
        )
    )
)

behavior.run(blackboard)
action = blackboard.get('action')

if not action:
    action = NOTHING
write_move(action)
