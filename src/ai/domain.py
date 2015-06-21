from ai.entelect import *
import copy
import random

class Box:
    __slots__ = ['top', 'right', 'bottom', 'left']

    def __init__(self):
        self.top = -1
        self.right = -1
        self.bottom = -1
        self.left = -1


class State:
    def __init__(self):
        self.playing_field = [None] * (PLAYING_FIELD_WIDTH * PLAYING_FIELD_HEIGHT)
        self.width = PLAYING_FIELD_WIDTH
        self.height = PLAYING_FIELD_HEIGHT

        self.player_number_real = None
        self.round_number = None
        self.round_limit = None
        self.kills = None
        self.lives = None
        self.respawn_timer = None
        self.missile_limit = 1
        self.wave_size = None
        self.aliens_delta_x = None
        self.enemy_has_alien_factory = None
        self.enemy_has_spare_lives = None

        self.ship = None
        self.alien_factory = None
        self.missile_controller = None

        self.alien_bbox = None

        self.shields = []
        self.missiles = []
        self.bullets = []
        self.aliens = []
        self.tracers = []
        self.tracer_bullets = []
        self.tracer_hits = []


    @staticmethod
    def from_game_state(game_state):
        state = State()
        offset_x = 1
        offset_y = 12
        state.round_number = game_state['RoundNumber']
        state.round_limit = game_state['RoundLimit']
        you = game_state['Players'][0]
        state.player_number_real = you['PlayerNumberReal']
        enemy = game_state['Players'][1]
        state.kills = you['Kills']
        state.enemy_has_spare_lives = enemy['Lives'] > 0
        state.lives = you['Lives']
        state.respawn_timer = you['RespawnTimer']
        state.missile_limit = you['MissileLimit']
        state.wave_size = enemy['AlienWaveSize']
        your_ship = you['Ship']
        if your_ship:
            Ship(your_ship['X'] - offset_x, your_ship['Y'] - offset_y, 1).add(state)
        your_alien_factory = you['AlienFactory']
        if your_alien_factory:
            AlienFactory(your_alien_factory['X'] - offset_x, your_alien_factory['Y'] - offset_y, 1).add(state)
        state.enemy_has_alien_factory = enemy['AlienFactory'] is None
        your_missile_controller = you['MissileController']
        if your_missile_controller:
            MissileController(your_missile_controller['X'] - offset_x, your_missile_controller['Y'] - offset_y, 1).add(state)
        alien_man = enemy['AlienManager']
        state.aliens_delta_x = alien_man['DeltaX']
        game_map = game_state['Map']
        your_field_end_x = 18
        your_field_end_y = 25
        for row_index in reversed(xrange(offset_y, your_field_end_y)):
            for column_index in reversed(xrange(offset_x, your_field_end_x)):
                cell = game_map['Rows'][row_index][column_index]
                if not cell:
                    continue
                x = cell['X'] - offset_x
                y = cell['Y'] - offset_y
                if cell['Type'] == SHIELD:
                    Shield(x, y, 1).add(state)
                elif cell['Type'] == BULLET:
                    Bullet(x, y, 2).add(state)
                elif cell['Type'] == ALIEN:
                    Alien(x, y, 2).add(state)
                elif cell['Type'] == MISSILE:
                    Missile(x, y, cell['PlayerNumber']).add(state)
        state.update_bbox()
        return state

    @staticmethod
    def in_bounds(x, y, width=1):
        return 0 <= y < PLAYING_FIELD_HEIGHT and 0 <= x < PLAYING_FIELD_WIDTH and x + width - 1 < PLAYING_FIELD_WIDTH

    @staticmethod
    def in_bounds_hv(x, y):
        return 0 <= y < PLAYING_FIELD_HEIGHT and 0 <= x < PLAYING_FIELD_WIDTH

    def is_tracer_bullet_x(self, x):
        for tracer_bullet in self.tracer_bullets:
            if tracer_bullet.x == x:
                return True
        return None

    def get_tracer_bullet(self, x, y):
        for tracer_bullet in self.tracer_bullets:
            if tracer_bullet.x == x and tracer_bullet.y == y:
                return tracer_bullet
        return None

    def get_entity(self, x, y):
        if self.in_bounds_hv(x, y):
            return self.playing_field[PLAYING_FIELD_WIDTH * y + x]
        return None

    def add_entity(self, entity):
        return self.traverse_map('add', entity, entity.x, entity.y)

    def add_entity_unsafe(self, entity):
        if entity:
            for x in xrange(entity.x, entity.x + entity.entity_behavior.width):
                self.playing_field[PLAYING_FIELD_WIDTH * entity.y + x] = entity

    def remove_entity(self, entity):
        self.traverse_map('remove', entity, entity.x, entity.y)

    def move_entity(self, entity, x, y):
        self.traverse_map('remove', entity, entity.x, entity.y)
        if self.traverse_map('add', entity, x, y):
            entity.x = x
            entity.y = y

    def traverse_map(self, action, entity, target_x, target_y):
        in_bounds = self.in_bounds(target_x, target_y, entity.entity_behavior.width)
        if not in_bounds and not action == 'remove':
            entity.handle_out_of_bounds(self, target_y >= self.height)
            return False
        for x in xrange(target_x, target_x + entity.entity_behavior.width):
            y = target_y
            if action == 'add':
                existing_entity = self.get_entity(x, y)
                if existing_entity:
                    entity.handle_collision(self, existing_entity)
                    if existing_entity.entity_behavior.entity_type != TRACER:
                        return False
                tracer_bullet = self.get_tracer_bullet(x, y)
                if tracer_bullet:
                    entity.handle_collision(self, tracer_bullet)
                self.playing_field[PLAYING_FIELD_WIDTH * y + x] = entity
            elif action == 'remove':
                if self.in_bounds_hv(x, y):
                    self.playing_field[PLAYING_FIELD_WIDTH * y + x] = None
        return True

    def check_open(self, target_x, target_y, width):
        if not self.in_bounds(target_x, target_y, width):
            return False
        for x in xrange(target_x, target_x + width):
            y = target_y
            if self.get_entity(x, y):
                return False
        return True

    def get_available_actions(self):
        ship = self.ship
        if not self.ship:
            return [NOTHING]

        next_state = self.clone()
        next_state.update(NOTHING)

        actions = []
        assert self.missile_limit <= 2
        if len(self.missiles) < self.missile_limit:
            actions.append(SHOOT)
        if self.in_bounds(ship.x - 1, ship.y, ship.entity_behavior.width):
            if not next_state.get_entity(ship.x - 1, ship.y):
                actions.append(MOVE_LEFT)
        if self.in_bounds(ship.x + 1, ship.y, ship.entity_behavior.width):
            if not next_state.get_entity(ship.x + ship.entity_behavior.width, ship.y):
                actions.append(MOVE_RIGHT)
        if self.lives > 0:
            if not self.alien_factory:
                actions.append(BUILD_ALIEN_FACTORY)
            if not self.missile_controller:
                actions.append(BUILD_MISSILE_CONTROLLER)
            actions.append(BUILD_SHIELD)
        actions.append(NOTHING)
        return actions

    def get_available_evade_actions(self):
        ship = self.ship
        if not self.ship:
            return [NOTHING]

        next_state = self.clone()
        next_state.update(NOTHING)

        actions = [NOTHING]
        if len(self.missiles) < self.missile_limit:
            actions.append(SHOOT)
        if self.in_bounds(ship.x - 1, ship.y, ship.entity_behavior.width):
            if not next_state.get_entity(ship.x - 1, ship.y):
                actions.append(MOVE_LEFT)
        if self.in_bounds(ship.x + 1, ship.y, ship.entity_behavior.width):
            if not next_state.get_entity(ship.x + ship.entity_behavior.width, ship.y):
                actions.append(MOVE_RIGHT)
        return actions

    def calculate_alien_bbox(self):
        bbox = Box()
        for alien in self.aliens:
            x = alien.x
            y = alien.y
            if bbox.top == -1 or y < bbox.top:
                bbox.top = y
            if bbox.bottom == -1 or y > bbox.bottom:
                bbox.bottom = y
            if bbox.left == -1 or x < bbox.left:
                bbox.left = x
            if bbox.right == -1 or x > bbox.right:
                bbox.right = x

        for alien in self.aliens:
            if alien.y == bbox.bottom:
                alien.at_front_line = True
            else:
                alien.at_front_line = False

        return bbox

    def update_bbox(self):
        self.alien_bbox = self.calculate_alien_bbox()

    def update(self, action, add_tracers=False, tracer_starting_round=0, add_bullet_tracers=False):
        self.round_number += 1
        if self.round_number == 40:
            self.wave_size += 1

        self.update_bbox()
        # Update the alien commander to spawn new aliens and give aliens orders
        if len(self.aliens) == 0 or self.alien_bbox.top == 3:
            for i in xrange(0, self.wave_size):
                if self.aliens_delta_x > 0:
                    Alien((i * 3), 1, 2).add(self)
                else:
                    Alien(16 - (i * 3), 1, 2).add(self)

        self.update_bbox()
        delta_x = self.aliens_delta_x
        delta_y = 0
        if self.aliens_delta_x == -1:
            if self.alien_bbox.left == 0:
                delta_x = 0
                delta_y = 1
                self.aliens_delta_x = 1
        if self.aliens_delta_x == 1:
            if self.alien_bbox.right == self.width - 1:
                delta_x = 0
                delta_y = 1
                self.aliens_delta_x = -1
        for alien in self.aliens:
            alien.delta_x = delta_x
            alien.delta_y = delta_y

        if add_bullet_tracers:
            if len(self.aliens) > 0:
                if self.round_number % 6 == 0:
                    self.set_alien_shoot_odds()
                else:
                    for alien in self.aliens:
                        alien.shoot_odds = 0

        # Update missiles, moving them forward
        for missile in sorted(self.missiles, key=lambda m: m.y):
            missile.update(self)

        # Update alien bullets, moving them forward
        for tracer_bullet in self.tracer_bullets[:]:
            tracer_bullet.update(self)

        for bullet in self.bullets[:]:
            bullet.update(self)

        for tracer in self.tracers[:]:
            tracer.update(self)

        if add_tracers and self.ship:
            for x in xrange(1, PLAYING_FIELD_WIDTH - 2):
                y = PLAYING_FIELD_HEIGHT - 3
                entity = self.get_entity(x, y)
                if entity and entity.entity_behavior.entity_type == SHIELD:
                    continue
                if abs(self.ship.x + 1 - x) < self.round_number - tracer_starting_round:
                    Tracer(x, y, 1, self.round_number, x).add(self)

        # Update aliens, executing their move & shoot orders
        for alien in self.aliens[:]:
            alien.update(self)

        # Update ships, executing their orders
        if self.ship:
            self.ship.perform_action(self, action)

        # Advance respawn timer and respawn ships if necessary.
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                Ship(self.width / 2 - 1, self.height - 2, 1).add(self)

    def select_shooting_alien(self):
        shoot_at_player = random.randint(0, 2) < 1 # 66% random, 33% at player
        if shoot_at_player:
            return self.shoot_at_player(), 0.333
        else:
            return self.shoot_at_random()

    def shoot_at_player(self):
        front_line = filter(lambda a: a.at_front_line, self.aliens)
        closest_alien = None
        closest_distance = 100
        target_x = PLAYING_FIELD_WIDTH / 2
        if self.ship:
            target_x = self.ship.x

        for alien in front_line:
            distance = abs(alien.x + alien.delta_x - target_x)
            if distance >= closest_distance:
                continue

            closest_alien = alien
            closest_distance = distance
        return closest_alien

    def shoot_at_random(self):
        exclude_alien = self.shoot_at_player()
        trigger_happy = self.trigger_happy_aliens()
        trigger_happy.remove(exclude_alien)
        return random.choice(trigger_happy), 0.666 / len(trigger_happy)

    def trigger_happy_aliens(self):
        if len(self.aliens) == 0:
            return None
        second_line_y = self.alien_bbox.bottom - 2
        aliens = []
        front_line = filter(lambda a: a.at_front_line, self.aliens)
        for alien in front_line:
            aliens.append(alien)
        second_line = filter(lambda a: a.y == second_line_y, self.aliens)
        for alien in second_line:
            entity_in_front = self.get_entity(alien.x, alien.y + 2)
            if entity_in_front is None or entity_in_front.entity_behavior.entity_type != ALIEN:
                aliens.append(alien)
        return aliens

    def set_alien_shoot_odds(self):
        for alien in self.aliens:
            alien.shoot_odds = 0
        if len(self.aliens) == 1:
            self.aliens[0].shoot_odds = 1.0
            return

        closest_alien = self.shoot_at_player()
        closest_alien.shoot_odds = 0.333
        trigger_happy = self.trigger_happy_aliens()
        trigger_happy.remove(closest_alien)
        for alien in trigger_happy:
            alien.shoot_odds = 0.666 / len(trigger_happy)

    def __deepcopy__(self, memo):
        state = State()
        state.round_number = self.round_number
        state.round_limit = self.round_limit
        state.player_number_real = self.player_number_real
        state.kills = self.kills
        state.enemy_has_spare_lives = self.enemy_has_spare_lives
        state.lives = self.lives
        state.respawn_timer = self.respawn_timer
        state.missile_limit = self.missile_limit
        state.wave_size = self.wave_size
        state.ship = copy.deepcopy(self.ship)
        state.alien_factory = self.alien_factory
        state.enemy_has_alien_factory = self.enemy_has_alien_factory
        state.missile_controller = self.missile_controller
        state.aliens_delta_x = self.aliens_delta_x
        state.shields = self.shields[:]
        state.bullets = copy.deepcopy(self.bullets)
        state.missiles = copy.deepcopy(self.missiles)
        state.aliens = copy.deepcopy(self.aliens)
        state.tracers = copy.deepcopy(self.tracers)
        state.tracer_bullets = copy.deepcopy(self.tracer_bullets)

        state.playing_field = [None] * (PLAYING_FIELD_WIDTH * PLAYING_FIELD_HEIGHT)
        state.add_entity_unsafe(state.ship)
        state.add_entity_unsafe(state.missile_controller)
        state.add_entity_unsafe(state.alien_factory)

        for entity in state.shields + state.bullets + state.missiles + state.aliens + state.tracers:
            state.add_entity_unsafe(entity)

        state.update_bbox()
        return state

    def clone(self):
        return copy.deepcopy(self)

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def __str__(self):
        text = '+%03d/%d+++++++:)%d+\n' % (self.round_number, self.round_limit, self.lives)
        for y in xrange(0, PLAYING_FIELD_HEIGHT):
            text += '+'
            for x in xrange(0, PLAYING_FIELD_WIDTH):
                entity = self.get_entity(x, y)
                symbol = ' '
                if entity:
                    symbol = entity.entity_behavior.symbol
                tracer_bullet = self.get_tracer_bullet(x, y)
                if tracer_bullet:
                    symbol = '%'
                text += symbol
            text += '+\n'
        text += '+!%d/%d+++++++++x%03d+\n' % (len(self.missiles), self.missile_limit, self.kills)
        return text

