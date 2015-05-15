import sys
import copy
from ai.entelect import *
from ai.strategy import *

def evaluate_state(state):
    result = 0
    result += state.lives * 5
    if state.ship:
        result += 100
        if state.ship.x > 3 or state.ship.x < 11:
            result += 1000
    return result

def search_best_action(state, max_depth):
    return search_best_action_recurse(state, max_depth, 0, [])[1]

def search_best_action_recurse(state, max_depth, current_depth=0, actions=None):
    if state.lives < 0 or current_depth == max_depth:
        return evaluate_state(state), None

    best_action = None
    best_score = -sys.maxint

    for i, action in enumerate(state.get_available_evade_actions()):
        new_state = state.clone()
        new_state.update(action)
        actions.append(action)

        if DEBUG:
            print new_state
        if DEBUG:
            print 'D', current_depth + 1, 'E', evaluate_state(new_state), ' -> '.join(actions)

        current_score, current_action = search_best_action_recurse(new_state, max_depth, current_depth + 1, actions)
        actions.pop()

        if not new_state.ship:
            return best_score, None

        if current_score > best_score:
            best_score = current_score
            best_action = action

    if DEBUG:
        print 'Best tree search action: ', current_depth + 1, best_score, best_action
    return best_score, best_action