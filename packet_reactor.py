'''
'''

import enum

from wiring import Wiring
from protocol import State, Direction
from listener import Signal


class PacketReactorException(Exception):
    pass


class DisconnectException(PacketReactorException):
    pass


class KickedOutException(PacketReactorException):
    pass


class PacketReactor:

    class HandshakeState(enum.Enum):

        STATUS = 1
        PLAY = 2

    def __init__(self, packet_factory, connection):

        self.packet_factory = packet_factory
        self.connection = connection
        self.state = State.HANDSHAKING

        self.keep_alive_packet = packet_factory.get_by_name(
            State.PLAY,
            Direction.TO_SERVER,
            'keep_alive'
        )

        # wire ourselves...to ourselves...

        wiring = Wiring(self.packet_factory)

        with wiring as wire:
            wire(self).to(self)

    def login(self, username):

        handshake_pkt = self.packet_factory.get_by_name(
            State.HANDSHAKING,
            Direction.TO_SERVER,
            'set_protocol'
        )()

        handshake_pkt.fields.protocolVersion = self.packet_factory.version
        handshake_pkt.fields.serverHost = self.connection.server
        handshake_pkt.fields.serverPort = self.connection.port
        handshake_pkt.fields.nextState = self.HandshakeState.PLAY.value

        self.connection.send(handshake_pkt)

        self.state = State.LOGIN

        login_pkt = self.packet_factory.get_by_name(
            State.LOGIN,
            Direction.TO_SERVER,
            'login_start'
        )()

        login_pkt.fields.username = username
        self.connection.send(login_pkt)

    @Signal.receiver
    def on_packet(self, packet_id, packet_data, packet_length):

        self.stateful_packet(self.state, packet_id, packet_data, packet_length)

    @Signal.packet_emitter
    def stateful_packet(self, state, id, data, length):
        pass

    #
    # default handlers
    #
    @Signal.packet_listener(State.LOGIN, 'encryption_begin')
    def on_encryption_begin(self, packet):

        raise NotImplementedError(
            'Encryption (aka Online Mode) is not supported at this time.'
        )

    @Signal.packet_listener(State.LOGIN, 'success')
    def on_login(self, packet):

        print('LOGIN: Robot "{}:{}" has been logged in.'.format(
            packet.fields.username,
            packet.fields.uuid)
        )

        self.state = State.PLAY

    @Signal.packet_listener(State.LOGIN, 'disconnect')
    def on_disconnect(self, packet):

        raise DisconnectException(packet.reason)

    @Signal.packet_listener(State.LOGIN, 'compress')
    def on_compress(self, packet):

        self.connection.set_compression(packet.threshold)

    @Signal.packet_listener(State.PLAY, 'keep_alive')
    def on_keep_alive(self, packet):

        response = self.keep_alive_packet()
        response.fields.keepAliveId = packet.fields.keepAliveId
        self.connection.send(response)

    @Signal.packet_listener(State.PLAY, 'kick_disconnect')
    def on_kick_disconnect(self, packet):

        raise KickedOutException(packet.fields.reason)
