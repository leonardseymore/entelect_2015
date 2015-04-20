# event base class
class Event():
    event_type = None
    payload = None

    # event_type and generic payload to avoid unnecessary base classes
    def __init__(self, event_type, payload=None):
        self.event_type = event_type
        self.payload = payload


# listeners where key = event_type
listeners = {}


# register object to handle event message of specified type
def register(event_type, obj):
    event_type_listeners = []
    if listeners.has_key(event_type):
        event_type_listeners = listeners[event_type]
    else:
        listeners[event_type] = event_type_listeners
    event_type_listeners.append(obj)


# unregister object from specified event type (None to remove from all)
def unregister(event_type, obj):
    if event_type:
        listeners[event_type].remove(obj)
    else:
        for key in listeners:
            listeners[key].remove(obj)


# dispatch event to interested listeners
def dispatch(event):
    for listener in listeners[event.event_type]:
        method = getattr(listener, 'handle_%s' % event.event_type)
        if method:
            method(event)
        else:
            listener.handle(event.event_type, event)
