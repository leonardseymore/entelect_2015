from ai.entelect import *
import copy
import random

class State:
    def __init__(self, player_number_real, round_number, round_limit, kills, lives, respawn_timer, missile_limit,
                 wave_size, ship, alien_factory, missile_controller, aliens_delta_x, aliens, shields, missiles, bullets,
                 enemy_has_alien_factory, enemy_has_spare_lives):
        self.playing_field = [[None for x in range(PLAYING_FIELD_WIDTH)] for y in range(PLAYING_FIELD_HEIGHT)]
        self.width = PLAYING_FIELD_WIDTH
        self.height = PLAYING_FIELD_HEIGHT

        self.player_number_real = player_number_real
        self.round_number = round_number
        self.round_limit = round_limit
        self.kills = kills
        self.extremity_kills = 0
        self.front_line_kills = 0
        self.lives = lives
        self.respawn_timer = respawn_timer
        self.missile_limit = 1
        self.wave_size = wave_size
        self.aliens_delta_x = aliens_delta_x
        self.enemy_has_alien_factory = enemy_has_alien_factory
        self.enemy_has_spare_lives = enemy_has_spare_lives

        self.shields = []
        self.missiles = []
        self.bullets = []
        self.aliens = []
        self.tracers = []
        self.tracer_bullets = []
        self.tracer_hits = []

        self.ship = ship
        if ship:
            self.ship.state = self
            self.ship.add()
        self.alien_factory = alien_factory
        if alien_factory:
            self.alien_factory.state = self
            self.alien_factory.add()
        self.missile_controller = missile_controller
        if missile_controller:
            self.missile_controller.state = self
            self.missile_controller.add()

        for shield in shields:
            shield.state = self
            shield.add()
        for missile in missiles:
            missile.state = self
            missile.add()
        for bullet in bullets:
            bullet.state = self
            bullet.add()
        for alien in aliens:
            alien.state = self
            alien.add()

        self.alien_bbox = self.calculate_alien_bbox()

    @staticmethod
    def from_game_state(game_state):
        offset_x = 1
        offset_y = 12
        round_number = game_state['RoundNumber']
        round_limit = game_state['RoundLimit']
        you = game_state['Players'][0]
        player_number_real = you['PlayerNumberReal']
        enemy = game_state['Players'][1]
        kills = you['Kills']
        enemy_has_spare_lives = enemy['Lives'] > 0
        lives = you['Lives']
        respawn_timer = you['RespawnTimer']
        missile_limit = you['MissileLimit']
        wave_size = enemy['AlienWaveSize']
        your_ship = you['Ship']
        ship = None
        if your_ship:
            ship = Ship(None, your_ship['X'] - offset_x, your_ship['Y'] - offset_y, 1)
        your_alien_factory = you['AlienFactory']
        alien_factory = None
        if your_alien_factory:
            alien_factory = AlienFactory(None, your_alien_factory['X'] - offset_x, your_alien_factory['Y'] - offset_y, 1)
        enemy_has_alien_factory = enemy['AlienFactory'] is None
        your_missile_controller = you['MissileController']
        missile_controller = None
        if your_missile_controller:
            missile_controller = MissileController(None, your_missile_controller['X'] - offset_x, your_missile_controller['Y'] - offset_y, 1)
        alien_man = enemy['AlienManager']
        aliens_delta_x = alien_man['DeltaX']
        game_map = game_state['Map']
        shields = []
        bullets = []
        missiles = []
        aliens = []
        your_field_end_x = 18
        your_field_end_y = 25
        for row_index in reversed(range(offset_y, your_field_end_y)):
            for column_index in reversed(range(offset_x, your_field_end_x)):
                cell = game_map['Rows'][row_index][column_index]
                if not cell:
                    continue

                x = cell['X'] - offset_x
                y = cell['Y'] - offset_y
                if cell['Type'] == SHIELD:
                    shields.append(Shield(None, x, y, 1))
                elif cell['Type'] == BULLET:
                    shields.append(Bullet(None, x, y, 2))
                elif cell['Type'] == ALIEN:
                    alien = Alien(None, x, y, 2, cell['Id'])
                    aliens.append(alien)
                elif cell['Type'] == MISSILE:
                    missiles.append(Missile(None, x, y, cell['PlayerNumber']))
        return State(player_number_real, round_number, round_limit, kills, lives, respawn_timer, missile_limit, wave_size,
                     ship, alien_factory, missile_controller, aliens_delta_x, aliens, shields, missiles, bullets,
                     enemy_has_alien_factory, enemy_has_spare_lives)

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

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
        if self.in_bounds(x, y):
            return self.playing_field[y][x]
        return None

    def add_entity(self, entity):
        return self.traverse_map('add', entity, entity.x, entity.y)

    def remove_entity(self, entity):
        self.traverse_map('remove', entity, entity.x, entity.y)

    def move_entity(self, entity, x, y):
        self.traverse_map('remove', entity, entity.x, entity.y)
        if self.traverse_map('add', entity, x, y):
            entity.x = x
            entity.y = y

    def traverse_map(self, action, entity, target_x, target_y):
        in_bounds = self.in_bounds(target_x, target_y) and self.in_bounds(target_x + entity.width - 1, target_y)
        if not in_bounds and not action == 'remove':
            entity.handle_out_of_bounds(target_y >= self.height)
            return False
        for x in range(target_x, target_x + entity.width):
            y = target_y
            if action == 'add':
                existing_entity = self.get_entity(x, y)
                if existing_entity:
                    entity.handle_collision(existing_entity)
                    if existing_entity.entity_type != TRACER:
                        return False
                tracer_bullet = self.get_tracer_bullet(x, y)
                if tracer_bullet:
                    entity.handle_collision(tracer_bullet)
                self.playing_field[y][x] = entity
            elif action == 'remove':
                if self.in_bounds(x, y):
                    self.playing_field[y][x] = None
        return True

    def check_open(self, target_x, target_y, width):
        for x in range(target_x, target_x + width):
            y = target_y
            if not self.in_bounds(x, y) or self.get_entity(x, y):
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
        if self.in_bounds(ship.x - 1, ship.y):
            if not next_state.get_entity(ship.x - 1, ship.y):
                actions.append(MOVE_LEFT)
        if self.in_bounds(ship.x + ship.width, ship.y):
            if not next_state.get_entity(ship.x + ship.width, ship.y):
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
        if self.in_bounds(ship.x - 1, ship.y):
            if not next_state.get_entity(ship.x - 1, ship.y):
                actions.append(MOVE_LEFT)
        if self.in_bounds(ship.x + ship.width, ship.y):
            if not next_state.get_entity(ship.x + ship.width, ship.y):
                actions.append(MOVE_RIGHT)
        return actions

    def calculate_alien_bbox(self):
        bbox = {'top': -1, 'right': -1, 'bottom': -1, 'left': -1,
                'right_weight': 0, 'bottom_weight': 0, 'left_weight': 0}
        for alien in self.aliens:
            x = alien.x
            y = alien.y
            if bbox['top'] == -1 or y < bbox['top']:
                bbox['top'] = y
            if bbox['bottom'] == -1 or y > bbox['bottom']:
                bbox['bottom'] = y
            if bbox['left'] == -1 or x < bbox['left']:
                bbox['left'] = x
            if bbox['right'] == -1 or x > bbox['right']:
                bbox['right'] = x

        for alien in self.aliens:
            if alien.x == bbox['left']:
                bbox['left_weight'] += 1
            if alien.x == bbox['right']:
                bbox['right_weight'] += 1
            if alien.y == bbox['bottom']:
                bbox['bottom_weight'] += 1
                alien.at_front_line = True
            else:
                alien.at_front_line = False
            alien.at_extremity = alien.x == bbox['left'] or alien.x == bbox['right'] or alien.y == bbox['bottom']
            extremities = []
            if alien.x == bbox['left']:
                extremities.append('left')
            if alien.x == bbox['right']:
                extremities.append('right')
            if alien.y == bbox['bottom']:
                extremities.append('bottom')
            alien.extremities = extremities

        return bbox

    def update_bbox(self):
        self.alien_bbox = self.calculate_alien_bbox()

    def update(self, action, add_tracers=False, tracer_starting_round=0):
        self.round_number += 1
        if self.round_number == 40:
            self.wave_size += 1

        self.update_bbox()
        # Update the alien commander to spawn new aliens and give aliens orders
        if len(self.aliens) == 0 or self.alien_bbox['top'] == 3:
            for i in range(0, self.wave_size):
                if self.aliens_delta_x > 0:
                    Alien(self, (i * 3), 1, 2).add()
                else:
                    Alien(self, 16 - (i * 3), 1, 2).add()

        self.update_bbox()
        delta_x = self.aliens_delta_x
        delta_y = 0
        if self.aliens_delta_x == -1:
            if self.alien_bbox['left'] == 0:
                delta_x = 0
                delta_y = 1
                self.aliens_delta_x = 1
        if self.aliens_delta_x == 1:
            if self.alien_bbox['right'] == self.width - 1:
                delta_x = 0
                delta_y = 1
                self.aliens_delta_x = -1
        for alien in self.aliens:
            alien.delta_x = delta_x
            alien.delta_y = delta_y

        if add_tracers:
            if len(self.aliens) > 0:
                if self.round_number % 6 == 0:
                    self.set_alien_shoot_odds()
                else:
                    for alien in self.aliens:
                        alien.shoot_odds = 0

        # Update missiles, moving them forward
        for missile in sorted(self.missiles, key=lambda m: m.y):
            missile.update()

        # Update alien bullets, moving them forward
        for tracer_bullet in self.tracer_bullets[:]:
            tracer_bullet.update()

        for bullet in self.bullets[:]:
            bullet.update()

        for tracer in self.tracers[:]:
            tracer.update()

        if add_tracers and self.ship:
            for x in range(1, PLAYING_FIELD_WIDTH - 2):
                y = PLAYING_FIELD_HEIGHT - 3
                entity = self.get_entity(x, y)
                if entity and entity.entity_type == SHIELD:
                    continue
                if abs(self.ship.x + 1 - x) < self.round_number - tracer_starting_round:
                    tracer = Tracer(self, x, y, 1, self.round_number, x)
                    tracer.add()

        # Update aliens, executing their move & shoot orders
        for alien in self.aliens[:]:
            alien.update()

        # Update ships, executing their orders
        if self.ship:
            self.ship.perform_action(action)

        # Advance respawn timer and respawn ships if necessary.
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                Ship(self, self.width / 2 - 1, self.height - 2, 1).add()

    def select_shooting_alien(self):
        shoot_at_player = random.randint(0, 2) < 1 # 66% random, 33% at player
        if shoot_at_player:
            return self.shoot_at_player(), 0.333
        else:
            return self.shoot_at_random()

    def shoot_at_player(self):
        front_line = filter(lambda alien: alien.at_front_line, self.aliens)
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
        second_line_y = self.alien_bbox['bottom'] - 2
        aliens = []
        front_line = filter(lambda alien: alien.at_front_line, self.aliens)
        for alien in front_line:
            aliens.append(alien)
        second_line = filter(lambda alien: alien.y == second_line_y, self.aliens)
        for alien in second_line:
            entity_in_front = self.get_entity(alien.x, alien.y + 2)
            if entity_in_front is None or entity_in_front.entity_type != ALIEN:
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


    def clone(self):
        return copy.deepcopy(self)

    def __eq__(self, other):
        return self.__str__() == other.__str__()

    def __str__(self):
        playing_field = self.playing_field
        text = '+%03d/%d+++++++:)%d+\n' % (self.round_number, self.round_limit, self.lives)
        for y in range(0, PLAYING_FIELD_HEIGHT):
            text += '+'
            for x in range(0, PLAYING_FIELD_WIDTH):
                entity = playing_field[y][x]
                symbol = ' '
                if entity:
                    symbol = entity.symbol
                tracer_bullet = self.get_tracer_bullet(x, y)
                if tracer_bullet:
                    symbol = '%'
                text += symbol
            text += '+\n'
        text += '+!%d/%d+++++++++x%03d+\n' % (len(self.missiles), self.missile_limit, self.kills)
        return text

