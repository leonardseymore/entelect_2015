import json
from os.path import *

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
    file_to_load = dirname(dirname(current_file))
    file_to_load = join(file_to_load, str(round_number).zfill(3), 'state.json')
    if exists(file_to_load):
        return load_state(file_to_load)