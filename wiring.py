'''
'''

from protocol import State, Direction
from listener import Signal, gather_marked_methods, filter_marked_methods, get_signal_marker


class Wiring:

    def __init__(self, packet_factory):

        self.packet_factory = packet_factory

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False

    def __call__(self, source):

        return Wire(self, source, self.packet_factory)


class Wire:

    def __init__(self, parent, source, packet_factory):

        self.parent = parent
        self.source = source
        self.packet_factory = packet_factory

    def to(self, target):

        self.resolve_emitters(target)

        emitters = self.gather_emitters(target)

        for name, handler in gather_marked_methods(self.source):

            for emitter in emitters:

                if emitter.subscribe(name, handler):
                    break

    @classmethod
    def gather_emitters(clz, target):

        retval = []

        for name in dir(target):

            if name.startswith('_'):
                continue

            obj = getattr(target, name)

            if isinstance(obj, (Observer, PacketObserver)):
                retval.append(obj)

        return retval

    def resolve_emitters(self, target):

        target_emitters = gather_marked_methods(target)

        for (kind, observer_clz) in (
            (Signal.Emitter, Observer),
            (Signal.PacketEmitter, PacketObserver)
        ):

            emitters = filter_marked_methods(target_emitters, kind)

            for name, old_method in emitters:

                observer = observer_clz(target, name, self)
                observer.old = old_method

                setattr(target, name, observer)


class Observer:

    def __init__(self, target, name, wire):

        self.target = target
        self.name = name
        self.listeners = []
        self.old = None

    def __repr__(self):

        return '{}.{}'.format(self.target, self.name)

    def subscribe(self, handler_name, handler):

        # only attach receivers to emitters if the handler's name
        #  corresponds to the emitter name i.e. on_<emitter_name>
        if 'on_{}'.format(self.name) != handler_name:
            return False

        if handler not in self.listeners:
            self.listeners.append(handler)

        return True

    def __call__(self, *args, **kwargs):

        for listener in self.listeners:
            listener(*args, **kwargs)


class PacketObserver(Observer):

    def __init__(self, target, name, wire):

        super().__init__(target, name, wire)

        self.listeners = {}

        self.packet_factory = wire.packet_factory

    def subscribe(self, handler_name, handler):

        signal_data = get_signal_marker(handler)

        if not isinstance(signal_data, Signal.PacketListener):
            return False

        state = signal_data.game_state
        packet_name = signal_data.packet_name

        assert isinstance(state, State), 'ASSERT: state must be of type State'

        packet = self.packet_factory.create_by_name(
            state,
            Direction.TO_CLIENT,
            packet_name
        )

        self.listeners.setdefault(state, {})[packet.packet_id] = \
            (packet, handler)

        return True

    def __call__(self, state, packet_id, packet_data, packet_length):

        packet, handler = self.listeners\
            .get(state, {})\
            .get(packet_id, (None, None))

        if handler:

            packet.clear()
            packet.hydrate(packet_data, packet_length)
            handler(packet)
