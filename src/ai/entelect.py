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
import copy

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

MAP_WIDTH = 19
MAP_HEIGHT = 25

MAP_TOP = 1
MAP_RIGHT = 17
MAP_BOTTOM = 23
MAP_LEFT = 1

YOUR_SPAWN_LOCATION = (16, 13)
YOUR_SPAWN_THRESHOLD = (16, 15)

ENEMY_SPAWN_LOCATION = (16, 11)
ENEMY_SPAWN_THRESHOLD = (16, 9)

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

#
# EVENTS
#

# event base class
class Event():
    event_type = None
    payload = None

    # event_type and generic payload to avoid unnecessary base classes
    def __init__(self, event_type, payload=None):
        self.event_type = event_type
        self.payload = payload


# listeners where key = event_type
listeners = {}


# register object to handle event message of specified type
def register(event_type, obj):
    event_type_listeners = []
    if listeners.has_key(event_type):
        event_type_listeners = listeners[event_type]
    else:
        listeners[event_type] = event_type_listeners
    event_type_listeners.append(obj)


# unregister object from specified event type (None to remove from all)
def unregister(event_type, obj):
    if event_type:
        listeners[event_type].remove(obj)
    else:
        for key in listeners:
            listeners[key].remove(obj)


# dispatch event to interested listeners
def dispatch(event):
    for listener in listeners[event.event_type]:
        method = getattr(listener, 'handle_%s' % event.event_type)
        if method:
            method(event)
        else:
            listener.handle(event.event_type, event)

#
# Blackboard
#

# blackboard to share game facts across different systems
class Blackboard():
    # parent scope
    parent = None
    data = None

    def __init__(self, parent=None):
        self.parent = parent
        self.data = {}

    def set(self, key, value):
        self.data[key] = value

    # gets a value recursively up the blackboard hierarchy
    def get(self, key):
        if self.data.has_key(key):
            return self.data[key]
        elif self.parent:
            return self.parent.get(key)
        else:
            return None

    # gets entire shadowed tree
    def get_obj(self, tree=None):
        if not tree:
            tree = {}

        for key in self.data:
            if not tree.has_key(key):
                tree[key] = self.data[key]

        if self.parent:
            self.parent.get_obj(tree)

        return tree

#
# BEHAVIOR
#

# a task is an abstract node in a behavior tree
class Task():
    # child tasks
    children = []

    def __init__(self, *children):
        self.children = children

    # abstract method to be implemented
    def run(self, blackboard=None):
        return


# selector runs children until a child evals to true
class Selector(Task):
    def run(self, blackboard=None):
        for c in self.children:
            if c.run(blackboard):
                return True
        return False


# sequence runs children until a child evals to false
class Sequence(Task):
    def run(self, blackboard=None):
        for c in self.children:
            if not c.run(blackboard):
                return False
        return True


# decorator conditionally executes child
class Decorator(Task):
    child = None

    def __init__(self, child):
        Task.__init__(self)
        self.child = child


# limit number of times task can be executed
class Limit(Decorator):
    run_limit = 0
    run_so_far = 0

    def __init__(self, child, run_limit):
        Decorator.__init__(self, child)
        self.run_limit = run_limit

    def run(self, blackboard=None):
        if self.run_so_far >= self.run_limit:
            return False
        self.run_so_far += 1
        return self.child.run(blackboard)


# run a child task until it fails
class UntilFail(Decorator):
    def run(self, blackboard=None):
        while True:
            if not self.child.run(blackboard):
                break
        return True


# flip the return value of task
class Inverter(Decorator):
    def run(self, blackboard=None):
        return not self.child.run(blackboard)


# inject blackboard into child task
class BlackboardManager(Decorator):
    def run(self, blackboard=None):
        new_blackboard = Blackboard(blackboard)
        return self.child.run(new_blackboard)


#
# MOVEMENT
#

# move a bbox up, right, down, left
def move_bbox(bbox, direction):
    new_bbox = copy.copy(bbox)
    if direction == 'up':
        new_bbox['top'] -= 1
        new_bbox['bottom'] -= 1
    elif direction == 'right':
        new_bbox['left'] += 1
        new_bbox['right'] += 1
    elif direction == 'down':
        new_bbox['top'] += 1
        new_bbox['bottom'] += 1
    else: # left
        new_bbox['left'] -= 1
        new_bbox['right'] -= 1

    return new_bbox

# predicts bbox location for player context (your, enemy) up to time t
# time 0 being current game state
# results can be put in cache if supplied
def predict_bbox(blackboard, player_context, t):
    bbox = blackboard.get('%s_alien_bbox' % player_context)
    direction = blackboard.get('%s_alien_direction' % player_context)

    wave_size = blackboard.get('%s_alien_wave_size' % player_context)
    round_number = blackboard.get('round_number')

    spawn_location = YOUR_SPAWN_LOCATION if player_context == 'enemy' else ENEMY_SPAWN_LOCATION
    spawn_threshold = YOUR_SPAWN_THRESHOLD if player_context == 'enemy' else ENEMY_SPAWN_THRESHOLD

    new_bbox = copy.copy(bbox)
    results = []
    results.append(new_bbox)
    for i in range(0, t):
        if (player_context == 'enemy' and new_bbox['left'] == MAP_LEFT and new_bbox['bottom'] == MAP_BOTTOM) or (player_context == 'your' and new_bbox['left'] == MAP_LEFT and new_bbox['top'] == MAP_TOP):
            continue

        if round_number == TIME_WAVE_SIZE_INCREASE:
            wave_size += 1

        if direction == 'left':
            if new_bbox['left'] == MAP_LEFT:
                direction = 'right'
                move_direction = 'down' if player_context == 'enemy' else 'up'
            else:
                direction = 'left'
                move_direction = 'left'
                check_y = 'top' if player_context == 'enemy' else 'bottom'
                set_y = 'bottom' if player_context == 'your' else 'top'
                if (new_bbox['right'], new_bbox[check_y]) == spawn_threshold:
                    new_bbox[set_y] = spawn_location[1]
                    new_bbox['left'] = spawn_location[0] - wave_size_to_bbox_width(wave_size) + 1

        else: # right
            if new_bbox['right'] == MAP_RIGHT:
                direction = 'left'
                move_direction = 'down' if player_context == 'enemy' else 'up'
            else:
                direction = 'right'
                move_direction = 'right'
        new_bbox = move_bbox(new_bbox, move_direction)
        results.append(new_bbox)

        round_number += 1
    return results

