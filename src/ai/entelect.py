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
# MOVEMENT
#

# predicts states up to time t from current state
def predict_states(state, t):
    results = [state]
    for i in range(1, t):
        state = next_state(state)
        if state:
            results.append(state)
        else:
            break
    return results

def get_bbox(aliens):
    bbox = {'top': -1, 'right': -1, 'bottom': -1, 'left': -1}
    for alien in aliens:
        x = alien['x']
        y = alien['y']
        if bbox['top'] == -1 or y < bbox['top']:
            bbox['top'] = y
        if bbox['bottom'] == -1 or y > bbox['bottom']:
            bbox['bottom'] = y
        if bbox['left'] == -1 or x < bbox['left']:
            bbox['left'] = x
        if bbox['right'] == -1 or x > bbox['right']:
            bbox['right'] = x
    return bbox

def clone_collection(collection, playing_field, state):
    new_collection = []

    for entity in collection:
        cloned_entity = copy.copy(entity)
        new_collection.append(cloned_entity)
        cloned_entity['collection'] = new_collection
        cloned_entity['playing_field'] = playing_field
        cloned_entity['state'] = state

        for i in range(cloned_entity['x'], cloned_entity['x'] + cloned_entity['width']):
            playing_field[cloned_entity['y']][cloned_entity['x']] = cloned_entity
    return new_collection

def clone_entity(entity, playing_field, state):
    if not entity:
        return None

    cloned_entity = copy.copy(entity)
    cloned_entity['playing_field'] = playing_field
    cloned_entity['state'] = state

    for i in range(cloned_entity['x'], cloned_entity['x'] + cloned_entity['width']):
        playing_field[cloned_entity['y']][i] = cloned_entity
    return cloned_entity

def new_entity(x, y, type, width, playing_field, collection, state, player_number):
    for i in range(x, x + width):
        entity_at = playing_field[y][i]
        if entity_at:
            raise Exception('Trying place entity [%s] on occupied space [%s (%d:%d)]' % (type, entity_at['type'], x, y))
    entity = {
        'x': x,
        'y': y,
        'type': type,
        'width': width,
        'playing_field': playing_field,
        'collection': collection,
        'state': state,
        'player_number': player_number
    }
    for i in range(x, x + width):
        playing_field[y][i] = entity
    if collection:
        collection.append(entity)

    entity['destroy'] = lambda this = entity: destroy_entity(this)
    return entity

def print_state(state):
    playing_field = state['playing_field']
    text = ''
    for x in range(0, PLAYING_FIELD_WIDTH + 2):
        text += '+'
    text += '\n'
    for y in range(0, PLAYING_FIELD_HEIGHT):
        text += '+'
        for x in range(0, PLAYING_FIELD_WIDTH):
            entity = playing_field[y][x]
            text += entity_to_symbol(playing_field[y][x])
        text += '+\n'
    for x in range(0, PLAYING_FIELD_WIDTH + 2):
        text += '+'
    text += '\n'
    print text


