from ai.entelect import *
import ai.movement

# expert base class
class Expert():
    name = None

    def __init__(self, name):
        self.name = name

    # modify blackboard as expert sees fit
    def run(self, blackboard):
        pass

# analyses game state and gets most important information
class FieldAnalystExpert(Expert):
    def __init__(self):
        Expert.__init__(self, 'Field Analyst Expert')

    def run(self, blackboard):
        game_state = blackboard.get('game_state')
        self.set_player_info(game_state, blackboard, 0)
        self.set_player_info(game_state, blackboard, 1)

    def set_player_info(self, game_state, blackboard, player_index):
        player_context = 'your' if player_index == 0 else 'enemy'
        player = game_state['Players'][player_index]

        # basic props
        blackboard.set('round_number', game_state['RoundNumber'])
        blackboard.set('rounds_remaining', game_state['RoundLimit'] - game_state['RoundNumber'])
        blackboard.set('%s_lives' % player_context, player['Lives'])
        blackboard.set('%s_kills' % player_context, player['Kills'])
        blackboard.set('%s_alien_wave_size' % player_context, player['AlienWaveSize'])
        blackboard.set('%s_missile_limit' % player_context, player['MissileLimit'])
        blackboard.set('%s_respawn_timer' % player_context, player['RespawnTimer'])
        blackboard.set('%s_respawn_timer' % player_context, player['RespawnTimer'])

        alien_manager = player['AlienManager']
        blackboard.set('%s_alien_direction' % player_context, 'left' if alien_manager['DeltaX'] == -1 else 'right')
        blackboard.set('%s_alien_shot_energy_cost' % player_context, alien_manager['ShotEnergyCost'])
        blackboard.set('%s_alien_shot_energy' % player_context, alien_manager['ShotEnergy'])

        # nullable object
        ship = player['Ship']
        if ship:
            blackboard.set('%s_ship' % player_context, {'X': ship['X'], 'Y': ship['Y']})
        else:
            blackboard.set('%s_ship' % player_context, None)

        alien_factory = player['AlienFactory']
        blackboard.set('%s_alien_factory_built' % player_context, alien_factory is not None)
        if alien_factory:
            blackboard.set('%s_alien_factory_pos' % player_context, {'X': alien_factory['X'], 'Y': alien_factory['Y']})
        else:
            blackboard.set('%s_alien_factory_pos' % player_context, None)

        game_map = game_state['Map']
        # complex entries

        alien_bbox = {'top': -1, 'right': -1, 'bottom': -1, 'left': -1}
        if game_state['RoundNumber'] == 0:
            if player_context == 'enemy':
                alien_bbox['top'] = YOUR_SPAWN_LOCATION[1]
                alien_bbox['right'] = MAP_RIGHT
                alien_bbox['bottom'] = YOUR_SPAWN_LOCATION[1]
                alien_bbox['left'] = MAP_RIGHT - wave_size_to_bbox_width(INITIAL_ALIEN_WAVE_SIZE) + 1
            else:
                alien_bbox['top'] = ENEMY_SPAWN_LOCATION[1]
                alien_bbox['right'] = MAP_RIGHT
                alien_bbox['bottom'] = ENEMY_SPAWN_LOCATION[1]
                alien_bbox['left'] = MAP_RIGHT - wave_size_to_bbox_width(INITIAL_ALIEN_WAVE_SIZE) + 1
        else:
            start_row = 0 if player_index == 0 else MAP_HEIGHT / 2
            end_row = MAP_HEIGHT / 2 if player_index == 0 else MAP_HEIGHT
            for row_index in range(start_row, end_row):
                for column_index in range(0, MAP_WIDTH):
                    cell = game_map['Rows'][row_index][column_index]
                    if not cell:
                        continue
    
                    if cell['Type'] == ALIEN:
                        if alien_bbox['top'] == -1:
                            alien_bbox['top'] = row_index
                        if alien_bbox['bottom'] == -1 or alien_bbox['bottom'] < row_index:
                            alien_bbox['bottom'] = row_index
                        if alien_bbox['left'] == -1 or alien_bbox['left'] > column_index:
                            alien_bbox['left'] = column_index
                        if alien_bbox['right'] == -1 or alien_bbox['right'] < column_index:
                            alien_bbox['right'] = column_index
        blackboard.set('%s_alien_bbox' % player_context, alien_bbox)

# expert in alien movement prediction
# depends on Field Analyst Expert
class AlienExpert(Expert):
    def __init__(self):
        Expert.__init__(self, 'Alien Expert')

    def run(self, blackboard):
        blackboard.set('your_bbox_predictions', ai.movement.predict_bbox(blackboard, 'your', blackboard.get('rounds_remaining')))
        blackboard.set('enemy_bbox_predictions', ai.movement.predict_bbox(blackboard, 'enemy', blackboard.get('rounds_remaining')))


field_analyst = FieldAnalystExpert()
alien_expert = AlienExpert()
experts = {'field_analyst': field_analyst, 'alien': alien_expert}