class EntityBehavior:
    def __init__(self, entity_type, symbol, width):
        self.entity_type = entity_type
        self.symbol = symbol
        self.width = width

    def destroy(self, state, entity):
        state.remove_entity(entity)

    def add(self, state, entity):
        return state.add_entity(entity)

    def handle_out_of_bounds(self, state, entity, bottom):
        pass

    def handle_collision(self, state, entity, other):
        if other.entity_behavior.entity_type == TRACER:
            return
        if other.entity_behavior.entity_type == TRACER_BULLET:
            entity.tracer_bullet_hit = other
            return
        entity.destroy(state)
        other.destroy(state)

    def __str__(self):
        return self.__class__.__name__

class ShieldBehavior(EntityBehavior):
    def __init__(self):
        EntityBehavior.__init__(self, SHIELD, SHIELD_SYMBOL, 1)

    def add(self, state, entity):
        if EntityBehavior.add(self, state, entity):
            state.shields.append(entity)
SHIELD_BEHAVIOR = ShieldBehavior()

class AlienBehavior(EntityBehavior):
    def __init__(self):
        EntityBehavior.__init__(self, ALIEN, ALIEN_SYMBOL, 1)

    def update(self, state, alien):
        state.move_entity(alien, alien.x + alien.delta_x, alien.y + alien.delta_y)

        if alien.shoot_odds > 0:
            TracerBullet(alien.x, alien.y + 1, 2, alien.shoot_odds).add(state)

    def add(self, state, entity):
        if EntityBehavior.add(self, state, entity):
            state.aliens.append(entity)

    def destroy(self, state, entity):
        EntityBehavior.destroy(self, state, entity)
        if entity in state.aliens:
            state.aliens.remove(entity)

    def handle_out_of_bounds(self, state, entity, bottom):
        EntityBehavior.handle_out_of_bounds(self, entity, bottom)
        if bottom:
            state.lives -= 1
            if state.ship:
                state.ship.destroy(state)
            entity.destroy(entity)

    def handle_collision(self, state, entity, other):
        EntityBehavior.handle_collision(self, state, entity, other)
        if other.entity_behavior.entity_type == MISSILE and entity.player_number != other.player_number:
            state.kills += 1
            state.update_bbox()
        elif other.entity_behavior.entity_type == TRACER:
            other.energy = PLAYING_FIELD_HEIGHT - 3 - entity.y
            other.alien = entity
            state.tracer_hits.append(other)
        elif other.entity_behavior.entity_type == SHIELD:
            self.explode(state, entity)

    def explode(self, state, entity):
        for x in xrange(entity.x - 1 + entity.delta_x, entity.x + 2 + entity.delta_y):
            for y in xrange(entity.y - 1 + entity.delta_x, entity.y + 2 + entity.delta_y):
                if entity.x == x and entity.y == y:
                    continue
                other = state.get_entity(x, y)
                if other:
                    other.destroy(state)
