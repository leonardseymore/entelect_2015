from ai.bot import *
import cProfile
import pstats
import logging
import logging.config
import StringIO
import sys
import time
import yaml

module_logger = logging.getLogger('main')


class Main:
    def __init__(self, argv):

        self.bot = None
        if len(argv) > 0:
            self.bot = argv[0]
        self.profiler = None

        with open('bot.yml', 'r') as config_file:
            self.config = yaml.load(config_file.read())

    def start_profiler(self):
        self.profiler = cProfile.Profile()
        self.profiler.enable()

    def stop_profiler(self):
        self.profiler.disable()
        s = StringIO.StringIO()
        sort_by = 'cumulative'
        ps = pstats.Stats(self.profiler, stream=s).sort_stats(sort_by)
        ps.print_stats()
        return s.getvalue()

    def run(self):
        start = time.time()
        logging.config.fileConfig('logging.conf')
        module_logger.debug('Using configuration: %s', self.config)

        if self.config['profile']:
            self.start_profiler()

        game_state = load_state()
        bot = BotHaywired()
        if self.bot:
            bot = BOTS[self.bot]
        action = bot.get_action(game_state)

        write_move(action)
        if self.config['profile']:
            print self.stop_profiler()
        print 'Bot: %s, Round: %d, Action:%s in %.3f seconds' % \
              (bot.name, game_state['RoundNumber'], action, time.time() - start)

if __name__ == "__main__":
    Main(sys.argv[1:]).run()
