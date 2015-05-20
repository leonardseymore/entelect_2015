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
        if key in self.data:
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
            if key not in tree:
                tree[key] = self.data[key]

        if self.parent:
            self.parent.get_obj(tree)

        return tree

    def __str__(self):
        return '%s' % self.get_obj()

#
# BEHAVIOR
#

# a task is an abstract node in a behavior tree
class Task():
    def __init__(self, *children):
        self.children = children

    # abstract method to be implemented
    def run(self, blackboard=None):
        if DEBUG:
            print self
        return

    def __str__(self):
        return self.__class__.__name__


# selector runs children until a child evals to true
class Selector(Task):
    def run(self, blackboard=None):
        Task.run(self, blackboard)
        for c in self.children:
            if c.run(blackboard):
                return True
        return False

    def __str__(self):
        return '?'


# sequence runs children until a child evals to false
class Sequence(Task):
    def run(self, blackboard=None):
        Task.run(self, blackboard)
        for c in self.children:
            if not c.run(blackboard):
                return False
        return True

    def __str__(self):
        return '->'


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
        Task.run(self, blackboard)
        if self.run_so_far >= self.run_limit:
            return False
        self.run_so_far += 1
        return self.child.run(blackboard)


# flip the return value of task
class Inverter(Decorator):
    def run(self, blackboard=None):
        Task.run(self, blackboard)
        return not self.child.run(blackboard)

    def __str__(self):
        return '~'

class AlwaysTrue(Decorator):
    def run(self, blackboard=None):
        Task.run(self, blackboard)
        self.child.run(blackboard)
        return True

# inject blackboard into child task
class BlackboardManager(Decorator):
    def run(self, blackboard=None):
        Task.run(self, blackboard)
        new_blackboard = Blackboard(blackboard)
        return self.child.run(new_blackboard)

