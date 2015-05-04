from ai.entelect import *

class State:
    def __init__(self, round_number, round_limit, kills, lives, respawn_timer, missile_limit, wave_size,
                 ship, alien_factory, missile_controller, aliens_delta_x, aliens, shields, missiles, bullets):
        self.playing_field = [[None for x in range(PLAYING_FIELD_WIDTH)] for y in range(PLAYING_FIELD_HEIGHT)]
        self.width = PLAYING_FIELD_WIDTH
        self.height = PLAYING_FIELD_HEIGHT

        self.round_number = round_number
        self.round_limit = round_limit
        self.kills = kills
        self.lives = lives
        self.respawn_timer = respawn_timer
        self.missile_limit = missile_limit
        self.wave_size = wave_size
        self.aliens_delta_x = aliens_delta_x

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

        self.shields = []
        self.missiles = []
        self.bullets = []
        self.aliens = []

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

    @staticmethod
    def from_game_state(game_state):
        offset_x = 1
        offset_y = 12
        round_number = game_state['RoundNumber']
        round_limit = game_state['RoundLimit']
        you = game_state['Players'][0]
        enemy = game_state['Players'][1]
        kills = you['Kills']
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
        your_missile_controller = you['MissileController']
        missile_controller = None
        if your_missile_controller:
            missile_controller = MissileController(None, your_missile_controller['X'] - offset_x, your_missile_controller['Y'] - offset_y, 1)
        alien_man = enemy['AlienManager']
        aliens_delta_x = alien_man['DeltaX']
        aliens = []
        for wave in alien_man['Waves']:
            for enemy_alien in wave:
                aliens.append(Alien(None, enemy_alien['X'] - offset_x, enemy_alien['Y'] - offset_y, 2))
        game_map = game_state['Map']
        shields = []
        bullets = []
        missiles = []
        your_field_end_x = 17
        your_field_end_y = 25
        for row_index in range(offset_y, your_field_end_y):
            for column_index in range(offset_x, your_field_end_x):
                cell = game_map['Rows'][row_index][column_index]
                if not cell:
                    continue
                if cell['Type'] == SHIELD:
                    shields.append(Shield(None, cell['X'] - offset_x, cell['Y'] - offset_y, 1))
                elif cell['Type'] == BULLET:
                    shields.append(Bullet(None, cell['X'] - offset_x, cell['Y'] - offset_y, 2))
                elif cell['Type'] == MISSILE:
                    missiles.append(Missile(None, cell['X'] - offset_x, cell['Y'] - offset_y, cell['PlayerNumber']))
        return State(round_number, round_limit, kills, lives, respawn_timer, missile_limit, wave_size,
                     ship, alien_factory, missile_controller, aliens_delta_x, aliens, shields, missiles, bullets)

    def in_bounds(self, x, y):
        return 0 <= x < self.width and 0 <= y < self.height

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
            print 'Moved %s -> %d:%d' % (entity, x, y)
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
                self.playing_field[y][x] = entity
            elif action == 'remove':
                if self.in_bounds(x, y):
                    self.playing_field[y][x] = None
        return True

    def get_available_actions(self):
        ship = self.ship
        if not self.ship:
            return [NOTHING]

        actions = []
        if self.in_bounds(ship.x - 1, ship.y):
            actions.append(MOVE_LEFT)
        if self.in_bounds(ship.x + ship.width + 1, ship.y):
            actions.append(MOVE_RIGHT)
        if len(self.missiles) < self.missile_limit:
            actions.append(SHOOT)
        if self.lives > 0:
            if self.alien_factory:
                actions.append(BUILD_ALIEN_FACTORY)
            if self.missile_controller:
                actions.append(BUILD_MISSILE_CONTROLLER)
            actions.append(BUILD_SHIELD)
        actions.append(NOTHING)
        return actions

    def get_alien_bbox(self):
        bbox = {'top': -1, 'right': -1, 'bottom': -1, 'left': -1}
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
        return bbox

    def update(self, action):
        self.round_number += 1
        if self.round_number == 40:
            self.wave_size += 1

        # Update the alien commander to spawn new aliens and give aliens orders
        bbox = self.get_alien_bbox()
        spawn_x = 16
        spawn_y = 1
        if (bbox['right'], bbox['top']) == (spawn_x, spawn_y):
            for i in range(0, self.wave_size):
                Alien(self, spawn_x - (i * 3), spawn_y, 2).add()

        bbox = self.get_alien_bbox()
        delta_x = self.aliens_delta_x
        delta_y = 0
        if self.aliens_delta_x == -1:
            if bbox['left'] == 0:
                delta_x = 0
                delta_y = 1
                self.aliens_delta_x = 1
        if self.aliens_delta_x == 1:
            if bbox['right'] == self.width - 1:
                delta_x = 0
                delta_y = 1
                self.aliens_delta_x = -1
        for alien in self.aliens:
            alien.delta_x = delta_x
            alien.delta_y = delta_y

        # Update missiles, moving them forward
        for missile in self.missiles[:]:
            missile.update()

        # Update alien bullets, moving them forward
        for bullet in self.bullets[:]:
            bullet.update()

        # Update aliens, executing their move & shoot orders
        for alien in self.aliens[:]:
            alien.update()

        # Update ships, executing their orders
        if action == MOVE_LEFT:
            if self.ship:
                self.ship.perform_action(action)

        # Advance respawn timer and respawn ships if necessary.
        if self.respawn_timer > 0:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                Ship(self, self.width / 2, self.height - 2).add()

    def __str__(self):
        playing_field = self.playing_field
        text = ''
        for x in range(0, PLAYING_FIELD_WIDTH + 2):
            text += '+'
        text += '\n'
        for y in range(0, PLAYING_FIELD_HEIGHT):
            text += '+'
            for x in range(0, PLAYING_FIELD_WIDTH):
                entity = playing_field[y][x]
                if entity:
                    text += entity.symbol
                else:
                    text += ' '
            text += '+\n'
        for x in range(0, PLAYING_FIELD_WIDTH + 2):
            text += '+'
        text += '\n'
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

    def destroy(self):
        self.state.remove_entity(self)

    def add(self):
        return self.state.add_entity(self)

    def update(self):
        pass

    def handle_out_of_bounds(self, bottom):
        print 'Out of bounds %s' % self

    def handle_collision(self, other):
        print 'Collision %s -> %s' % (self, other)
        self.destroy()
        other.destroy()

    def __str__(self):
        return "%s@%d:%d" % (self.__class__.__name__, self.x, self.y)