ALIEN_BEHAVIOR = AlienBehavior()


class BulletBehavior(EntityBehavior):
    def __init__(self):
        EntityBehavior.__init__(self, BULLET, BULLET_SYMBOL, 1)

    def update(self, state, entity):
        state.move_entity(entity, entity.x, entity.y + entity.delta_y)

    def handle_out_of_bounds(self, state, entity, bottom):
        EntityBehavior.handle_out_of_bounds(self, state, entity, bottom)
        self.destroy(state, entity)

    def add(self, state, entity):
        if EntityBehavior.add(self, state, entity):
            state.bullets.append(entity)

    def destroy(self, state, entity):
        EntityBehavior.destroy(self, state, entity)
        if entity in state.bullets:
            state.bullets.remove(entity)
BULLET_BEHAVIOR = BulletBehavior()


class TracerBulletBehavior(EntityBehavior):
    def __init__(self):
        EntityBehavior.__init__(self, TRACER_BULLET, TRACER_BULLET_SYMBOL, 1)

    def update(self, state, entity):
        entity.y += entity.delta_y
        other = state.get_entity(entity.x, entity.y)
        if other:
            entity.handle_collision(state, other)

    def handle_out_of_bounds(self, state, entity, bottom):
        EntityBehavior.handle_out_of_bounds(self, state, entity, bottom)
        state.destroy(state, entity)

    def handle_collision(self, state, entity, other):
        other.tracer_bullet_hit = entity

    def add(self, state, entity):
        state.tracer_bullets.append(entity)
        other = state.get_entity(entity.x, entity.y)
        if other:
            entity.handle_collision(state, other)

    def destroy(self, state, entity):
        EntityBehavior.destroy(self, state, entity)
        if entity in state.tracer_bullets:
            state.tracer_bullets.remove(entity)