class Entity:
    def __init__(self, state, x, y, entity_type, symbol, width, player_number):
        self.state = state
        self.x = x
        self.y = y
        self.entity_type = entity_type
        self.symbol = symbol
        self.width = width
        self.player_number = player_number
        self.get_shot_odds = 0.0

    def destroy(self):
        self.state.remove_entity(self)

    def add(self):
        return self.state.add_entity(self)

    def handle_out_of_bounds(self, bottom):
        pass

    def handle_collision(self, other):
        if other.entity_type == TRACER:
            # other.destroy() # TODO: is this right?
            return
        if other.entity_type == TRACER_BULLET:
            self.get_shot_odds += other.shoot_odds
            return
        self.destroy()
        other.destroy()

    def __str__(self):
        return "%s@%d:%d" % (self.__class__.__name__, self.x, self.y)


class Shield(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, SHIELD, SHIELD_SYMBOL, 1, player_number)


class Alien(Entity):
    def __init__(self, state, x, y, player_number, alien_id=None):
        Entity.__init__(self, state, x, y, ALIEN, ALIEN_SYMBOL, 1, player_number)
        self.alien_id = alien_id
        self.delta_y = -1 if player_number == 1 else 1
        self.delta_x = -1
        self.at_extremity = False
        self.extremities = []
        self.at_front_line = False
        self.shoot_odds = 0
        self.behind_shield = False

    def update(self):
        self.state.move_entity(self, self.x + self.delta_x, self.y + self.delta_y)
        behind_shield = False
        for y in range(2, 5):
            entity = self.state.get_entity(self.x, PLAYING_FIELD_HEIGHT - y)
            if entity and entity.entity_type == SHIELD:
                behind_shield = True
        self.behind_shield = behind_shield

        if self.shoot_odds > 0:
            tracer_bullet = TracerBullet(self.state, self.x, self.y + 1, 2, self.shoot_odds)
            tracer_bullet.add()

    def add(self):
        if Entity.add(self):
            self.state.aliens.append(self)

    def destroy(self):
        Entity.destroy(self)
        if self in self.state.aliens:
            self.state.aliens.remove(self)

    def handle_out_of_bounds(self, bottom):
        Entity.handle_out_of_bounds(self, bottom)
        if bottom:
            self.state.lives -= 1
            if self.state.ship:
                self.state.ship.destroy()
            self.destroy()

    def handle_collision(self, other):
        Entity.handle_collision(self, other)
        if other.entity_type == MISSILE and self.player_number != other.player_number:
            self.state.kills += 1
            if self.at_front_line:
                self.state.front_line_kills += 1
            if self.at_extremity:
                self.state.extremity_kills += 1
                self.state.update_bbox()
        elif other.entity_type == TRACER:
            other.energy = PLAYING_FIELD_HEIGHT - 3 - self.y
            other.alien = self
            self.state.tracer_hits.append(other)
        elif other.entity_type == SHIELD:
            self.explode()

    def explode(self):
        for x in range(self.x - 1 + self.delta_x, self.x + 2 + self.delta_y):
            for y in range(self.y - 1 + self.delta_x, self.y + 2 + self.delta_y):
                if self.x == x and self.y == y:
                    continue
                entity = self.state.get_entity(x, y)
                if entity:
                    entity.destroy()

