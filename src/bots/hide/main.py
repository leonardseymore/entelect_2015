from ai.entelect import *

game_state = load_state()
blackboard = Blackboard()
blackboard.set('game_state', game_state)
field_analyst.run(blackboard)

if blackboard.get('your_alien_factory_built'):
    write_move(BUILD_SHIELD)
else:
    write_move(BUILD_ALIEN_FACTORY)
