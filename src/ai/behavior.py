from blackboard import Blackboard


# a task is an abstract node in a behavior tree
class Task():
    # child tasks
    children = []

    def __init__(self, *children):
        self.children = children

    # abstract method to be implemented
    def run(self, blackboard=None):
        return


# selector runs children until a child evals to true
class Selector(Task):
    def run(self, blackboard=None):
        for c in self.children:
            if c.run(blackboard):
                return True
        return False


# sequence runs children until a child evals to false
class Sequence(Task):
    def run(self, blackboard=None):
        for c in self.children:
            if not c.run(blackboard):
                return False
        return True


# decorator conditionally executes child
class Decorator(Task):
    child = None

    def __init__(self, child):
        Task.__init__(self)
        self.child = child


# limit number of times task can be executed
class Limit(Decorator):
    run_limit = 0
    run_so_far = 0

    def __init__(self, child, run_limit):
        Decorator.__init__(self, child)
        self.run_limit = run_limit

    def run(self, blackboard=None):
        if self.run_so_far >= self.run_limit:
            return False
        self.run_so_far += 1
        return self.child.run(blackboard)


# run a child task until it fails
class UntilFail(Decorator):
    def run(self, blackboard=None):
        while True:
            if not self.child.run(blackboard):
                break
        return True


# flip the return value of task
class Inverter(Decorator):
    def run(self, blackboard=None):
        return not self.child.run(blackboard)


# inject blackboard into child task
class BlackboardManager(Decorator):
    def run(self, blackboard=None):
        new_blackboard = Blackboard(blackboard)
        return self.child.run(new_blackboard)
