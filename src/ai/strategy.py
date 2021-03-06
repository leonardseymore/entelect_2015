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
        return state.your_alien_factory() is not None


class HasMissileController(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.your_missile_controller() is not None

class IsEarlyGame(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.round_number < 40


class EnemyHasAlienFactory(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.enemy_alien_factory() is not None


class KillEnemyAlienFactory(Task):
    def __init__(self, limit=22, *children):
        Task.__init__(self, *children)
        self.limit = limit

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()

        target = None
        while not target and self.limit > 0 and next_state.round_number < next_state.round_limit:
            af = next_state.enemy_alien_factory()
            if not af:
                break

            next_state.update(NOTHING, True, state.round_number, True)
            self.logger.debug('Next state\n%s', next_state)
            if len(next_state.tracer_alien_factory_hits) > 0:
                target = next_state.tracer_alien_factory_hits[0]
                self.logger.debug('Hit enemy alien factory %s', target)
                break

            # candidates = filter(lambda tr: af.x <= tr.target.x < af.x + af.entity_behavior.width, next_state.tracer_shield_hits)
            # if len(candidates) > 0:
            #     self.logger.debug('Hit shield hits %s', candidates)
            #     target = candidates[0]
            self.limit -= 1

        self.logger.debug('Target tracer %s', target)
        if not target:
            self.logger.debug('No tracer found')
            return False
        blackboard.set('tracer', target)
        return True


class HasAllBuildings(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.your_missile_controller() is not None and state.your_alien_factory() is not None


class HasSpareLives(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.your_lives() > 0


class HasShip(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.your_ship() is not None


class FirstWaveKilled(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.your_kills() >= 3


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
        return state.your_ship().x == loc


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
        if loc < state.your_ship().x:
            blackboard.set('action', MOVE_LEFT)
        elif loc > state.your_ship().x:
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
        next_state.update(action, add_bullet_tracers=True)
        for i in xrange(0, 3):  # predict i gonna move into bad situation
            if not next_state.your_ship() or next_state.your_lives() < state.your_lives() or next_state.your_ship().is_hit_by_lethal_tracer():
                self.logger.debug('Dangerous action %s', action)
                return True
            next_state.update(NOTHING, add_bullet_tracers=True)
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
        return len(state.your_missiles()) < state.your_missile_limit()


class IsStartingRound(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.round_number == 0

class IsRoundNumber(Task):
    def __init__(self, round_number, *children):
        Task.__init__(self, *children)
        self.round_number = round_number

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.round_number == self.round_number

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
        ).run(blackboard, flow)


class CanKill(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        next_state.update(SHOOT)
        for i in xrange(0, 10):  # predict missile up to spawn row
            next_state.update(NOTHING)
            if next_state.your_kills() > state.your_kills() + len(state.your_missiles()):
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
        x = state.your_ship().x + 1
        for y in xrange(state.your_ship().y - self.dist, state.your_ship().y):
            entity = state.get_entity(x, y)
            if entity and entity.entity_type == BULLET:
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
    def __init__(self, target_alien=None, *children):
        Task.__init__(self, *children)
        self.target_alien = target_alien

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()

        target = None
        if self.target_alien:
            self.logger.debug('Searching for tracer to target alien %s', self.target_alien)
            while next_state.round_number < next_state.round_limit:
                next_state.update(NOTHING, True, state.round_number, True)
                # self.logger.debug('Next state\n%s', next_state)
                alien_tracer = filter(lambda tr: tr.target == self.target_alien, next_state.tracer_hits)
                if len(alien_tracer) > 0:
                    self.logger.debug('Found alien tracer alien=%s, tracers=%s', self.target_alien, alien_tracer)
                    target = alien_tracer[0]
                    break
            if not target:
                self.logger.debug('No tracer to target alien found %s', self.target_alien)
        else:
            for i in xrange(0, 12):
                next_state.update(NOTHING, True, state.round_number, True)
                self.logger.debug('Next state\n%s', next_state)
                candidates = filter(lambda tr: False if tr.tracer_bullet_hit and tr.tracer_bullet_hit.shoot_odds == 1.0 else True, next_state.tracer_hits)
                # candidates = filter(lambda tr: tr.alien.y >= next_state.enemy_alien_bbox().bottom - 3,candidates)
                if len(candidates) > 0:
                    target = candidates[0]

        self.logger.debug('Target tracer %s', target)
        if not target:
            self.logger.debug('No tracer found %s', target)
            return False
        blackboard.set('tracer', target)
        return True


class KillTracer(Task):
    def __init__(self, tracer=None, high_risk_alien=False, wait=True, from_blackboard=False, *children):
        Task.__init__(self, *children)
        self.tracer = tracer
        self.high_risk_alien = high_risk_alien
        self.wait = wait
        self.from_blackboard = from_blackboard

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)

        if self.high_risk_alien:
            high_risk_aliens = blackboard.get('high_risk_aliens')
            highest_risk_alien = high_risk_aliens[0]
            if not SetTracer(target_alien=highest_risk_alien).run(blackboard, flow):
                return False
            tracer = blackboard.get('tracer')
        elif self.from_blackboard:
            tracer = blackboard.get('tracer')
        elif not self.tracer:
            if not SetTracer().run(blackboard, flow):
                return False
            tracer = blackboard.get('tracer')
        else:
            tracer = self.tracer
        loc = tracer.starting_x - 1
        blackboard.set('loc', loc)

        if self.wait:
            Sequence(
                MoveToLocation(loc),
                WaitTillRound(tracer.starting_round - 1),
                HasMissile(),
                SetAction(SHOOT)
            ).run(blackboard, flow)
            return True
        else:
            return Sequence(
                SetLocation(loc),
                AtLocation(),
                AtRound(tracer.starting_round - 1),
                HasMissile(),
                SetAction(SHOOT)
            ).run(blackboard, flow)

    def __repr__(self):
        return 'KillTracer(HR=%s)' % self.high_risk_alien


class IsInvasionImminent(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return state.alien_bbox.bottom > 7


class InDanger(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        for i in xrange(0, 4):  # predict if bullet or missile gonna kill me
            if next_state.your_lives() < state.your_lives():
                return True
            next_state.update(NOTHING, True, state.round_number, True)

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
        if not next_state.your_ship():
            return True

        for x in xrange(next_state.your_ship().x - 1, next_state.your_ship().x + next_state.your_ship().width + 1):
            for y in [next_state.your_ship().y - 1, next_state.your_ship().y - 2]:
                entity = next_state.get_entity(x, y)
                if entity and entity.entity_type == ALIEN:
                    self.logger.debug('Alien too close! %s', entity)
                    return True
        return False


class IsSoleSurvivor(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        return len(state.enemy_aliens()) == 1

class TMinusLt(Task):
    def __init__(self, t_minus, *children):
        Task.__init__(self, *children)
        self.t_minus = t_minus

    def run(self, blackboard, flow):
        return blackboard.get('t_minus') <= self.t_minus


class SetHighRiskAliens(Task):
    def __init__(self, dist=5, *children):
        Task.__init__(self, *children)
        self.dist = dist

    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        while next_state.your_ship():
            next_state.update(NOTHING)
            enemy_aliens = next_state.enemy_aliens()
            high_risk_aliens = filter(lambda a: a.y > PLAYING_FIELD_HEIGHT - self.dist, enemy_aliens)
            if len(high_risk_aliens) > 0:
                blackboard.set('high_risk_aliens', high_risk_aliens)
                blackboard.set('t_minus', next_state.round_number - state.round_number)
                self.logger.debug('High risk aliens %s in T-%s', high_risk_aliens, next_state.round_number - state.round_number)
                return True
        self.logger.debug('No high risk aliens could be found %s', high_risk_aliens)
        return False

class SetHighRiskExplodingAliens(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        while len(next_state.enemy_exploding_aliens()) == len(state.enemy_exploding_aliens()):
            next_state.update(NOTHING)
        enemy_aliens = next_state.enemy_exploding_aliens()
        # high_risk_aliens = sorted(enemy_aliens, key=lambda a: (-next_state.enemy_aliens_delta_x() * a.x, a.y))
        high_risk_aliens = enemy_aliens
        if len(high_risk_aliens) > 0:
            blackboard.set('high_risk_aliens', high_risk_aliens)
            self.logger.debug('High risk exploding aliens %s', high_risk_aliens)
            return True
        return False

class SetHighRiskSpawnAliens(Task):
    def run(self, blackboard, flow):
        Task.run(self, blackboard, flow)
        state = blackboard.get('state')
        next_state = state.clone()
        while len(next_state.enemy_aliens()) == len(state.enemy_aliens()):
            next_state.update(NOTHING)
        print next_state
        enemy_aliens = next_state.enemy_aliens()
        high_risk_aliens = sorted(enemy_aliens, key=lambda a: (-next_state.enemy_aliens_delta_x() * a.x, a.y))
        if len(high_risk_aliens) > 0:
            blackboard.set('high_risk_aliens', [high_risk_aliens[0]])
            self.logger.debug('High risk spawn aliens %s', high_risk_aliens)
            return True
        return False

strategies = [InDanger(), SearchBestAction(4), SearchBestAction(4, True), SearchBestAction(1, True),
              IsInvasionImminent(), IsAlienTooClose(), SetTracer(), IsMoveDangerous(),
              Sequence(SetAction(MOVE_LEFT), IsMoveDangerous())]

class TreeSearchBestAction:
    def __init__(self):
        self.logger = logging.getLogger('search.TreeSearchBestAction')

    @staticmethod
    def evaluate(state, include_tracers, loc):
        result = 0
        result += state.your_lives() * 5
        result += state.your_kills() * 2
        result -= state.enemy_alien_bbox().bottom
        if state.your_missile_controller():
            result += 10
        if state.your_alien_factory():
            result += 10
        result -= len(state.your_missiles())
        if state.your_ship():
            if include_tracers:
                if state.your_ship().is_hit_by_lethal_tracer():
                    result -= 500
            result += 1000
            if loc:
                result -= abs(state.your_ship().x - loc)
        return result

    def search(self, state, max_depth, include_tracers=False, loc=None):
        self.logger.debug('Starting state %s\n%s', self.evaluate(state, include_tracers, loc), state)
        return self.search_recurse(state, state.round_number, max_depth, include_tracers, 0, [], loc)[1]

    def search_recurse(self, state, starting_round, max_depth, include_tracers, current_depth, actions, loc):
        if state.your_lives() < 0 or current_depth == max_depth:
            return self.evaluate(state, include_tracers, loc), None

        best_action = None
        best_score = -sys.maxint

        for i, action in enumerate(state.get_available_evade_actions()):
            new_state = state.clone()
            new_state.update(action, add_bullet_tracers=True)
            actions.append(action)

            self.logger.debug('\n%s %s\n%s', self.evaluate(new_state, include_tracers, loc),
                              ' -> '.join(actions), new_state)
            current_score, current_action = self.search_recurse(new_state, starting_round, max_depth, include_tracers,
                                                                current_depth + 1, actions, loc)
            actions.pop()

            if not new_state.your_ship():
                return best_score, None

            if current_score > best_score:
                best_score = current_score
                best_action = action

        self.logger.debug('Best tree search action: depth=%s score=%s action=%s',
                          current_depth + 1, best_score, best_action)
        return best_score, best_action

TREE_SEARCH = TreeSearchBestAction()
SEARCH = {'tree': TREE_SEARCH}
