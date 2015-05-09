from ai.domain import *
from ai.treesearch import *

game_state = load_state()
state = State.from_game_state(game_state)
action = plan_action(state, 6)
# print score, action
print action
write_move(action)