#
# EXPERTS
#

# expert base class
class Expert():
    name = None

    def __init__(self, name):
        self.name = name

    # modify blackboard as expert sees fit
    def run(self, blackboard):
        pass

# analyses game state and gets most important information
class FieldAnalystExpert(Expert):
    def __init__(self):
        Expert.__init__(self, 'Field Analyst Expert')

    def run(self, blackboard):
        game_state = blackboard.get('game_state')
        # basic props
        blackboard.set('round_number', game_state['RoundNumber'])
        blackboard.set('round_limit', game_state['RoundLimit'])
        blackboard.set('rounds_remaining', game_state['RoundLimit'] - game_state['RoundNumber'])
        self.set_player_info(game_state, blackboard, 0)
        self.set_player_info(game_state, blackboard, 1)


    def set_player_info(self, game_state, blackboard, player_index):
        player_context = 'your' if player_index == 0 else 'enemy'
        player = game_state['Players'][player_index]

        blackboard.set('%s_lives' % player_context, player['Lives'])
        blackboard.set('%s_kills' % player_context, player['Kills'])
        blackboard.set('%s_alien_wave_size' % player_context, player['AlienWaveSize'])
        blackboard.set('%s_missile_limit' % player_context, player['MissileLimit'])
        blackboard.set('%s_respawn_timer' % player_context, player['RespawnTimer'])
        blackboard.set('%s_respawn_timer' % player_context, player['RespawnTimer'])

        alien_manager = player['AlienManager']
        blackboard.set('%s_alien_direction' % player_context, 'left' if alien_manager['DeltaX'] == -1 else 'right')
        blackboard.set('%s_alien_shot_energy_cost' % player_context, alien_manager['ShotEnergyCost'])
        blackboard.set('%s_alien_shot_energy' % player_context, alien_manager['ShotEnergy'])

        # nullable object
        ship = player['Ship']
        if ship:
            blackboard.set('%s_ship' % player_context, {'X': ship['X'], 'Y': ship['Y']})
        else:
            blackboard.set('%s_ship' % player_context, None)

        alien_factory = player['AlienFactory']
        blackboard.set('%s_alien_factory_built' % player_context, alien_factory is not None)
        if alien_factory:
            blackboard.set('%s_alien_factory_pos' % player_context, {'X': alien_factory['X'], 'Y': alien_factory['Y']})
        else:
            blackboard.set('%s_alien_factory_pos' % player_context, None)

        game_map = game_state['Map']
        # complex entries

        alien_bbox = {'top': -1, 'right': -1, 'bottom': -1, 'left': -1}
        if game_state['RoundNumber'] == 0:
            if player_context == 'enemy':
                alien_bbox['top'] = YOUR_SPAWN_LOCATION[1]
                alien_bbox['right'] = MAP_RIGHT
                alien_bbox['bottom'] = YOUR_SPAWN_LOCATION[1]
                alien_bbox['left'] = MAP_RIGHT - wave_size_to_bbox_width(INITIAL_ALIEN_WAVE_SIZE) + 1
            else:
                alien_bbox['top'] = ENEMY_SPAWN_LOCATION[1]
                alien_bbox['right'] = MAP_RIGHT
                alien_bbox['bottom'] = ENEMY_SPAWN_LOCATION[1]
                alien_bbox['left'] = MAP_RIGHT - wave_size_to_bbox_width(INITIAL_ALIEN_WAVE_SIZE) + 1
        else:
            start_row = 0 if player_index == 0 else MAP_HEIGHT / 2
            end_row = MAP_HEIGHT / 2 if player_index == 0 else MAP_HEIGHT
            for row_index in range(start_row, end_row):
                for column_index in range(0, MAP_WIDTH):
                    cell = game_map['Rows'][row_index][column_index]
                    if not cell:
                        continue

                    if cell['Type'] == ALIEN:
                        if alien_bbox['top'] == -1:
                            alien_bbox['top'] = row_index
                        if alien_bbox['bottom'] == -1 or alien_bbox['bottom'] < row_index:
                            alien_bbox['bottom'] = row_index
                        if alien_bbox['left'] == -1 or alien_bbox['left'] > column_index:
                            alien_bbox['left'] = column_index
                        if alien_bbox['right'] == -1 or alien_bbox['right'] < column_index:
                            alien_bbox['right'] = column_index
        blackboard.set('%s_alien_bbox' % player_context, alien_bbox)

# expert in alien movement prediction
# depends on Field Analyst Expert
class AlienExpert(Expert):
    def __init__(self):
        Expert.__init__(self, 'Alien Expert')

    def run(self, blackboard):
        blackboard.set('your_bbox_predictions', predict_bbox(blackboard, 'your', blackboard.get('rounds_remaining')))
        blackboard.set('enemy_bbox_predictions', predict_bbox(blackboard, 'enemy', blackboard.get('rounds_remaining')))


field_analyst = FieldAnalystExpert()
alien_expert = AlienExpert()
experts = {'field_analyst': field_analyst, 'alien': alien_expert}