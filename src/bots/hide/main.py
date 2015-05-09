from ai.entelect import *
from ai.domain import *

game_state = load_state()
state = State.from_game_state(game_state)

if state.alien_factory:
    write_move(BUILD_SHIELD)
else:
    write_move(BUILD_ALIEN_FACTORY)
