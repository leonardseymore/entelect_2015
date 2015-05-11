from ai.entelect import *
from ai.domain import *

game_state = load_state()
state = State.from_game_state(game_state)

if state.check_open(15, 1, 1) or state.check_open(16, 1, 1) or state.check_open(17, 1, 1):
    write_move(BUILD_SHIELD)
else:
    write_move(NOTHING)