class Bullet(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, BULLET, BULLET_SYMBOL, 1, player_number)
        self.delta_y = -1 if player_number == 1 else 1

    def update(self):
        self.state.move_entity(self, self.x, self.y + self.delta_y)

    def handle_out_of_bounds(self, bottom):
        Entity.handle_out_of_bounds(self, bottom)
        self.destroy()

    def handle_collision(self, other):
        Entity.handle_collision(self, other)
        if other.entity_type == TRACER_BULLET:
            other.reach_dest_odds = 0.0

    def add(self):
        if Entity.add(self):
            self.state.bullets.append(self)

    def destroy(self):
        Entity.destroy(self)
        if self in self.state.bullets:
            self.state.bullets.remove(self)

class TracerBullet(Entity):
    def __init__(self, state, x, y, player_number, shoot_odds):
        Entity.__init__(self, state, x, y, TRACER_BULLET, TRACER_BULLET_SYMBOL, 1, player_number)
        self.delta_y = -1 if player_number == 1 else 1
        self.shoot_odds = shoot_odds

    def update(self):
        self.y += self.delta_y
        entity = self.state.get_entity(self.x, self.y)
        if entity:
            entity.handle_collision(self)

    def handle_out_of_bounds(self, bottom):
        Entity.handle_out_of_bounds(self, bottom)
        self.destroy()

    def handle_collision(self, other):
        other.get_shot_odds += self.shoot_odds
        if other.entity_type == TRACER:
            other.reach_dest_odds -= self.shoot_odds
        elif (other.entity_type == MISSILE or other.entity_type == BULLET) and other.player_number != self.player_number:
            other.reach_dest_odds = 0.0

    def add(self):
        self.state.tracer_bullets.append(self)

    def destroy(self):
        if self in self.state.tracer_bullets:
            self.state.tracer_bullets.remove(self)

    def __str__(self):
        return "%s@%d:%d - shoot_odds=%s" % (self.__class__.__name__, self.x, self.y, self.shoot_odds)

