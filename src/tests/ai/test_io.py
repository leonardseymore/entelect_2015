__author__ = 'leonard'

import unittest
import ai.io
import os

class LoadMapTestCase(unittest.TestCase):
    def setUp(self):
        self.resources_dir = os.path.dirname(os.path.realpath(__file__)) + '/../resources/'

    def test_load_map(self):
        game_map = ai.io.load_map(self.resources_dir + 'map.txt')
        self.assertIsNotNone(game_map)

    def test_load_state(self):
        game_state = ai.io.load_map(self.resources_dir + 'state.json')
        self.assertIsNotNone(game_state)
