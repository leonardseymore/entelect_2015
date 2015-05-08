from ai.domain import *
from ai.treesearch import *

game_state = load_state()
state = State.from_game_state(game_state)
score, action = search_best_action(state, 2)
# print score, action
write_move(action)
