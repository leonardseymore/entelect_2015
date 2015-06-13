from ai.entelect import *
from ai.domain import *
import timeit

resources_dir = os.path.dirname(os.path.realpath(__file__)) + '/../'
game_state = load_state(resources_dir + 'state_end.json')

state = State.from_game_state(game_state)
print state
repeat = 1000
time = timeit.timeit('state.clone()', number=repeat, setup="from __main__ import state")
print '~%.06fs/clone' % (time/repeat)