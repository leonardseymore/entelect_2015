"""
movement and targeting module
"""

import copy
from ai.entelect import *

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
    for i in range(0, t):
        if (player_context == 'enemy' and new_bbox['left'] == MAP_LEFT and new_bbox['bottom'] == MAP_BOTTOM) or (player_context == 'your' and new_bbox['left'] == MAP_LEFT and new_bbox['top'] == MAP_TOP):
            continue

        round_number += 1
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

    return results
