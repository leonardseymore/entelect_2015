import random
from ai.entelect import *

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
write_move(move)
print 'Move - %s' % move
