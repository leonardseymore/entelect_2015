import random
import sys
import .. ai.io

MOVES = [
            'Nothing',
            'MoveLeft',
            'MoveRight',
            'Shoot',
            'BuildAlienFactory',
            'BuildMissileController',
            'BuildShield'
        ]	

move = random.choice(MOVES)
ai.io.write_move(move)		
print 'Move - %s' % move
