from ai.entelect import *
import logging
import sys


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

    def __repr__(self):
        return '%s' % self.get_obj()

#
# BEHAVIOR
#


# a task is an abstract node in a behavior tree
class Task():
    def __init__(self, *children):
        self.children = children
        self.logger = logging.getLogger('strategy.%s' % self.__class__.__name__)

    # abstract method to be implemented
    def run(self, blackboard, flow):
        flow.append(self)
        return

    def __repr__(self):
        return self.__class__.__name__


# selector runs children until a child evals to true
class Selector(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        for c in self.children:
            if c.run(blackboard, flow):
                return True
        return False

    def __repr__(self):
        return '?'


# sequence runs children until a child evals to false
class Sequence(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        for c in self.children:
            if not c.run(blackboard, flow):
                return False
        return True

    def __repr__(self):
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

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        if self.run_so_far >= self.run_limit:
            return False
        self.run_so_far += 1
        return self.child.run(blackboard)


# flip the return value of task
class Inverter(Decorator):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        return not self.child.run(blackboard, flow)

    def __repr__(self):
        return '~'


class AlwaysTrue(Decorator):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        self.child.run(blackboard, flow)
        return True


# inject blackboard into child task
class BlackboardManager(Decorator):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        new_blackboard = Blackboard(blackboard)
        return self.child.run(new_blackboard)


# domain specific
class HasAlienFactory(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.alien_factory is not None


class HasMissileController(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.missile_controller is not None


class HasSpareLives(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.lives > 0


class HasShip(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.ship is not None


class FirstWaveKilled(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.kills >= 3


# this is only true at the beginning of the game
class SetSafestBuildingLocation(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
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
    def run(self, blackboard, flow):
        state = blackboard.get('state')
        loc = blackboard.get('loc')
        return state.ship.x == loc


class SetLocation(Task):
    def __init__(self, loc, *children):
        Task.__init__(self, *children)
        self.loc = loc

    def run(self, blackboard, flow):
        blackboard.set('loc', self.loc)
        return True


class MoveToLocation(Task):
    def __init__(self, loc=None, *children):
        Task.__init__(self, *children)
        self.loc = loc

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
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

    def __repr__(self):
        return 'MoveToLocation(%s)' % self.loc


class IsMoveDangerous(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        action = blackboard.get('action')
        next_state.update(action)
        for i in range(0, 3):  # predict i gonna move into bad situation
            if not next_state.ship or next_state.lives < state.lives or next_state.ship.get_shot_odds > 0.0:
                self.logger.debug('Dangerous action %s', action)
                return True
            next_state.update(NOTHING)
        return False


class SetAction(Task):
    def __init__(self, action, *children):
        Task.__init__(self, *children)
        self.action = action

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        blackboard.set('action', self.action)
        return True


class HasMissile(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return len(state.missiles) < state.missile_limit


class IsStartingRound(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.round_number == 0


class Kill(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        return Sequence(
            Selector(
                IsStartingRound(),
                CanKill()
            ),
            HasMissile(),
            SetAction(SHOOT)
        ).run(blackboard)


class CanKill(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        next_state.update(SHOOT)
        for i in range(0, 10):  # predict missile up to spawn row
            next_state.update(NOTHING)
            if next_state.kills > state.kills + len(state.missiles):
                blackboard.set('kill_cost', i)
                return True
        return False


class CanShootBullet(Task):
    def __init__(self, dist=3, *children):
        Task.__init__(self, *children)
        self.dist = dist

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        x = state.ship.x + 1
        for y in range(state.ship.y - self.dist, state.ship.y):
            entity = state.get_entity(x, y)
            if entity and entity.entity_type == BULLET:
                return True
        return False


class KillExtremity(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        next_state.update(SHOOT)
        for i in range(0, 10):  # predict missile up to spawn row
            next_state.update(NOTHING)
            if next_state.extremity_kills > state.extremity_kills + len(state.missiles):
                blackboard.set('kill_cost', i)
                return True
        return False


class AtRound(Task):
    def __init__(self, round_number, *children):
        Task.__init__(self, *children)
        self.round_number = round_number

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.round_number == self.round_number

    def __repr__(self):
        return 'AtRound(%s)' % self.round_number


class WaitTillRound(Task):
    def __init__(self, round_number, *children):
        Task.__init__(self, *children)
        self.round_number = round_number

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.round_number >= self.round_number

    def __repr__(self):
        return 'WaitTillRound(%s)' % self.round_number


class SetTracer(Task):
    def __init__(self, *children):
        Task.__init__(self, *children)

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        for i in range(0, 12):
            next_state.update(NOTHING, add_tracers=True, tracer_starting_round=state.round_number)
            self.logger.debug('Next state\n%s', next_state)

        for t in next_state.tracer_hits:
            self.logger.debug('%s', t)

        if len(next_state.tracer_hits) == 0:
            self.logger.debug('No tracer hits found')
            return False

        # only choose to shoot 100% odd aliens
        candidates = filter(lambda tr: tr.get_shot_odds == 0.0, next_state.tracer_hits)
        if len(candidates) == 0:
            self.logger.debug('No tracer candidates found')
            return False
        candidates = sorted(candidates, key=lambda c: (abs(state.ship.x - t.starting_x) + t.energy))
        for candidate in candidates:
            self.logger.debug('Candidate %s', candidate)
        self.logger.debug('Ship %s', state.ship)

        tracer_hit = candidates[0]
        if not tracer_hit:
            return False
        blackboard.set('tracer', tracer_hit)
        return True


class KillTracerNoWait(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        if not SetTracer().run(blackboard, flow):
            return False
        tracer = blackboard.get('tracer')
        loc = tracer.starting_x - 1
        blackboard.set('loc', loc)
        return Sequence(
            HasMissile(),
            SetLocation(loc),
            AtLocation(),
            AtRound(tracer.starting_round - 1),
            SetAction(SHOOT)
        ).run(blackboard, flow)


class KillTracer(Task):
    def __init__(self, tracer=None, *children):
        Task.__init__(self, *children)
        self.tracer = tracer

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        if not self.tracer:
            if not SetTracer().run(blackboard, flow):
                return False
            tracer = blackboard.get('tracer')
        else:
            tracer = self.tracer
        loc = tracer.starting_x - 1
        blackboard.set('loc', loc)
        Sequence(
            MoveToLocation(loc),
            WaitTillRound(tracer.starting_round - 1),
            HasMissile(),
            SetAction(SHOOT)
        ).run(blackboard, flow)
        return True


class IsInvasionImminent(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.alien_bbox['bottom'] > 7


class SetMoveToFrontLineAvg(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        total = 0
        count = 0
        next_state = state.clone()
        next_state.update(SHOOT)
        for i in range(0, 10):  # predict missile up to spawn row
            next_state.update(NOTHING)
            for alien in next_state.aliens:
                if alien.at_front_line:
                    total += alien.x
                    count += 1
        avg = total / count
        blackboard.set('loc', avg - 1)
        return True


class InDanger(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        for i in range(0, 4):  # predict if bullet or missile gonna kill me
            if next_state.lives < state.lives or next_state.ship.get_shot_odds > 0.0:
                return True
            next_state.update(NOTHING)

        return False


class SearchBestAction(Task):
    def __init__(self, max_depth=3, include_tracers=False, include_loc=True, *children):
        Task.__init__(self, *children)
        self.max_depth = max_depth
        self.include_tracers = include_tracers
        self.include_loc = include_loc

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        loc = None
        if self.include_loc:
            loc = blackboard.get('loc')
        action = TREE_SEARCH.search(state, self.max_depth, self.include_tracers, loc)
        if action:
            blackboard.set('action', action)
            return True
        else:
            return False

    def __repr__(self):
        return 'SearchBestAction(include_tracers=%s, max_depth=%s)' % (self.include_tracers, self.max_depth)


class IsAlienTooClose(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
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
            for y in [next_state.ship.y - 1, next_state.ship.y - 2]:
                entity = next_state.get_entity(x, y)
                if entity and entity.entity_type == ALIEN:
                    self.logger.debug('Alien too close! %s', entity)
                    return True
        return False


class IsSoleSurvivor(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return len(state.aliens) == 1

strategies = [InDanger(), SearchBestAction(4), SearchBestAction(4, True), SearchBestAction(1, True),
              IsInvasionImminent(), IsAlienTooClose(), SetTracer(), IsMoveDangerous()]

class TreeSearchBestAction:
    def __init__(self):
        self.logger = logging.getLogger('search.TreeSearchBestAction')

    @staticmethod
    def evaluate(state, include_tracers, loc):
        result = 0
        result += state.lives * 5
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

    def search(self, state, max_depth, include_tracers=False, loc=None):
        self.logger.debug('Starting state %s\n%s', self.evaluate(state, include_tracers, loc), state)
        return self.search_recurse(state, state.round_number, max_depth, include_tracers, 0, [], loc)[1]

    def search_recurse(self, state, starting_round, max_depth, include_tracers, current_depth, actions, loc):
        if state.lives < 0 or current_depth == max_depth:
            return self.evaluate(state, include_tracers, loc), None

        best_action = None
        best_score = -sys.maxint

        for i, action in enumerate(state.get_available_evade_actions()):
            new_state = state.clone()
            new_state.update(action, include_tracers, starting_round)
            actions.append(action)

            self.logger.debug('\n%s %s\n%s', self.evaluate(new_state, include_tracers, loc),
                              ' -> '.join(actions), new_state)
            current_score, current_action = self.search_recurse(new_state, starting_round, max_depth, include_tracers,
                                                                current_depth + 1, actions, loc)
            actions.pop()

            if not new_state.ship:
                return best_score, None

            if current_score > best_score:
                best_score = current_score
                best_action = action

        self.logger.debug('Best tree search action: depth=%s score=%s action=%s',
                          current_depth + 1, best_score, best_action)
        return best_score, best_action


class MctsBestAction:
    def __init__(self):
        self.logger = logging.getLogger('search.MctsBestAction')

    def search(self, state): # TODO: timeout?
        self.simulate(state)

    def simulate(self, state):
        next_state = state.clone()

        while next_state.lives >= 0 and next_state.round_number < next_state.round_limit:
            action = self.get_action(next_state, None)
            next_state.update(action) #TODO: sim bullets?

    def get_action(self, state, tracer):
        blackboard = Blackboard()
        blackboard.set('state', state)

        def build(build_action):
            build_behavior = Sequence(
                SetSafestBuildingLocation(),
                Selector(
                    Sequence(
                        Inverter(AtLocation()),
                        Inverter(MoveToLocation())
                    ),
                    SetAction(build_action)
                )
            )
            return build_behavior

        behavior = Selector(
            Sequence(
                Inverter(HasShip()),
                SetAction(NOTHING)
            ),
            Sequence(
                InDanger(),
                SearchBestAction(4, True)
            ),
            Sequence(
                Selector(
                    Sequence(
                        HasSpareLives(),
                        Selector(
                            Sequence(
                                # Inverter(IsSoleSurvivor()),
                                KillTracerNoWait()
                            ),
                            Sequence(
                                Inverter(HasMissileController()),
                                build(BUILD_MISSILE_CONTROLLER)
                            ),
                            Sequence(
                                Inverter(HasAlienFactory()),
                                build(BUILD_ALIEN_FACTORY)
                            )
                        )
                    ),
                    Sequence(
                        KillTracer(),
                    ),
                ),
                Sequence(
                    IsMoveDangerous(),
                    SearchBestAction(4)
                )
            )
        )

        flow = []
        behavior.run(blackboard, flow)
        action = blackboard.get('action')
        self.logger.debug('Flow: %s' % ' '.join(str(f) for f in flow))

        if not action:
            action = NOTHING
        return action

TREE_SEARCH = TreeSearchBestAction()
MCTS_SEARCH = MctsBestAction()
SEARCH = {'tree': TREE_SEARCH, 'mcts': MCTS_SEARCH}