TRACER_BULLET_BEHAVIOR = TracerBulletBehavior()


class TracerBehavior(EntityBehavior):
    def __init__(self):
        EntityBehavior.__init__(self, TRACER, TRACER_SYMBOL, 1)

    def update(self, state, entity):
        state.move_entity(entity, entity.x, entity.y + entity.delta_y)

    def handle_out_of_bounds(self, state, entity, bottom):
        EntityBehavior.handle_out_of_bounds(self, state, entity, bottom)
        self.destroy(state, entity)

    def handle_collision(self, state, entity, other):
        if other.entity_behavior.entity_type == ALIEN:
            state.tracer_hits.append(entity)
            entity.alien = other
        # elif other.entity_behavior.entity_type == BULLET:
        #     entity.get_shot_odds = 0.0
        elif other.entity_behavior.entity_type == TRACER_BULLET:
            entity.tracer_bullet_hit = other
        else:
            self.destroy(state, entity)

    def add(self, state, entity):
        if EntityBehavior.add(self, state, entity):
            state.tracers.append(entity)

    def destroy(self, state, entity):
        EntityBehavior.destroy(self, state, entity)
        if entity in state.tracers:
            state.tracers.remove(entity)
TRACER_BEHAVIOR = TracerBehavior()


class MissileBehavior(EntityBehavior):
    def __init__(self, player_number):
        EntityBehavior.__init__(self, MISSILE, MISSILE_PLAYER1_SYMBOL if player_number == 1 else MISSILE_PLAYER2_SYMBOL, 1)
        self.delta_y = -1 if player_number == 1 else 1

    def update(self, state, entity):
        state.move_entity(entity, entity.x, entity.y + self.delta_y)

    # TODO: a missile does not get destroyed when it exits the top of the playing field
    def handle_out_of_bounds(self, state, entity, bottom):
        EntityBehavior.handle_out_of_bounds(self, state, entity, bottom)
        self.destroy(state, entity)

    def handle_collision(self, state, entity, other):
        EntityBehavior.handle_collision(self, state, entity, other)
        if other.entity_behavior.entity_type == ALIEN and entity.player_number != other.player_number:
            state.kills += 1
            state.update_bbox()

    def add(self, state, entity):
        if EntityBehavior.add(self, state, entity):
            state.missiles.append(entity)

    def destroy(self, state, entity):
        EntityBehavior.destroy(self, state, entity)
        if entity in state.missiles:
            state.missiles.remove(entity)
