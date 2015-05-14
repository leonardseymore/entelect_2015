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
        SearchBestAction(5)
    ),
    Sequence(
        HasMissile(),
        CanShootBullet(),
        SetAction(SHOOT)
    ),
    Sequence(
        HasSpareLives(),
        Selector(
            Sequence(
                Selector(
                    IsStartingRound(),
                    Kill()
                ),
                HasMissile(),
                SetAction(SHOOT)
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
)

behavior.run(blackboard)
action = blackboard.get('action')

if not action:
    action = NOTHING

print 'Round: %d, Action:%s' % (state.round_number, action)
write_move(action)