class Shield(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, SHIELD, SHIELD_SYMBOL, 1, player_number)


class Alien(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, ALIEN, ALIEN_SYMBOL, 1, player_number)
        self.delta_y = -1 if player_number == 1 else 1
        self.delta_x = -1

    def update(self):
        self.state.move_entity(self, self.x + self.delta_x, self.y + self.delta_y)

    def add(self):
        if Entity.add(self):
            self.state.aliens.append(self)

    def destroy(self):
        Entity.destroy(self)
        if self in self.state.aliens:
            self.state.aliens.remove(self)

    def handle_collision(self, other):
        Entity.handle_collision(self, other)
        if other.entity_type == MISSILE and self.player_number != other.player_number:
            self.state.kills += 1
        elif other.entity_type == SHIELD:
            self.explode()

    def explode(self):
        pass # TODO: explode


class Bullet(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, BULLET, BULLET_SYMBOL, 1, player_number)
        self.delta_y = -1 if player_number == 1 else 1

    def update(self):
        self.state.move_entity(self, self.x, self.y + self.delta_y)

    def handle_out_of_bounds(self, bottom):
        Entity.handle_out_of_bounds(self, bottom)
        self.destroy()

    def add(self):
        if Entity.add(self):
            self.state.bullets.append(self)

    def destroy(self):
        Entity.destroy(self)
        if self in self.state.bullets:
            self.state.bullets.remove(self)


class Missile(Entity):
    def __init__(self, state, x, y, player_number):
        Entity.__init__(self, state, x, y, MISSILE, MISSILE_PLAYER1_SYMBOL if player_number == 1 else MISSILE_PLAYER2_SYMBOL, 1, player_number)
        self.delta_y = 1 if player_number == 1 else -1

    def update(self):
        self.state.move_entity(self, self.x, self.y + self.delta_y)

    def handle_out_of_bounds(self, bottom):
        Entity.handle_out_of_bounds(self, bottom)
        self.destroy()

    def handle_collision(self, other):
        Entity.handle_collision(self, other)
        if other.entity_type == ALIEN and self.player_number != other.player_number:
            self.state.kills += 1

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
            pass # TODO: build shield array


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
            self.state.wave_size += 1
            self.state.alien_factory = self

    def destroy(self):
        Entity.destroy(self)
        self.wave_size -= 1
        self.state.alien_factory = None
