__author__ = 'leonard'

import unittest
import ai.io
import os
from ai.hash import *

class LoadMapTestCase(unittest.TestCase):
    def setUp(self):
        self.resources_dir = os.path.dirname(os.path.realpath(__file__)) + '/../resources/'

    def test_hash_game_state(self):
        game_state = ai.io.load_state(self.resources_dir + 'state.json')
        self.assertIsNotNone(game_state)
        game_state_hash = hash_game_state(game_state)
        print(game_state_hash)
