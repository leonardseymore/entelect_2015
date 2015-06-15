import unittest
from ai.behavior import *


class TaskFail(Task):
    def run(self, blackboard=None):
        return False


class TaskSucceed(Task):
    def run(self, blackboard=None):
        return True


class TaskSucceedXTimes(Task):
    times_succeed = 0
    times_ran = 0

    def __init__(self, times_succeed, *children):
        Task.__init__(self, *children)
        self.times_succeed = times_succeed

    def run(self, blackboard=None):
        result = False
        if self.times_ran < self.times_succeed:
            result = True
        self.times_ran += 1
        return result


class TaskBlackboardSetValue(Task):
    def run(self, blackboard=None):
        blackboard.set('test_key', 'test_value')
        return True


class TaskBlackboardGetValue(Task):
    def run(self, blackboard=None):
        return blackboard.get('test_key') == 'test_value'


class BehaviorTestCase(unittest.TestCase):
    def test_children(self):
        child1 = Task()
        child2 = Task()
        child3 = Task()
        root = Task(child1, child2, child3)
        self.assertEqual(root.children[0], child1)
        self.assertEqual(root.children[1], child2)
        self.assertEqual(root.children[2], child3)

    def test_selector_fail(self):
        child_fail = TaskFail()
        selector = Selector(child_fail)
        result = selector.run()
        self.assertFalse(result)

    def test_selector_succeed(self):
        child_succeed = TaskSucceed()
        selector = Selector(child_succeed)
        result = selector.run()
        self.assertTrue(result)

    def test_sequence_fail(self):
        child_fail = TaskFail()
        sequence = Sequence(child_fail)
        result = sequence.run()
        self.assertFalse(result)

    def test_sequence_succeed(self):
        child_succeed = TaskSucceed()
        sequence = Sequence(child_succeed)
        result = sequence.run()
        self.assertTrue(result)

    def test_decorator_setup(self):
        child = Task()
        decorator = Decorator(child)
        self.assertEquals(child, decorator.child)

    def test_decorator_limit(self):
        run_limit = 5
        child = TaskSucceed()
        limit = Limit(child, run_limit)
        for i in xrange(0, 10):
            result = limit.run()
            if i < run_limit:
                self.assertTrue(result)
            else:
                self.assertFalse(result)

    def test_decorator_until_fail(self):
        run_times = 5
        child = TaskSucceedXTimes(run_times)
        until_fail = UntilFail(child)
        result = until_fail.run()
        self.assertTrue(result)

    def test_decorator_blackboard(self):
        root = BlackboardManager(TaskBlackboardGetValue())
        self.assertFalse(root.run())

        root = BlackboardManager(Sequence(TaskBlackboardSetValue(), TaskBlackboardGetValue()))
        self.assertTrue(root.run())
