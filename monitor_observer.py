'''
'''

import os
import json

from protocol import State, Direction
from observer import Listener
from raw_packet_event import RawPacketEvent
from state_event import StateChangeEvent


class AnalyticsReactor:

    def __init__(self, packet_factory):

        self.factory = packet_factory
        self.state = State.HANDSHAKING

    @Listener(StateChangeEvent)
    def on_state_change(self, event):

        self.state = event.new_state

    @Listener(RawPacketEvent)
    def on_raw_packet(self, event):

        packet_clz = self.factory.get_by_id(
            self.state, Direction.TO_CLIENT, event.packet_id)

        # TODO do something here (other than printing - that's too slow)