MISSILE_BEHAVIOR_PLAYER1 = MissileBehavior(1)
MISSILE_BEHAVIOR_PLAYER2 = MissileBehavior(2)


class ShipBehavior(EntityBehavior):
    def __init__(self):
        EntityBehavior.__init__(self, SHIP, SHIP_PLAYER1_SYMBOL, 3)

    def add(self, state, entity):
        if EntityBehavior.add(self, state, entity):
            state.ship = entity

    def destroy(self, state, entity):
        EntityBehavior.destroy(self, state, entity)
        state.lives -= 1
        state.respawn_timer = 3
        state.ship = None

    def perform_action(self, state, entity, action):
        if action == MOVE_LEFT:
            state.move_entity(entity, entity.x - 1, entity.y)
        elif action == MOVE_RIGHT:
            state.move_entity(entity, entity.x + 1, entity.y)
        elif action == SHOOT:
            Missile(entity.x + 1, entity.y - 1, entity.player_number).add(state)
        elif action == BUILD_ALIEN_FACTORY:
            AlienFactory(entity.x, entity.y + 1, entity.player_number).add(state)
        elif action == BUILD_MISSILE_CONTROLLER:
            MissileController(entity.x, entity.y + 1, entity.player_number).add(state)
        elif action == BUILD_SHIELD:
            pass  # TODO: build shield array
