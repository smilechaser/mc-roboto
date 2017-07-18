'''
'''

import enum

from protocol import State, Direction
from observer import Emitter, Listener
from packet_event import PacketEvent
from raw_packet_event import RawPacketEvent


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

        self._state = State.HANDSHAKING

        self.keep_alive_packet = packet_factory.get_by_name(
            State.PLAY, Direction.TO_SERVER, 'keep_alive')

        self.play_state_emitter = Emitter(PacketEvent, area=State.PLAY)
        self.login_state_emitter = Emitter(PacketEvent, area=State.LOGIN)
        self.handshake_state_emitter = Emitter(
            PacketEvent, area=State.HANDSHAKING)

        self.play_state_emitter.bind(self)
        self.login_state_emitter.bind(self)
        self.handshake_state_emitter.bind(self)

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, new_state):

        print('State transition {} --> {}'.format(self._state, new_state))

        self._state = new_state

    @Listener(RawPacketEvent)
    def on_raw_packet(self, event):

        # print('on_raw_packet (state={}, packet_id={})'.format(self.state, event.packet_id))

        packet_clz = self.packet_factory.get_by_id(
            self.state, Direction.TO_CLIENT, event.packet_id)

        # TODO need to handle packets with 'switch' field types
        for name, xtype in packet_clz.FIELDS:

            if xtype == 'switch':
                print('Skipping packet "{}" w/ switch field.'.format(
                    packet_clz.NAME))
                return

        packet = packet_clz()
        packet.from_wire(event.data, event.length)

        if self._state == State.PLAY:

            self.play_state_emitter(key=packet.NAME, packet=packet)

        elif self._state == State.LOGIN:

            self.login_state_emitter(key=packet.NAME, packet=packet)

        elif self._state == State.HANDSHAKING:

            self.handshake_state_emitter(key=packet.NAME, packet=packet)

    def login(self, username):

        handshake_pkt = self.packet_factory.get_by_name(
            State.HANDSHAKING, Direction.TO_SERVER, 'set_protocol')()

        handshake_pkt.fields.protocolVersion = self.packet_factory.version
        handshake_pkt.fields.serverHost = self.connection.server
        handshake_pkt.fields.serverPort = self.connection.port
        handshake_pkt.fields.nextState = self.HandshakeState.PLAY.value

        self.connection.send(handshake_pkt)

        self.state = State.LOGIN

        login_pkt = self.packet_factory.get_by_name(
            State.LOGIN, Direction.TO_SERVER, 'login_start')()

        login_pkt.fields.username = username
        self.connection.send(login_pkt)

    #
    # default handlers
    #
    @Listener(PacketEvent, State.LOGIN, key='encryption_begin')
    def on_encryption_begin(self, packet):

        raise NotImplementedError(
            'Encryption (aka Online Mode) is not supported at this time.')

    @Listener(PacketEvent, State.LOGIN, key='success')
    def on_login(self, event):

        packet = event.packet

        print('LOGIN: Robot "{}:{}" has been logged in.'.format(
            packet.fields.username, packet.fields.uuid))

        self.state = State.PLAY

    @Listener(PacketEvent, State.LOGIN, key='disconnect')
    def on_disconnect(self, packet):

        raise DisconnectException(packet.reason)

    @Listener(PacketEvent, State.LOGIN, key='compress')
    def on_compress(self, event):

        packet = event.packet

        self.connection.set_compression(packet.threshold)

    @Listener(PacketEvent, State.PLAY, key='keep_alive')
    def on_keep_alive(self, event):

        packet = event.packet

        response = self.keep_alive_packet()
        response.fields.keepAliveId = packet.fields.keepAliveId
        self.connection.send(response)

    @Listener(PacketEvent, State.PLAY, key='kick_disconnect')
    def on_kick_disconnect(self, event):

        raise KickedOutException(event.packet.fields.reason)
