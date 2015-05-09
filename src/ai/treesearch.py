import sys
from ai.entelect import *
from ai.strategy import *

def evaluate_state(state):
    result = 0
    result += state.lives * 2
    result += state.kills
    result += len(state.shields)
    bbox = state.get_alien_bbox()
    result -= (abs(bbox['right'] - bbox['left']) * abs(bbox['top'] - bbox['bottom'])) * 10
    if state.ship:
        result += 10000
    if state.alien_factory:
        result += 50
    if state.missile_controller:
        result += 10
    if state.ship:
        result -= abs(state.ship.x - PLAYING_FIELD_WIDTH / 2 - 1)
    return result

def search_best_action(state, actions, max_depth):
    return search_best_action_recurse(state, actions, max_depth)[1]

def search_best_action_recurse(state, actions, max_depth, current_depth=0):
    if state.lives < 0 or current_depth == max_depth:
        return evaluate_state(state), None

    best_action = None
    best_score = -sys.maxint - 1
    available_actions = state.get_available_actions()
    supported_actions = []
    for a in available_actions:
        if a in actions:
            supported_actions.append(a)

    for i, action in enumerate(supported_actions):
        new_state = state.clone()
        new_state.update(action)

        if DEBUG:
            print '\t' * current_depth, i, action

        current_score, current_action = search_best_action_recurse(new_state, actions, max_depth, current_depth + 1)

        if current_score > best_score:
            best_score = current_score
            best_action = action

    if DEBUG:
        print '-' * current_depth, best_score, best_action
    return best_score, best_action