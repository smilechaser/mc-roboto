'''
'''

from collections import OrderedDict, deque
import functools
import inspect

from protocol import State, Direction


class Emitter:
    '''
    '''

    def __init__(self, event=None, area=None, dispatcher=None):

        self.listeners = OrderedDict()

        self._event_clz = Event if event is None else event

        self._dispatcher = Dispatcher() if dispatcher is None else dispatcher

        self.area = area

    @property
    def dispatcher(self):
        return self._dispatcher

    @dispatcher.setter
    def dispatcher(self, new_dispatcher):

        self._dispatcher = new_dispatcher

    def subscribe(self, observer, key=None):

        self.listeners.setdefault(key, []).append(observer)

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

        event = self._event_clz(emitter=self, **kwargs)

        self._dispatcher.enqueue(emitter=self, event=event, key=key)

    def notify(self, event, key):

        for observer_key, observers in self.listeners.items():

            if observer_key != key:
                continue

            for observer in observers:
                observer(event)


class Dispatcher:
    '''
    '''

    def __init__(self):

        self.event_queue = deque()

    def enqueue(self, emitter, event, key=None):

        self.event_queue.append(
            (event, key)
        )

        # the default implementation dispatches right away
        self.dispatch(emitter)

    def dispatch(self, emitter, full=False):

        while True:

            event = key = None

            try:
                event, key = self.event_queue.popleft()
            except IndexError:
                break

            emitter.notify(event, key)

            if not full:
                break


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