class Tracer(Entity):
    def __init__(self, state, x, y, player_number, starting_round, starting_x):
        Entity.__init__(self, state, x, y, TRACER, TRACER_SYMBOL, 1, player_number)
        self.delta_y = -1 if player_number == 1 else 1
        self.starting_round = starting_round
        self.starting_x = starting_x
        self.reach_dest_odds = 1.0
        self.energy = 0
        self.alien = None

    def update(self):
        self.state.move_entity(self, self.x, self.y + self.delta_y)

    def handle_out_of_bounds(self, bottom):
        Entity.handle_out_of_bounds(self, bottom)
        self.destroy()

    def handle_collision(self, other):
        if other.entity_type == ALIEN:
            self.energy = PLAYING_FIELD_HEIGHT - 3 - other.y
            self.state.tracer_hits.append(self)
            self.alien = other
        elif other.entity_type == BULLET:
            self.reach_dest_odds = 0.0
        elif other.entity_type == TRACER_BULLET:
            self.reach_dest_odds -= other.shoot_odds
        else:
            self.destroy()

    def add(self):
        if Entity.add(self):
            self.state.tracers.append(self)

    def destroy(self):
        if self in self.state.tracers:
            self.state.tracers.remove(self)

    def __repr__(self):
        return '{%s}' % self

    def __eq__(self, other):
        return self.starting_x == other.starting_x and self.starting_round == other.starting_round

    def __str__(self):
        return "%s@%d:%d - starting_round=%s, starting_x=%d, reach_dest_odds=%s, energy=%s" % (self.__class__.__name__, self.x, self.y, self.starting_round, self.starting_x, self.reach_dest_odds, self.energy)

