from blackboard import Blackboard


# a task is an abstract node in a behavior tree
class Task():
    # child tasks
    children = []

    def __init__(self):
        return

    # abstract method to be implemented
    def run(self, blackboard):
        return


# selector runs children until a child evals to true
class Selector(Task):
    def run(self, blackboard):
        for c in self.children:
            if c.run():
                return True
        return False


# sequence runs children until a child evals to false
class Sequence(Task):
    def run(self, blackboard):
        for c in self.children:
            if not c.run():
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
    runLimit = 0
    runSoFar = 0

    def run(self, blackboard):
        if self.runSoFar >= self.runLimit:
            return False
        self.runSoFar += 1
        return self.child.run()


# run a child task until it fails
class UntilFail(Decorator):
    def run(self, blackboard):
        while True:
            if not self.child.run():
                break
        return True


# flip the return value of task
class Inverter(Decorator):
    def run(self, blackboard):
        return not self.child.run()


# inject blackboard into child task
class BlackboardManager(Decorator):
    def run(self, blackboard):
        new_blackboard = Blackboard(blackboard)
        return self.child.run(new_blackboard)
