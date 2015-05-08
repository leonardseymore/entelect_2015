from ai.entelect import *

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

class SafeToFire(Task):
    def run(self, blackboard):
        state = blackboard.get('state')
        return len(state.missiles) < state.missile_limit

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