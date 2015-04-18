import unittest
from ai.blackboard import Blackboard


class BlackboardTestCase(unittest.TestCase):
    base_blackboard = None
    test_key = None
    test_value = None

    def setUp(self):
        self.base_blackboard = Blackboard()
        self.test_key = 'test_key'
        self.test_value = 'test_value'
        self.base_blackboard.set(self.test_key, self.test_value)

    def test_blackboard(self):
        get_value = self.base_blackboard.get(self.test_key)
        self.assertEqual(self.test_value, get_value)

    def test_blackboard_shadow(self):
        child_blackboard = Blackboard(self.base_blackboard)
        shadow_value = 'modified_value'
        child_blackboard.set(self.test_key, shadow_value)
        get_shadow_value = child_blackboard.get(self.test_key)
        self.assertEqual(shadow_value, get_shadow_value)

    def test_blackboard_parent_scope(self):
        child_blackboard = Blackboard(self.base_blackboard)
        get_value = child_blackboard.get(self.test_key)
        self.assertEqual(self.test_value, get_value)