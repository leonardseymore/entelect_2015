import json

# game map loaded to string
def load_map(file = 'output/map.txt'):
	with open(file, "r") as map_file:
		game_map = map_file.read()

# game state loaded to dictionary
def load_state(file = 'output/map.txt'):
	with open('output/state.json', "r") as state_file:
		game_state = json.loads(state_file.read())
        
# writes the move to file
def write_move(move, file = 'output/move.txt'):
	move_file = open(file, 'w')
	move_file.write(move + '\r\n')
	move_file.close()