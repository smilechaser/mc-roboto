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

        self.parent = parent
        self.packet = packet

    def __enter__(self):

        self.packet.clear()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):

        return False

    def __setattr__(self, key, value):

        if key not in ('parent', 'packet'):

            setattr(self.packet, key, value)

        super().__setattr__(key, value)

    def send(self, connection):

        connection.send(self.packet)
