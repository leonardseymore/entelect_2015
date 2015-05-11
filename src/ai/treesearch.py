import sys
from ai.entelect import *
from ai.strategy import *

DEBUG_TREE_SEARCH = False

def evaluate_state(state):
    result = 0
    result += state.lives * 2
    result += state.kills
    result += len(state.missiles)
    if state.ship:
        result += 100
    return result

def search_best_action(state, max_depth):
    return search_best_action_recurse(state, max_depth)[1]

def search_best_action_recurse(state, max_depth, current_depth=0):
    if state.lives < 0 or current_depth == max_depth:
        return evaluate_state(state), None

    best_action = None
    best_score = -sys.maxint

    for i, action in enumerate(state.get_available_evade_actions()):
        new_state = state.clone()
        new_state.update(action)

        if DEBUG_TREE_SEARCH:
            print '\t' * current_depth, i, action

        current_score, current_action = search_best_action_recurse(new_state, max_depth, current_depth + 1)

        if current_score > best_score:
            best_score = current_score
            best_action = action

    if DEBUG_TREE_SEARCH:
        print '\t' * current_depth, best_score, best_action
    return best_score, best_action