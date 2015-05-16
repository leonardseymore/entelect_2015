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

import os.path
import json
import pickle
import tempfile

DEBUG = False

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
TRACER = 'Tracer'
TRACER_BULLET = 'TracerBullet'

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
TRACER_SYMBOL = '@'
TRACER_BULLET_SYMBOL = '%'

MAP_WIDTH = 19
MAP_HEIGHT = 25

PLAYING_FIELD_HEIGHT = 12
PLAYING_FIELD_WIDTH = 17
YOUR_PLAYING_START = (1,12)
YOUR_PLAYING_END = (17,25)

MAP_TOP = 1
MAP_RIGHT = 17
MAP_BOTTOM = 23
MAP_LEFT = 1

YOUR_SPAWN_LOCATION = (16, 11)
YOUR_SPAWN_THRESHOLD = (16, 9)

ENEMY_SPAWN_LOCATION = (16, 13)
ENEMY_SPAWN_THRESHOLD = (16, 15)

YOUR_SHIELD_FRONT = 19
ENEMY_SHIELD_FRONT = 5

INITIAL_LIVES = 3
INITIAL_ALIEN_WAVE_SIZE = 3
TIME_WAVE_SIZE_INCREASE = 40

REPLAY_DIR='C:/Users/leonard/entelect/harness/Replays/'

TEXT_TO_SYMBOL = {
    WALL: WALL_SYMBOL,
    ALIEN: ALIEN_SYMBOL,
    SHIELD: SHIELD_SYMBOL,
    EMPTY: EMPTY_SYMBOL,
    BULLET: BULLET_SYMBOL,
    ALIEN_FACTORY: ALIEN_FACTORY_SYMBOL,
    MISSILE_CONTROLLER: MISSILE_CONTROLLER_SYMBOL
}

def wave_size_to_bbox_width(wave_size):
    return wave_size * 3 - 2

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

def entity_to_symbol(entity):
    if not entity:
        return EMPTY_SYMBOL

    text = entity.entity_type
    if text == MISSILE:
        if entity.player_number == 1:
            return MISSILE_PLAYER1_SYMBOL
        else:
            return MISSILE_PLAYER2_SYMBOL
    elif text == SHIP:
        if entity.player_number == 1:
            return SHIP_PLAYER1_SYMBOL
        else:
            return SHIP_PLAYER2_SYMBOL
    else:
        return TEXT_TO_SYMBOL[text]

# game map loaded to string
def load_map(path='output/map.txt'):
    with open(path, "r") as map_file:
        game_map = map_file.read()
        return game_map


# game state loaded to dictionary
def load_state(path='output/state.json'):
    with open(path, "r") as state_file:
        game_state = json.loads(state_file.read())
        return game_state


# writes the move to file
def write_move(move, path='output/move.txt'):
    move_file = open(path, 'w')
    move_file.write(move + '\r\n')
    move_file.close()


# loads relative harness files for testing purposes
def load_relative_harness_file(current_file, round_number):
    if not round_number >= 0 and round_number <= 200:
        return
    file_to_load = os.path.dirname(os.path.dirname(current_file))
    file_to_load = os.path.join(file_to_load, str(round_number).zfill(3), 'state.json')
    if os.path.exists(file_to_load):
        return load_state(file_to_load)

def is_bbox_equal(bbox1, bbox2):
    return bbox1['top'] == bbox2['top'] and bbox1['right'] == bbox2['right'] and bbox1['bottom'] == bbox2['bottom'] and bbox1['left'] == bbox2['left']

def walk_harness_replay_dir(state_files, top, names):
    state_file = os.path.join(top, 'state.json')
    if os.path.exists(state_file):
        state_files.append(state_file)

# expects top level replay directory c:\Users\leonard\entelect\Replays\0001
# or replay file  c:\Users\leonard\entelect\Replays\0001\001\state.json
def load_harness_replay_states(filename, replaytype='file'):
    if replaytype == 'dir':
        directory = filename
    elif replaytype == 'file':
        directory = os.path.dirname(os.path.dirname(filename))
    else:
        raise Exception('Unknown replay type %s' % replaytype)
    state_files = []
    os.path.walk(directory, walk_harness_replay_dir, state_files)
    states = []
    for state_file in state_files:
        states.append(load_state(state_file))
    return states

def save_obj(key, value):
    out = open(os.path.join(tempfile.gettempdir(), key), 'wb')
    pickle.dump(value, out)
    out.close()

def load_obj(key):
    filename = os.path.join(tempfile.gettempdir(), key)
    if not os.path.exists(filename):
        return None
    return pickle.load(open(os.path.join(tempfile.gettempdir(), key), 'rb'))

def remove_obj(key):
    filename = os.path.join(tempfile.gettempdir(), key)
    if os.path.exists(filename):
        os.remove(filename)

def print_predicted_states(state, limit=200):
    print state
    next_state = state.clone()
    while limit > 0 and next_state.lives >= 0 and next_state.round_number < state.round_limit:
        next_state.update(NOTHING, True, state.round_number)
        print next_state
        next_state = next_state.clone()
        limit -= 1
