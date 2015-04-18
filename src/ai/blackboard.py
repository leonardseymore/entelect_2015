# blackboard to share game facts across different systems
class Blackboard():
    # parent scope
    parent = None
    data = {}

    def __init__(self, parent=None):
        self.parent = parent

    def set(self, key, value):
        self.data[key] = value

    # gets a value recursively up the blackboard hierarchy
    def get(self, key):
        if key in self.data:
            return self.data[key]
        elif self.parent:
            return self.parent.get(key)
        else:
            return None