class Missile(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, MISSILE, MISSILE_PLAYER1_SYMBOL if player_number == 1 else MISSILE_PLAYER2_SYMBOL, 1, player_number)
        self.delta_y = -1 if player_number == 1 else 1

    def update(self):
        self.state.move_entity(self, self.x, self.y + self.delta_y)

    def handle_out_of_bounds(self, bottom):
        Entity.handle_out_of_bounds(self, bottom)
        self.destroy()

    def handle_collision(self, other):
        print self, other
        Entity.handle_collision(self, other)
        if other.entity_type == ALIEN and self.player_number != other.player_number:
            self.state.kills += 1
            if other.at_front_line:
                self.state.front_line_kills += 1
            if other.at_extremity:
                self.state.extremity_kills += 1
                self.state.update_bbox()

    def add(self):
        if Entity.add(self):
            self.state.missiles.append(self)

    def destroy(self):
        Entity.destroy(self)
        if self in self.state.missiles:
            self.state.missiles.remove(self)


class Ship(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, SHIP, SHIP_PLAYER1_SYMBOL if player_number == 1 else SHIP_PLAYER2_SYMBOL, 3, player_number)

    def add(self):
        if Entity.add(self):
            self.state.ship = self

    def destroy(self):
        Entity.destroy(self)
        self.state.lives -= 1
        self.state.respawn_timer = 3
        self.state.ship = None

    def perform_action(self, action):
        if action == MOVE_LEFT:
            self.state.move_entity(self, self.x - 1, self.y)
        elif action == MOVE_RIGHT:
            self.state.move_entity(self, self.x + 1, self.y)
        elif action == SHOOT:
            Missile(self.state, self.x + 1, self.y - 1, self.player_number).add()
        elif action == BUILD_ALIEN_FACTORY:
            AlienFactory(self.state, self.x, self.y + 1, self.player_number).add()
        elif action == BUILD_MISSILE_CONTROLLER:
            MissileController(self.state, self.x, self.y + 1, self.player_number).add()
        elif action == BUILD_SHIELD:
            pass  # TODO: build shield array


class MissileController(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, MISSILE_CONTROLLER, MISSILE_CONTROLLER_SYMBOL, 3, player_number)
        self.delta_y = 1 if player_number == 1 else -1

    def add(self):
        if Entity.add(self):
            self.state.missile_limit += 1
            self.state.missile_controller = self

    def destroy(self):
        Entity.destroy(self)
        self.state.missile_limit -= 1
        self.state.missile_controller = None


class AlienFactory(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, ALIEN_FACTORY, ALIEN_FACTORY_SYMBOL, 3, player_number)
        self.delta_y = 1 if player_number == 1 else -1

    def add(self):
        if Entity.add(self):
            self.state.alien_factory = self

    def destroy(self):
        Entity.destroy(self)
        self.state.alien_factory = None
