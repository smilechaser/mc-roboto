'''
'''

import enum

from wiring import Wiring
from protocol import State
from responses import Responses
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

        self.responses = Responses(self.packet_factory)

        self.responses.add(State.HANDSHAKING, 'set_protocol')
        self.responses.add(State.LOGIN, 'login_start')
        self.responses.add(State.PLAY, 'keep_alive')

        # wire ourselves...to ourselves...

        wiring = Wiring(self.packet_factory)

        with wiring as wire:

            wire(self).to(self)

    def login(self, username):

        with self.responses.set_protocol as handshake_pkt:

            handshake_pkt.protocolVersion = self.packet_factory.version
            handshake_pkt.serverHost = self.connection.server
            handshake_pkt.serverPort = self.connection.port
            handshake_pkt.nextState = self.HandshakeState.PLAY.value

            handshake_pkt.send(self.connection)

        self.state = State.LOGIN

        with self.responses.login_start as login_pkt:

            login_pkt.username = username

            login_pkt.send(self.connection)

    @Signal.receiver
    def on_packet(self, packet_id, packet_data, packet_length):

        self.stateful_packet(self.state, packet_id, packet_data, packet_length)

    @Signal.packet_emitter
    def stateful_packet(self, state, id, data, length):
        pass

    #
    # default handlers
    #
    #
    @Signal.packet_listener(State.LOGIN, 'encryption_begin')
    def on_encryption_begin(self, packet):

        raise NotImplementedError(
            'Encryption (aka Online Mode) is not supported at this time.'
        )

    @Signal.packet_listener(State.LOGIN, 'success')
    def on_login(self, packet):

        print('LOGIN: Robot "{}:{}" has been logged in.'.format(
            packet.username,
            packet.uuid)
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

        with self.responses.keep_alive as response:

            response.keepAliveId = packet.keepAliveId
            response.send(self.connection)

    @Signal.packet_listener(State.PLAY, 'kick_disconnect')
    def on_kick_disconnect(self, packet):

        raise KickedOutException(packet.reason)