# Update the alien commander to spawn new aliens and give aliens orders
# Update missiles, moving them forward
# Update alien bullets, moving them forward
# Update aliens, executing their move & shoot orders
# Update ships, executing their orders
# Advance respawn timer and respawn ships if necessary.
def next_state(state, action=None):
    new_state = {}
    # basic
    round_number = state['round_number']
    kills = state['kills']
    lives = state['lives']
    missile_limit = state['missile_limit']
    respawn_timer = state['respawn_timer']
    direction = state['enemy_alien_direction']
    wave_size = state['enemy_alien_wave_size']
    # entities
    ship = state['ship']
    alien_factory = state['alien_factory']
    missile_controller = state['missile_controller']
    # collections
    shields = state['shields']
    missiles = state['missiles']
    aliens = state['aliens']
    bullets = state['bullets']
    buildings = state['buildings']
    playing_field = state['playing_field']
    # new collections
    new_state['lives'] = lives
    new_playing_field = [[None for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]
    new_shields = clone_collection(shields, new_playing_field, new_state)
    new_missiles = clone_collection(missiles, new_playing_field, new_state)
    new_aliens = clone_collection(aliens, new_playing_field, new_state)
    new_bullets = clone_collection(bullets, new_playing_field, new_state)
    new_buildings = clone_collection(buildings, new_playing_field, new_state)
    new_ship = clone_entity(ship, new_playing_field, new_state)
    new_alien_factory = clone_entity(alien_factory, new_playing_field, new_state)
    new_missile_controller = clone_entity(missile_controller, new_playing_field, new_state)

    new_state['ship'] = new_ship
    new_state['alien_factory'] = new_alien_factory
    new_state['missile_controller'] = new_missile_controller

    if round_number == TIME_WAVE_SIZE_INCREASE:
        wave_size += 1
    if respawn_timer > -1:
        respawn_timer -= 1

    # Update the alien commander to spawn new aliens and give aliens orders
    bbox = get_bbox(aliens)
    spawn_x = 16
    spawn_y = 1
    if (bbox['right'], bbox['top']) == (spawn_x, spawn_y):
        for i in range(0, wave_size):
            entity_x = spawn_x - (i * 3)
            entity_y = spawn_y
            entity = new_playing_field[entity_y][entity_x]
            if entity:
                entity['destroy']()
            else:
                new_entity(x, y, ALIEN, 1, new_playing_field, new_aliens, new_state, 2)

    # TODO: also remove out of bound items
    # Update missiles, moving them forward
    for missile in new_missiles[:]:
        missile['y'] += missile['direction']
        entity = new_playing_field[missile['y']][missile['x']]
        if entity:
            entity['destroy']()
            new_missiles.remove(missile)
            if entity['type'] == ALIEN:
                kills += 1

    # Update alien bullets, moving them forward
    for bullet in new_bullets[:]:
        bullet['y'] += 1
        entity = new_playing_field[bullet['y']][bullet['x']]
        if entity:
            entity['destroy']()
            new_bullets.remove(bullet)

    # Update aliens, executing their move & shoot orders
    bbox = get_bbox(new_aliens)
    move_direction = None
    if direction == -1:
        if bbox['left'] == 0:
            direction = 1
            move_direction = 'down'
        else:
            move_direction = 'left'
    else: # right
        if bbox['right'] == PLAYING_FIELD_WIDTH:
            direction = -1
            move_direction = 'down'
        else:
            move_direction = 'right'

    for alien in aliens:
        if move_direction == 'left':
            alien['x'] -= 1
        elif move_direction == 'right':
            alien['x'] += 1
        elif move_direction == 'down':
            alien['y'] += 1

        entity = new_playing_field[alien['y']][alien['x']]
        if entity:
            entity['destroy']()
            new_aliens.remove(alien)
            if entity['type'] == SHIELD:
                for y in range(entity['y'] - 1, entity['y'] + 2):
                    for x in range(entity['x'] - 1, entity['x'] + 2):
                        collateral = new_playing_field[y][x]
                        collateral['destroy']()

    # check if game over
    new_lives = new_state['lives']
    if new_lives < 0:
        return None

    # Update ships, executing their orders
    if ship:
        if action == MOVE_LEFT:
            if ship['x'] == 0:
                raise Exception('Out of bounds')
            else:
                ship['x'] -= 1
        elif action == MOVE_RIGHT:
            if ship['x'] > PLAYING_FIELD_WIDTH - 1:
                raise Exception('Out of bounds')
            else:
                ship['x'] += 1
        elif action == SHOOT:
            if missile_limit >= sum(missile.player_number == 1 for missile in new_missiles):
                raise Exception('Out of missiles')
            else:
                new_entity(ship['x'] + 1, ship['y'] - 1, MISSILE, 1, new_playing_field, None, new_state, 1)
        elif action == BUILD_ALIEN_FACTORY or action == BUILD_MISSILE_CONTROLLER or action == BUILD_SHIELD:
            if new_lives == 0:
                raise Exception('No lives left for building')
            if action == BUILD_ALIEN_FACTORY:
                if alien_factory:
                    raise Exception('Alien factory already built')
                else:
                    alien_factory = new_entity(ship['x'], ship['y'] + 1, ALIEN_FACTORY, 3, new_playing_field, new_buildings, new_state, 1)
            elif action == BUILD_MISSILE_CONTROLLER:
                if missile_controller:
                    raise Exception('Missile controller already built')
                else:
                    missile_controller = new_entity(ship['x'], ship['y'] + 1, MISSILE_CONTROLLER, 3, new_playing_field, new_buildings, new_state, 1)
            elif action == BUILD_SHIELD:
                for y in range(6, 10):
                    for x in range(ship['x'], ship['width']):
                        entity = new_playing_field[y][x]
                        if entity:
                            if not entity['type'] == SHIELD:
                                entity['destroy']()
                        else:
                            new_entity(x, y, SHIELD, 1, new_playing_field, new_shields, new_state, 1)

    # Advance respawn timer and respawn ships if necessary.
    if respawn_timer > -1:
        respawn_timer -= 1
        if respawn_timer == -1:
            ship_x = 8
            ship_y = PLAYING_FIELD_HEIGHT - 2
            entity = new_playing_field[ship_y][ship_x]
            if entity:
                entity['destroy']()
                respawn_timer = 2
            else:
                ship = new_entity(ship_x, ship_y, SHIP, 3, new_playing_field, None, new_state)

    # check if game over
    new_lives = new_state['lives']
    if new_lives < 0:
        return None

    # update state
    round_number += 1
    new_state['round_number'] = round_number
    new_state['lives'] = new_lives
    new_state['kills'] = kills
    new_state['missile_limit'] = missile_limit
    new_state['respawn_timer'] = respawn_timer
    new_state['enemy_alien_direction'] = direction
    new_state['enemy_alien_wave_size'] = wave_size
    # collections
    new_state['shields'] = new_shields
    new_state['missiles'] = new_missiles
    new_state['aliens'] = new_aliens
    new_state['bullets'] = new_bullets
    new_state['buildings'] = new_buildings
    new_state['playing_field'] = new_playing_field

    return new_state
#
# SEARCH
#
class Node():
    blackboard = None

    def __init__(self, blackboard):
        self.blackboard = blackboard

    # def get_children(self):



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

# clean up collections and playing field when an entity is destroyed
def destroy_entity(entity):
    print 'Destroying [%s] at [%d:%d]' % (entity['type'], entity['x'], entity['y'])
    collection = entity.get('collection')
    if collection:
        collection.remove(entity)
    for i in range(entity['x'], entity['x'] + entity['width']):
        entity['playing_field'][entity['y']][i] = None

    state = entity['state']
    if entity['type'] == SHIP:
        state['lives'] -= 1
        state['respawn_timer'] = 3
        state['ship'] = None
    elif entity['type'] == ALIEN_FACTORY:
        state['alien_factory'] = None
    elif entity['type'] == MISSILE_CONTROLLER:
        state['missile_limit'] = 1
        state['missile_controller'] = None

# analyses game state and gets most important information
class FieldAnalystExpert(Expert):
    def __init__(self):
        Expert.__init__(self, 'Field Analyst Expert')

    def run(self, blackboard):
        game_state = blackboard.get('game_state')
        # basic props
        state = {}
        state['round_number'] = game_state['RoundNumber']
        state['round_limit'] = game_state['RoundLimit']
        you = game_state['Players'][0]
        state['missile_limit'] = you['MissileLimit']
        state['respawn_timer'] = you['RespawnTimer']
        state['kills'] = you['Kills']
        state['lives'] = you['Lives']
        enemy = game_state['Players'][1]
        state['enemy_alien_wave_size'] = enemy['AlienWaveSize']
        enemy_alien_man = enemy['AlienManager']
        state['enemy_alien_direction'] = enemy_alien_man['DeltaX']

        game_map = game_state['Map']
        playing_field = [[None for x in range(MAP_WIDTH)] for y in range(MAP_HEIGHT)]
        aliens = []
        missiles = []
        bullets = []
        shields = []
        buildings = []
        alien_factory = None
        missile_controller = None
        ship = None
        for row_index in range(YOUR_PLAYING_START[1], YOUR_PLAYING_END[1]):
            for column_index in range(YOUR_PLAYING_START[0], YOUR_PLAYING_END[0]):
                cell = game_map['Rows'][row_index][column_index]
                if not cell:
                    continue

                player_number = cell['PlayerNumber']
                x = cell['X'] - YOUR_PLAYING_START[0]
                y = cell['Y'] - YOUR_PLAYING_START[1]

                if cell['X'] == column_index and cell['Y'] == row_index:
                    entity = new_entity(x, y, cell['Type'], cell['Width'], playing_field, None, state, player_number)

                collection = None
                if cell['Type'] == ALIEN:
                    collection = aliens
                if cell['Type'] == MISSILE:
                    collection = missiles
                    entity['direction'] = -1 if player_number == 1 else 1
                elif cell['Type'] == BULLET:
                    collection = bullets
                elif cell['Type'] == ALIEN_FACTORY or cell['Type'] == MISSILE_CONTROLLER:
                    if cell['X'] == column_index and cell['Y'] == row_index:
                        collection = buildings
                        if cell['Type'] == ALIEN_FACTORY:
                            alien_factory = entity
                        else:
                            missile_controller = entity
                elif cell['Type'] == SHIELD:
                    collection = shields
                elif cell['Type'] == SHIP:
                    if cell['X'] == column_index and cell['Y'] == row_index:
                        if player_number == 1:
                            ship = entity
                if entity and collection is not None:
                    entity['collection'] = collection
                    collection.append(entity)

        state['aliens'] = aliens
        state['missiles'] = missiles
        state['bullets'] = bullets
        state['shields'] = shields
        state['buildings'] = buildings
        state['alien_factory'] = alien_factory
        state['missile_controller'] = missile_controller
        state['ship'] = ship
        state['playing_field'] = playing_field
        blackboard.set('state', state)

# expert in alien movement prediction
# depends on Field Analyst Expert
class AlienExpert(Expert):
    def __init__(self):
        Expert.__init__(self, 'Alien Expert')

    def run(self, blackboard):
        blackboard.set('predictions', predict_states(blackboard.get_obj(), blackboard.get('rounds_remaining')))


field_analyst = FieldAnalystExpert()
alien_expert = AlienExpert()
experts = {'field_analyst': field_analyst, 'alien': alien_expert}