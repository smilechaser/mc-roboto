import unittest

from observer import Emitter, Listener, Event


class MyEvent(Event):
    pass


class SpyObserver:
    def __init__(self):

        self.clear()

    def clear(self):
        self.events = []

    def on_no_listener(self, event):

        self.events.append(('on_no_listener', event))

    @Listener(Event)
    def on_basic(self, event):

        self.events.append(('on_basic', event))

    @Listener(Event, area='area_1')
    def on_area(self, event):

        self.events.append(('on_area', event))

    @Listener(Event, key='key_1')
    def on_key(self, event):

        self.events.append(('on_key', event))

    @Listener(Event, area='area_2', key='key_2')
    def on_both(self, event):

        self.events.append(('on_both', event))

    @Listener(MyEvent)
    def on_my_event(self, event):

        self.events.append(('on_my_event', event))


class TestSubscribe(unittest.TestCase):
    def test_subscribe_basic(self):

        emitter = Emitter()
        obs = SpyObserver()

        emitter.subscribe(obs.on_no_listener)

        emitter(index=1)

        self.assertEqual(len(obs.events), 1)
        self.assertEqual(obs.events[0][0], 'on_no_listener')

    def test_subscribe_key(self):
        '''Test subscription with a key - events with keys
        other than what we subscribed to must be filtered out.'''

        emitter = Emitter(area='area_1')
        obs = SpyObserver()

        emitter.subscribe(obs.on_basic, key='a')

        emitter(key='a', index=1)
        emitter(key='b', index=2)

        self.assertEqual(len(obs.events), 1)
        self.assertEqual(obs.events[0][0], 'on_basic')
        self.assertEqual(obs.events[0][1].data['index'], 1)


class TestBind(unittest.TestCase):
    def test_basic(self):

        emitter = Emitter()
        obs = SpyObserver()

        emitter.bind(obs)

        emitter(index=1)

        self.assertEqual(len(obs.events), 1)
        self.assertEqual(obs.events[0][0], 'on_basic')

    def test_key(self):

        emitter = Emitter()
        obs = SpyObserver()

        emitter.bind(obs)

        emitter(key='key_1', index=1)

        self.assertEqual(len(obs.events), 1)
        self.assertEqual(obs.events[0][0], 'on_key')

    def test_area(self):

        emitter = Emitter(area='area_1')
        obs = SpyObserver()

        emitter.bind(obs)

        emitter(index=1)

        self.assertEqual(len(obs.events), 1)
        self.assertEqual(obs.events[0][0], 'on_area')

    def test_both(self):

        emitter = Emitter(area='area_2')
        obs = SpyObserver()

        emitter.bind(obs)

        emitter(key='key_2', index=1)

        self.assertEqual(len(obs.events), 1)
        self.assertEqual(obs.events[0][0], 'on_both')

    def test_custom_event(self):

        emitter = Emitter(event=MyEvent)
        obs = SpyObserver()

        emitter.bind(obs)

        emitter(index=1)

        self.assertEqual(len(obs.events), 1)
        self.assertEqual(obs.events[0][0], 'on_my_event')