SHIP_BEHAVIOR = ShipBehavior()


class MissileControllerBehavior(EntityBehavior):
    def __init__(self):
        EntityBehavior.__init__(self, MISSILE_CONTROLLER, MISSILE_CONTROLLER_SYMBOL, 3)

    def add(self, state, entity):
        if EntityBehavior.add(self, state, entity):
            # TODO: can we assume constant limit of 2?
            state.missile_limit = 2
            state.missile_controller = entity

    def destroy(self, state, entity):
        EntityBehavior.destroy(self, state, entity)
        state.missile_limit = 1
        state.missile_controller = None
MISSILE_CONTROLLER_BEHAVIOR = MissileControllerBehavior()


class AlienFactoryBehavior(EntityBehavior):
    def __init__(self):
        EntityBehavior.__init__(self, ALIEN_FACTORY, ALIEN_FACTORY_SYMBOL, 3)

    def add(self, state, entity):
        if EntityBehavior.add(self, state, entity):
            state.alien_factory = entity

    def destroy(self, state, entity):
        EntityBehavior.destroy(self, state, entity)
        state.alien_factory = None
ALIEN_FACTORY_BEHAVIOR = AlienFactoryBehavior()


class Entity:
    def __init__(self, x, y, player_number, entity_behavior):
        self.x = x
        self.y = y
        self.entity_behavior = entity_behavior
        self.player_number = player_number
        self.tracer_bullet_hit = None

    def is_hit_by_lethal_tracer(self):
        return self.tracer_bullet_hit and self.tracer_bullet_hit.energy < 1

    def destroy(self, state):
        self.entity_behavior.destroy(state, self)

    def add(self, state):
        return self.entity_behavior.add(state, self)

    def handle_out_of_bounds(self, state, bottom):
        pass

    def handle_collision(self, state, other):
        self.entity_behavior.handle_collision(state, self, other)

    def __str__(self):
        return "%s@%d:%d" % (self.__class__.__name__, self.x, self.y)


