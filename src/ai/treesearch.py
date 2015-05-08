import sys
from ai.entelect import *
from ai.strategy import *

def evaluate_state(state):
    result = 0
    result += state.round_number
    result += state.kills
    if state.ship:
        result += 1000
    if state.alien_factory:
        result += 50
    if state.missile_controller:
        result += 10
    result += len(state.shields)
    return result

def search_best_move(blackboard, max_depth):
    state = blackboard.get('state')
    return search_best_action(state, max_depth)

def search_best_action(state, max_depth, current_depth=0):
    if state.lives < 0 or current_depth == max_depth:
        return evaluate_state(state), None

    best_action = NOTHING
    best_score = -sys.maxint - 1
    for i, action in enumerate(state.get_available_actions()):
        new_state = state.clone()
        new_state.update(action)

        if DEBUG:
            print '\t' * current_depth, i, action

        current_score, current_action = search_best_action(new_state, max_depth, current_depth + 1)

        if current_score > best_score:
            best_score = current_score
            best_action = action

    if DEBUG:
        print '-' * current_depth, best_score, best_action
    return best_score, best_action