# domain specific
class HasAlienFactory(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.alien_factory is not None

class HasMissileController(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.missile_controller is not None

class HasSpareLives(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.lives > 0

class HasShip(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.ship is not None

class FirstWaveKilled(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.kills >= 3

# this is only true at the beginning of the game
class SetSafestBuildingLocation(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        if state.player_number_real == 2:
            safe_locs = [1, PLAYING_FIELD_WIDTH - 4]
        else:
            safe_locs = [PLAYING_FIELD_WIDTH - 4, 1]
        closest = None
        for safe_loc in safe_locs:
            if state.check_open(safe_loc, PLAYING_FIELD_HEIGHT - 1, 3):
                if closest is None:
                    closest = safe_loc
        if closest:
            blackboard.set('loc', closest)
            return True
        return False

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
    def __init__(self, loc=None, *children):
        Task.__init__(self, *children)
        self.loc = loc

    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        loc = self.loc
        if not loc:
            loc = blackboard.get('loc')
        if loc < state.ship.x:
            blackboard.set('action', MOVE_LEFT)
        elif loc > state.ship.x:
            blackboard.set('action', MOVE_RIGHT)
        else:
            return True
        return False

    def __str__(self):
        return 'MoveToLocation(%s)' % self.loc

class IsMoveDangerous(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        next_state = state.clone()
        action = blackboard.get('action')
        next_state.update(action)
        for i in range(0, 3): # predict i gonna move into bad situation
            if not next_state.ship or next_state.lives < state.lives:
                print 'Dangerous action %s' % action
                return True
            next_state.update(NOTHING)
        return False

class SetAction(Task):
    def __init__(self, action, *children):
        Task.__init__(self, *children)
        self.action = action

    def run(self, blackboard):
        Task.run(self, blackboard)
        blackboard.set('action', self.action)
        return True

class HasMissile(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return len(state.missiles) < state.missile_limit

class IsStartingRound(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.round_number == 0

class Kill(Task):
    def run(self, blackboard=None):
        Task.run(self, blackboard)
        return Sequence(
            Selector(
                IsStartingRound(),
                CanKill()
            ),
            HasMissile(),
            SetAction(SHOOT)
        ).run(blackboard)


class CanKill(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        next_state = state.clone()
        next_state.update(SHOOT)
        for i in range(0, 10): # predict missile up to spawn row
            next_state.update(NOTHING)
            if next_state.kills > state.kills + len(state.missiles):
                blackboard.set('kill_cost', i)
                return True
        return False

class CanShootBullet(Task):
    def __init__(self, dist=3, *children):
        Task.__init__(self, *children)
        self.dist = dist

    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        x = state.ship.x + 1
        for y in range(state.ship.y - self.dist, state.ship.y):
            entity = state.get_entity(x, y)
            if entity and entity.entity_type == BULLET:
                return True
        return False

class KillExtremity(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        next_state = state.clone()
        next_state.update(SHOOT)
        for i in range(0, 10): # predict missile up to spawn row
            next_state.update(NOTHING)
            if next_state.extremity_kills > state.extremity_kills + len(state.missiles):
                blackboard.set('kill_cost', i)
                return True
        return False

class KillFrontLine(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        next_state = state.clone()
        next_state.update(NOTHING, add_tracers=True, tracer_starting_round=state.round_number)
        for i in range(0, 20):
            for tracer_hit in next_state.tracer_hits:
                pass
            next_state.update(NOTHING, add_tracers=True, tracer_starting_round=state.round_number)
        return False

class AtRound(Task):
    def __init__(self, round_number, *children):
        Task.__init__(self, *children)
        self.round_number = round_number

    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.round_number == self.round_number

    def __str__(self):
        return 'AtRound(%s)' % self.round_number

class WaitTillRound(Task):
    def __init__(self, round_number, *children):
        Task.__init__(self, *children)
        self.round_number = round_number

    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.round_number >= self.round_number

    def __str__(self):
        return 'WaitTillRound(%s)' % self.round_number

class SetTracer(Task):
    def __init__(self, *children):
        Task.__init__(self, *children)

    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        next_state = state.clone()
        for i in range(0, 10):
            next_state.update(NOTHING, add_tracers=True, tracer_starting_round=state.round_number)
            print next_state

        for t in next_state.tracer_hits:
            print '%s' % t

        if len(next_state.tracer_hits) == 0:
            print 'No tracer hits found'
            return False

        # only choose to shoot 100% odd aliens
        candidates = filter(lambda t: t.reach_dest_odds == 1.0, next_state.tracer_hits)
        if len(candidates) == 0:
            print 'No tracer candidates found'
            return False
        print 'CANDIDATES'
        candidates = sorted(candidates, key=lambda c: (abs(state.ship.x - t.starting_x) + t.energy))
        for candidate in candidates:
            print '%s' % candidate
        print state.ship



        tracer_hit = candidates[0]
        if not tracer_hit:
            return False
        blackboard.set('tracer', tracer_hit)
        return True

class KillTracerNoWait(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        if not SetTracer().run(blackboard):
            return False
        tracer = blackboard.get('tracer')
        return Sequence(
            HasMissile(),
            SetLocation(tracer.starting_x - 1),
            AtLocation(),
            AtRound(tracer.starting_round - 1),
            SetAction(SHOOT)
        ).run(blackboard)

class KillTracer(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        if not SetTracer().run(blackboard):
            return False
        tracer = blackboard.get('tracer')
        Sequence(
            MoveToLocation(tracer.starting_x - 1),
            WaitTillRound(tracer.starting_round - 1),
            HasMissile(),
            SetAction(SHOOT)
        ).run(blackboard)
        return True

class IsInvasionImminent(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        return state.alien_bbox['bottom'] > 7

class SetMoveToFrontLineAvg(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        total = 0
        count = 0
        next_state = state.clone()
        next_state.update(SHOOT)
        for i in range(0, 10): # predict missile up to spawn row
            next_state.update(NOTHING)
            for alien in next_state.aliens:
                if alien.at_front_line:
                    total += alien.x
                    count += 1
        avg = total / count
        blackboard.set('loc', avg - 1)
        return True


class InDanger(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        next_state = state.clone()
        for i in range(0, 4): # predict if bullet or missile gonna kill me
            if next_state.lives < state.lives:
                return True
            next_state.update(NOTHING)
        return False

class AvoidDanger(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
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
            if DEBUG:
                print 'i %d option_cost %d' % (i, option_cost)
            if best_option is None or best_option_cost > option_cost:
                best_option = option
                best_option_cost = option_cost
        if DEBUG:
            print 'Avoid danger by: %s' % best_option
        blackboard.set('action', best_option)
        return True

class SearchBestAction(Task):
    def __init__(self, max_depth=3, include_tracers=False, *children):
        Task.__init__(self, *children)
        self.max_depth = max_depth
        self.include_tracers = include_tracers

    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        action = search_best_action(state, self.max_depth, self.include_tracers)
        if action:
            blackboard.set('action', action)
            return True
        else:
            return False

class IsAlienTooClose(Task):
    def run(self, blackboard):
        Task.run(self, blackboard)
        state = blackboard.get('state')
        next_state = state.clone()
        next_state.update(NOTHING)
        # x  x  x         # -> delta_x = 1
        #                 #
        #    x  AAA       #
        # XXX         MMM #
        ###################
        if not next_state.ship:
            return True

        for x in range(next_state.ship.x - 1, next_state.ship.x + next_state.ship.width + 1):
            for y in [next_state.ship.y -1, next_state.ship.y - 2]:
                entity = next_state.get_entity(x, y)
                if entity and entity.entity_type == ALIEN:
                    print 'Alien too close!', entity
                    return True
        return False


strategies = [InDanger(), SearchBestAction(4), SearchBestAction(4, True), IsInvasionImminent(), IsAlienTooClose(),
              SetTracer()]