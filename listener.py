'''
'''
import functools
import inspect


class SignalDecoratorCollisionException(Exception):
    pass


class Signal:

    SIGNATURE_STRING = 'signal_marker'

    @classmethod
    def packet_listener(clz, game_state, packet_name):

        def packet_listener_decorator(meth):

            if hasattr(meth, clz.SIGNATURE_STRING):
                raise SignalDecoratorCollisionException('A Signal decorator already exists.')

            set_signal_marker(meth, clz.PacketListener(game_state, packet_name))

            @functools.wraps(meth)
            def method_wrapper(*args, **kwargs):
                meth(*args, **kwargs)
            return method_wrapper

        return packet_listener_decorator

    @classmethod
    def packet_emitter(clz, meth):

        if hasattr(meth, clz.SIGNATURE_STRING):
            raise SignalDecoratorCollisionException('A Signal decorator already exists.')

        set_signal_marker(meth, clz.PacketEmitter())

        @functools.wraps(meth)
        def method_wrapper(*args, **kwargs):
            meth(*args, **kwargs)
        return method_wrapper

    @classmethod
    def emitter(clz, meth):

        if hasattr(meth, clz.SIGNATURE_STRING):
            raise SignalDecoratorCollisionException('A Signal decorator already exists.')

        set_signal_marker(meth, clz.Emitter())

        @functools.wraps(meth)
        def method_wrapper(*args, **kwargs):
            meth(*args, **kwargs)
        return method_wrapper

    @classmethod
    def receiver(clz, meth):

        if hasattr(meth, clz.SIGNATURE_STRING):
            raise SignalDecoratorCollisionException('A Signal decorator already exists.')

        set_signal_marker(meth, clz.Receiver())

        @functools.wraps(meth)
        def method_wrapper(*args, **kwargs):
            meth(*args, **kwargs)
        return method_wrapper

    class PacketListener:

        def __init__(self, game_state, packet_name):

            self.game_state = game_state
            self.packet_name = packet_name

    class PacketEmitter:
        pass

    class Emitter:
        pass

    class Receiver:
        pass


def gather_marked_methods(target):

    return [x for x in inspect.getmembers(target, inspect.ismethod) if hasattr(x[-1], Signal.SIGNATURE_STRING)]


def filter_marked_methods(methods, item_or_items):

    retval = []
    items = []

    if isinstance(item_or_items, (list, tuple)):
        items.extend(item_or_items)
    else:
        items.append(item_or_items)

    for method in methods:
        for item in items:

            marker = get_signal_marker(method[1])

            assert marker is not None

            if isinstance(marker, item):
                retval.append(method)

    return retval


def get_signal_marker(target):

    return getattr(target, Signal.SIGNATURE_STRING, None)


def set_signal_marker(target, data):

    setattr(target, Signal.SIGNATURE_STRING, data)
