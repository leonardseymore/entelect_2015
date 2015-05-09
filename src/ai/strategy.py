from ai.entelect import *
from ai.treesearch import *

#
# Blackboard
#

# blackboard to share game facts across different systems
class Blackboard():
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
# BEHAVIOR
#

# a task is an abstract node in a behavior tree
class Task():
    def __init__(self, *children):
        self.children = children

    # abstract method to be implemented
    def run(self, blackboard=None):
        return


# selector runs children until a child evals to true
class Selector(Task):
    def run(self, blackboard=None):
        for c in self.children:
            if c.run(blackboard):
                return True
        return False


# sequence runs children until a child evals to false
class Sequence(Task):
    def run(self, blackboard=None):
        for c in self.children:
            if not c.run(blackboard):
                return False
        return True


# decorator conditionally executes child
class Decorator(Task):
    def __init__(self, child):
        Task.__init__(self)
        self.child = child


# limit number of times task can be executed
class Limit(Decorator):
    def __init__(self, child, run_limit):
        Decorator.__init__(self, child)
        self.run_limit = run_limit
        self.run_so_far = 0

    def run(self, blackboard=None):
        if self.run_so_far >= self.run_limit:
            return False
        self.run_so_far += 1
        return self.child.run(blackboard)


# run a child task until it fails
class UntilFail(Decorator):
    def run(self, blackboard=None):
        while True:
            if not self.child.run(blackboard):
                break
        return True


# flip the return value of task
class Inverter(Decorator):
    def run(self, blackboard=None):
        return not self.child.run(blackboard)


# inject blackboard into child task
class BlackboardManager(Decorator):
    def run(self, blackboard=None):
        new_blackboard = Blackboard(blackboard)
        return self.child.run(new_blackboard)

# domain specific
class HasAlienFactory(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        return state.alien_factory is not None

class HasMissileController(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        return state.missile_controller is not None

class HasSpareLives(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        return state.lives > 0

class HasShip(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        return state.ship is not None

class SetSafestBuildingLocation(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        safe_locs = [1, PLAYING_FIELD_WIDTH - 4]
        closest = None
        for safe_loc in safe_locs:
            if state.check_open(safe_loc, PLAYING_FIELD_HEIGHT - 1, 3):
                if closest is None or abs(safe_loc - state.ship.x) < closest:
                    closest = safe_loc
        if closest:
            blackboard.set('safe_build_loc', closest)
            return True
        return False

class AtSafestBuildingLocation(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        safe_building_loc = blackboard.get('safe_build_loc')
        return state.ship.x == safe_building_loc

class MoveToSafestBuildingLocation(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        safe_building_loc = blackboard.get('safe_build_loc')
        if safe_building_loc < state.ship.x:
            blackboard.set('action', MOVE_LEFT)
        else:
            blackboard.set('action', MOVE_RIGHT)
        return True

class AtLocation(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        loc = blackboard.get('loc')
        return state.ship.x == loc

class SetLocation(Task):
    def __init__(self, loc, *children):
        Task.__init__(self, *children)
        self.loc = loc

    def run(self, blackboard):
        blackboard.set('loc', self.loc)
        return True

class MoveToLocation(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        if blackboard.get('loc') < state.ship.x:
            blackboard.set('action', MOVE_LEFT)
        else:
            blackboard.set('action', MOVE_RIGHT)
        return True

class SetLocationToMiddle(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        blackboard.set('loc', PLAYING_FIELD_WIDTH / 2 - 1)
        return True

class MoveAgainstAlienWave(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        if state.aliens_delta_x < 0:
            blackboard.set('action', MOVE_RIGHT)
        else:
            blackboard.set('action', MOVE_LEFT)
        return True

class MoveWithAlienWave(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        if state.aliens_delta_x > 0:
            blackboard.set('action', MOVE_RIGHT)
        else:
            blackboard.set('action', MOVE_LEFT)
        return True

class MoveToAlienWaveLeft(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        if state.aliens_delta_x > 0:
            blackboard.set('action', MOVE_RIGHT)
        else:
            blackboard.set('action', MOVE_LEFT)
        return True

class MoveAcrossBoard(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        ship_delta_x = load_obj('ship_delta_x')

        if not ship_delta_x:
            ship_delta_x = -1 * state.aliens_delta_x

        if state.ship.x < 4:
            ship_delta_x = 1
        elif state.ship.x > 10:
            ship_delta_x = -1

        save_obj('ship_delta_x', ship_delta_x)

        if ship_delta_x > 0:
            blackboard.set('action', MOVE_RIGHT)
        else:
            blackboard.set('action', MOVE_LEFT)
        return True

class IsMoveDangerous(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        next_state = state.clone()
        action = blackboard.get('action')
        next_state.update(action)
        for i in range(0, 3): # predict i gonna move into bad situation
            if next_state.lives < state.lives:
                print 'Bad idea to action %s' % action
                return True
            next_state.update(NOTHING)
        return False

class SetAction(Task):
    def __init__(self, action, *children):
        Task.__init__(self, *children)
        self.action = action

    def run(self, blackboard):
        blackboard.set('action', self.action)
        return True

class HasMissile(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        return len(state.missiles) < state.missile_limit

class IsStartingRound(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        return state.round_number == 0

class CanKill(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        next_state = state.clone()
        next_state.update(SHOOT)
        for i in range(0, 10): # predict missile up to spawn row
            next_state.update(NOTHING)
            if next_state.kills > state.kills + len(state.missiles):
                return True
        return False

class InDanger(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        next_state = state.clone()
        for i in range(0, 4): # predict if bullet or missile gonna kill me
            if next_state.lives < state.lives:
                return True
            next_state.update(NOTHING)
        return False

class AvoidDanger(Task):
    def run(self, blackboard):
        state = blackboard.get('state')

        best_option = None
        best_option_cost = -1
        for option in [NOTHING, MOVE_LEFT, MOVE_RIGHT, SHOOT]:
            next_state = state.clone()
            next_state.update(option)
            option_cost = 0
            for i in range(0, 3): # predict if bullet or missile gonna kill me if i move left
                if next_state.lives < state.lives:
                    continue
                option_cost += 1
            print 'i %d option_cost %d' % (i, option_cost)
            if best_option is None or best_option_cost > option_cost:
                best_option = option
                best_option_cost = option_cost
        print 'Avoid danger by: %s' % best_option
        blackboard.set('action', best_option)
        return True

class SearchBestAction(Task):
    def __init__(self, max_depth=3, *children):
        Task.__init__(self, *children)
        self.max_depth = max_depth

    def run(self, blackboard):
        state = blackboard.get('state')
        action = search_best_action(state, self.max_depth)
        if action:
            blackboard.set('action', action)
            return True
        else:
            return False
#
# EXPERTS
#

# expert base class
class Expert():
    def __init__(self):
        pass

    # modify blackboard as expert sees fit
    def run(self, blackboard):
        pass

class ExpertOptimizer(Expert):
    def run(self, blackboard):
        state = blackboard.get('state')
        actions = state.get_available_actions()
        if len(actions) > 2 and NOTHING in actions:
            actions.remove(NOTHING)
        blackboard.set('actions', actions)

# field_analyst = FieldAnalystExpert()
# alien_expert = AlienExpert()
# experts = {'field_analyst': field_analyst, 'alien': alien_expert}