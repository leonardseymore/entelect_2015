import sys
import copy
from ai.entelect import *
from ai.strategy import *

def evaluate_state(state, include_tracers, loc):
    result = 0
    result += state.lives * 5
    result += state.extremity_kills * 3
    result += state.kills * 2
    if state.missile_controller:
        result += 10
    if state.alien_factory:
        result += 10
    result -= len(state.missiles)
    result -= state.alien_bbox['bottom']
    if state.ship:
        if include_tracers:
            if state.ship.get_shot_odds > 0:
                result -= 200
        result += 100
        if state.ship.x > 3 or state.ship.x < 11:
            result += 1000
        if loc:
            result -= abs(state.ship.x - loc)
    return result

def search_best_action(state, max_depth, include_tracers=False, loc=None):
    if DEBUG:
        print 'Starting state %s' % evaluate_state(state, include_tracers, loc)
        print state
    return search_best_action_recurse(state, state.round_number, max_depth, include_tracers, 0, [], loc)[1]

def search_best_action_recurse(state, starting_round, max_depth, include_tracers, current_depth, actions, loc):
    if state.lives < 0 or current_depth == max_depth:
        return evaluate_state(state, include_tracers, loc), None

    best_action = None
    best_score = -sys.maxint

    for i, action in enumerate(state.get_available_evade_actions()):
        new_state = state.clone()
        new_state.update(action, include_tracers, starting_round)
        actions.append(action)

        if DEBUG:
            print '-' * 19
            if new_state.ship:
                print 'ss', new_state.ship.get_shot_odds
            print evaluate_state(new_state, include_tracers, loc), ' -> '.join(actions)
            print new_state

        current_score, current_action = search_best_action_recurse(new_state, starting_round, max_depth, include_tracers, current_depth + 1, actions, loc)
        actions.pop()

        if not new_state.ship:
            return best_score, None

        if current_score > best_score:
            best_score = current_score
            best_action = action

    if DEBUG:
        print 'Best tree search action: ', current_depth + 1, best_score, best_action
    return best_score, best_action

#
# TRACER OPTIMISATION
#

def sim_kill_candidate(state, candidate):
    if not state.ship or state.round_number >= candidate.starting_round:
        return None

    next_state = state.clone()
    if len(state.missiles) < state.missile_limit and state.ship.x + 1 == candidate.starting_x and state.round_number == candidate.starting_round - 1:
        next_state.update(SHOOT)
        return next_state

    action = NOTHING
    if state.ship.x + 1 > candidate.starting_x:
        action = MOVE_LEFT
    elif state.ship.x + 1 < candidate.starting_x:
        action = MOVE_RIGHT

    next_state.update(action)
    return sim_kill_candidate(next_state, candidate)

def evaluate_kill(state):
    new_state = state.clone()
    while new_state.ship:
        new_state.update(NOTHING)
    return len(new_state.aliens)

def get_candidates(state, look_ahead=12):
    next_state = state.clone()
    for i in range(0, look_ahead):
        next_state.update(NOTHING, add_tracers=True, tracer_starting_round=state.round_number)
        # print next_state

    if len(next_state.tracer_hits) == 0:
        print 'No tracer hits found'
        return []

    # only choose to shoot 100% odd aliens
    candidates = filter(lambda t: t.reach_dest_odds == 1.0, next_state.tracer_hits)
    if len(candidates) == 0:
        print 'No tracer candidates found'
        return []

    print 'CANDIDATES', candidates
    return candidates

def search_best_candidate(state, max_depth):
    return search_best_candidate_recurse(state, 0, max_depth, [])[1]

def search_best_candidate_recurse(state, current_depth, max_depth, candidates):
    if current_depth == max_depth:
        return evaluate_kill(state), None

    best_candidate = None
    best_score = sys.maxint

    for i, candidate in enumerate(get_candidates(state)):
        new_state = sim_kill_candidate(state, candidate)
        if not new_state:
            continue
        candidates.append(candidate)

        if DEBUG:
            print '-' * 19
            if new_state:
                print evaluate_kill(new_state), ' -> ', candidates
            # print new_state

        current_score, current_candidate = search_best_candidate_recurse(new_state, current_depth + 1, max_depth, candidates)
        candidates.pop()

        if current_score < best_score:
            best_score = current_score
            best_candidate = candidate

    if DEBUG:
        print 'Best tree search candidate: ', current_depth + 1, best_score, best_candidate
    return best_score, best_candidate