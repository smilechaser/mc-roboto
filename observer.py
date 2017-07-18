'''
'''

from collections import OrderedDict
import functools
import inspect

from protocol import State, Direction


class Emitter:
    '''
    '''

    def __init__(self, event=None, area=None):

        self.listeners = OrderedDict()

        self._event_clz = Event if event is None else event

        self.area = area

    def subscribe(self, observer, key=None):

        self.listeners[key] = observer

    def bind(self, subscriber):

        # get all methods of subscriber
        methods = inspect.getmembers(subscriber, inspect.ismethod)

        # trim down the list to only those with our decorator attrib
        methods = [(name, method) for name, method in methods
                   if hasattr(method, Listener.DECORATOR_MARK)]

        # subscribe all of the ones that match our event type
        for method_name, method in methods:

            for listener in getattr(method, Listener.DECORATOR_MARK):

                event_clz = listener.event_clz
                key = listener.key
                area = listener.area

                if event_clz == self._event_clz and area == self.area:
                    self.subscribe(method, key=key)

    def __call__(self, key=None, **kwargs):

        for observer_key, observer in self.listeners.items():

            if observer_key != key:
                continue

            observer(self._event_clz(emitter=self, **kwargs))


class Listener:
    '''
    '''

    DECORATOR_MARK = 'Listeners'

    def __init__(self, event_clz, area=None, key=None):

        self.event_clz = event_clz
        self.area = area
        self.key = key

    def __call__(self, fn):

        if not hasattr(fn, self.DECORATOR_MARK):
            setattr(fn, self.DECORATOR_MARK, [])

        getattr(fn, self.DECORATOR_MARK).append(self)

        @functools.wraps(fn)
        def decorated(*args, **kwargs):
            fn(*args, **kwargs)

        return decorated


class Event:
    '''
    '''

    def __init__(self, emitter, **kwargs):

        self.emitter = emitter
        self.data = kwargs
