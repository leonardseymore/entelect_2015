from ai.domain import *
from copy import deepcopy
import random

game_state = load_state()
state = State.from_game_state(game_state)
print '<<BEFORE %d >>' % state.round_number
print state

actions = state.get_available_actions()
#next_state = deepcopy(state)
action = random.choice(actions)
state.update(action)
print '<<AFTER %s >>' % action
print state

write_move(action)
