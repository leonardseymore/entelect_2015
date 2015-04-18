# AAA: Your Ship
# VVV: Opponent's Ship
# XXX: Alien Factory
# MMM: Missile Controller
# #: Wall
# -: Shield
# x: Alien
# |: Alien Bullet
# !: Your Missiles
# i: Opponent's Missiles

NOTHING = 'Nothing'
MOVE_LEFT = 'MoveLeft'
MOVE_RIGHT = 'MoveRight'
SHOOT = 'Shoot'
BUILD_ALIEN_FACTORY = 'BuildAlienFactory'
BUILD_MISSILE_CONTROLLER = 'BuildMissileController'
BUILD_SHIELD = 'BuildShield'

WALL = 'Wall'
ALIEN = 'Alien'
SHIP = 'Ship'
SHIELD = 'Shield'
EMPTY = None
MISSILE = 'Missile'
BULLET = 'Bullet'
ALIEN_FACTORY = 'AlienFactory'
MISSILE_CONTROLLER = 'MissileController'

WALL_SYMBOL = '#'
ALIEN_SYMBOL = 'x'
SHIP_PLAYER1_SYMBOL = 'A'
SHIP_PLAYER2_SYMBOL = 'V'
SHIELD_SYMBOL = '-'
EMPTY_SYMBOL = ' '
MISSILE_PLAYER1_SYMBOL = '!'
MISSILE_PLAYER2_SYMBOL = 'i'
BULLET_SYMBOL = '|'
ALIEN_FACTORY_SYMBOL = 'X'
MISSILE_CONTROLLER_SYMBOL = 'M'

TEXT_TO_SYMBOL = {
    WALL: WALL_SYMBOL,
    ALIEN: ALIEN_SYMBOL,
    SHIELD: SHIELD_SYMBOL,
    EMPTY: EMPTY_SYMBOL,
    BULLET: BULLET_SYMBOL,
    ALIEN_FACTORY: ALIEN_FACTORY_SYMBOL,
    MISSILE_CONTROLLER: MISSILE_CONTROLLER_SYMBOL
}


def cell_to_symbol(cell):
    if not cell:
        return EMPTY_SYMBOL

    text = cell['Type']
    if text == MISSILE:
        if cell['PlayerNumber'] == 1:
            return MISSILE_PLAYER1_SYMBOL
        else:
            return MISSILE_PLAYER2_SYMBOL
    elif text == SHIP:
        if cell['PlayerNumber'] == 1:
            return SHIP_PLAYER1_SYMBOL
        else:
            return SHIP_PLAYER2_SYMBOL
    else:
        return TEXT_TO_SYMBOL[text]