class Shield(Entity):
    def __init__(self, x, y, player_number):
        Entity.__init__(self, x, y, player_number, SHIELD_BEHAVIOR)


class Alien(Entity):
    def __init__(self, x, y, player_number):
        Entity.__init__(self, x, y, player_number, ALIEN_BEHAVIOR)
        self.delta_y = -1 if player_number == 1 else 1
        self.delta_x = -1
        self.at_front_line = False
        self.shoot_odds = 0

    def update(self, state):
        self.entity_behavior.update(state, self)

    def explode(self, state):
        self.entity_behavior.explode(state, self)

    def __deepcopy__(self, memo):
        clone = Alien(self.x, self.y, self.player_number)
        clone.delta_y = self.delta_y
        clone.delta_x = self.delta_x
        clone.at_front_line = self.at_front_line
        clone.shoot_odds = self.shoot_odds
        return clone

class Bullet(Entity):
    def __init__(self, x, y, player_number):
        Entity.__init__(self, x, y, player_number, BULLET_BEHAVIOR)
        self.delta_y = -1 if player_number == 1 else 1

    def update(self, state):
        self.entity_behavior.update(state, self)

    def __deepcopy__(self, memo):
        return Bullet(self.x, self.y, self.player_number)


class TracerBullet(Entity):
    def __init__(self, x, y, player_number, shoot_odds):
        Entity.__init__(self, x, y, player_number, TRACER_BULLET_BEHAVIOR)
        self.delta_y = -1 if player_number == 1 else 1
        self.shoot_odds = shoot_odds
        self.energy = PLAYING_FIELD_HEIGHT - y - 2

    def update(self, state):
        self.entity_behavior.update(state, self)

    def __deepcopy__(self, memo):
        return TracerBullet(self.x, self.y, self.player_number, self.shoot_odds)

    def __str__(self):
        return "%s@%d:%d - shoot_odds=%s, energy=%d" % (self.__class__.__name__, self.x, self.y, self.shoot_odds, self.energy)

class Tracer(Entity):
    def __init__(self, x, y, player_number, starting_round, starting_x):
        Entity.__init__(self, x, y, player_number, TRACER_BEHAVIOR)
        self.delta_y = -1 if player_number == 1 else 1
        self.starting_round = starting_round
        self.starting_x = starting_x
        self.energy = 0
        self.alien = None

    def update(self, state):
        self.entity_behavior.update(state, self)

    def __deepcopy__(self, memo):
        clone = Tracer(self.x, self.y, self.player_number, self.starting_round, self.starting_x)
        clone.energy = self.energy
        clone.alien = self.alien
        return clone

    def __repr__(self):
        return '{%s}' % self

    def __eq__(self, other):
        return self.starting_x == other.starting_x and self.starting_round == other.starting_round

    def __str__(self):
        return "%s@%d:%d - starting_round=%s, starting_x=%d, tracer_bullet_hit=%s" % (self.__class__.__name__, self.x, self.y, self.starting_round, self.starting_x, self.tracer_bullet_hit)


class Missile(Entity):
    def __init__(self, x, y, player_number):
        Entity.__init__(self, x, y, player_number, MISSILE_BEHAVIOR_PLAYER1 if player_number == 1 else MISSILE_BEHAVIOR_PLAYER2)

    def update(self, state):
        self.entity_behavior.update(state, self)

    def __deepcopy__(self, memo):
        return Missile(self.x, self.y, self.player_number)

class Ship(Entity):
    def __init__(self, x, y, player_number):
        Entity.__init__(self, x, y, player_number, SHIP_BEHAVIOR)

    def perform_action(self, state, action):
        self.entity_behavior.perform_action(state, self, action)

    def __deepcopy__(self, memo):
        return Ship(self.x, self.y, self.player_number)

class MissileController(Entity):
    def __init__(self, x, y, player_number):
        Entity.__init__(self, x, y, player_number, MISSILE_CONTROLLER_BEHAVIOR)

    def __deepcopy__(self, memo):
        return MissileController(self.x, self.y, self.player_number)

class AlienFactory(Entity):
    def __init__(self, x, y, player_number):
        Entity.__init__(self, x, y, player_number, ALIEN_FACTORY_BEHAVIOR)

    def __deepcopy__(self, memo):
        return AlienFactory(self.x, self.y, self.player_number)