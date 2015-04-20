# expert base class
class Expert():
    name = None

    def __init__(self, name):
        self.name = name

    # modify blackboard as expert sees fit
    def run(self, blackboard):
        pass

# analyses game state and gets most important information
class ExpertFieldAnalyst(Expert):
    def __init__(self):
        Expert.__init__(self, 'FieldAnalyst')

    def run(self, blackboard):
        game_state = blackboard.get('game_state')
        you = game_state['Players'][0]
        enemy = game_state['Players'][1]
        your_ship = you['Ship']
        enemy_ship = enemy['Ship']
        blackboard.set('your_ship', {'X': your_ship['X'], 'Y': your_ship['Y']})
        blackboard.set('enemy_ship', {'X': enemy_ship['X'], 'Y': enemy_ship['Y']})
        blackboard.set('your_lives', you['Lives'])
        blackboard.set('enemy_lives', enemy['Lives'])

experts = [ExpertFieldAnalyst()]