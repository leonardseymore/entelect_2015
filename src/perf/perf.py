from ai.entelect import *
from ai.domain import *
from ai.strategy import MCTS_SEARCH, TREE_SEARCH
import cProfile
import pstats
import logging
import logging.config
import StringIO
import timeit

profiler = cProfile.Profile()
profiler.enable()

resources_dir = os.path.dirname(os.path.realpath(__file__)) + '/../'
game_state = load_state(resources_dir + 'state_end.json')

state = State.from_game_state(game_state)
# repeat = 1000
# time = timeit.timeit('state.clone()', number=repeat, setup="from __main__ import state")
# print '~%.06fs/clone' % (time/repeat)
#
# tree_search = TREE_SEARCH
# repeat = 10
# time = timeit.timeit('tree_search.search(state, 4)', number=repeat, setup='from __main__ import state, tree_search')
# print '~%.06fs/tree_search' % (time/repeat)

mcts = MCTS_SEARCH
repeat = 10
time = timeit.timeit('mcts.search(state)', number=repeat, setup='from __main__ import state, mcts')
print '~%.06fs/mcts' % (time/repeat)

profiler.disable()
s = StringIO.StringIO()
sort_by = 'tottime'
ps = pstats.Stats(profiler, stream=s).sort_stats(sort_by)
ps.print_stats()
print s.getvalue()
