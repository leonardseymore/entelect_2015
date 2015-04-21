import ai.io
import ai.entelect
from ai.expert import field_analyst
from ai.blackboard import Blackboard

game_state = ai.io.load_state()
blackboard = Blackboard()
blackboard.set('game_state', game_state)
field_analyst.run(blackboard)

if blackboard.get('your_alien_factory_built'):
    ai.io.write_move(ai.entelect.BUILD_SHIELD)
else:
    ai.io.write_move(ai.entelect.BUILD_ALIEN_FACTORY)
