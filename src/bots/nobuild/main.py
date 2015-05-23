from bots.bot import *

game_state = load_state()
bot = BotNoBuild()
action = bot.get_action(load_state())
print 'Round: %d, Action:%s' % (game_state['RoundNumber'], action)
write_move(action)
