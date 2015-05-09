import sys
from ai.entelect import *
from ai.strategy import *
from copy import *

def evaluate_discontentment(state):
    result = 0
    result -= state.lives
    result -= state.kills
    result -= len(state.shields)
    result += len(state.aliens)
    if state.ship:
        result -= 1000
    return result

class Model:
    def __init__(self, state):
        self.state = state
        self.actions = state.get_available_actions()
        self.action_idx = 0

    def get_next_action(self):
        if self.action_idx >= len(self.actions):
            return None
        next_action = self.actions[self.action_idx]
        self.action_idx += 1
        return next_action

    def apply_action(self, action):
        self.state.update(action)
        self.actions = self.state.get_available_actions()
        self.action_idx = 0

    def clone(self):
        return deepcopy(self)

def plan_action(state, max_depth):
    models = [None] * (max_depth + 1)
    actions = [None] * max_depth

    models[0] = Model(state)
    current_depth = 0

    best_action = None
    best_value = sys.maxint

    while current_depth >= 0:
        current_value = evaluate_discontentment(models[current_depth].state)
        if current_depth >= max_depth:
            if current_value < best_value:
                best_value = current_value
                best_action = actions[0]
            current_depth -= 1
            continue

        next_action = models[current_depth].get_next_action()
        if next_action:
            models[current_depth + 1] = models[current_depth].clone()
            actions[current_depth] = next_action
            models[current_depth + 1].apply_action(next_action)
            current_depth += 1
        else:
            current_depth -= 1
    return best_action