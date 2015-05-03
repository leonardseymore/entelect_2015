from ai.entelect import *

game_state = load_state()
blackboard = Blackboard()
blackboard.set('game_state', game_state)
field_analyst.run(blackboard)
state = blackboard.get('state')
print '<<BEFORE>>'
print_state(state)
n = next_state(state)
print '<<AFTER>>'
print_state(n)

write_move(BUILD_SHIELD)
