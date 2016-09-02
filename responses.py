'''
'''

from protocol import Direction


class Responses:

    def __init__(self, factory):

        self.factory = factory

    def add(self, state, name):

        packet = self.factory.create_by_name(state, Direction.TO_SERVER, name)

        context = ResponseContext(self, packet)

        setattr(self, name, context)


class ResponseContext:

    def __init__(self, parent, packet):

        self.__dict__['parent'] = parent
        self.__dict__['packet'] = packet

    def __enter__(self):

        self.packet.clear()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        return False

    def __setattr__(self, key, value):

        if key in self.__dict__:
            super().__setattr__(key, value)
            return

        setattr(self.packet, key, value)

    def __getattr__(self, key):

        if key in self.__dict__:
            return self.__dict__[key]

        try:
            return getattr(self.__dict__['packet'], key)
        except AttributeError:
            raise

        raise AttributeError

    def send(self, connection):

        connection.send(self.packet)

    def dump(self):

        return self.packet.dump()
