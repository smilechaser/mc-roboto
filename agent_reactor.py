'''
'''

import threading
import time

from protocol import State, Direction
from facing import Facing
from atoms import Position, Velocity
from listener import Signal


class GameInfo:

    def __init__(self):

        self.entity_id = None
        self.game_mode = None
        self.dimension = None
        self.difficulty = None
        self.level_type = None


class ModelReactor:

    SECONDS_PER_GAME_TICK = 0.05

    def __init__(self, packet_factory, connection):

        self.factory = packet_factory
        self.connection = connection

        RESPONSE_PACKETS = (
            'client_command',
            'teleport_confirm',
            'flying',
            'position_look',
            'held_item_slot',
            'block_dig',
            'entity_action',
            'block_place'
        )

        for name in RESPONSE_PACKETS:

            prop_name = name + '_packet'

            packet = packet_factory.get_by_name(
                State.PLAY,
                Direction.TO_SERVER,
                name
            )

            setattr(self, prop_name, packet)

        self.dead = True
        self.respawn_timer = None

        self.facing = Facing()

        self.position = Position()
        self.velocity = Velocity()

        self.last_time = None
        self.tick_counter = 0

        self.game_info = GameInfo()

        self.dig_ticks_remaining = None

        self.responder_thread = threading.Thread(target=self.responder)
        self.respond = True

    def responder(self):
        '''This is the method that gets called in a separate thread.'''

        while self.respond:

            if self.last_time is not None:

                now = time.perf_counter()

                if (now - self.last_time) >= self.SECONDS_PER_GAME_TICK:

                    self.last_time = now
                    self.on_tick_local()

                    self.tick(self.last_time)

    def on_tick_local(self):

        if self.respawn_timer is not None:

            self.respawn_timer -= 1

            if self.respawn_timer <= 0:

                packet = self.client_command_packet()
                packet.fields.actionId = 0
                self.connection.send(packet)

                self.respawn_timer = None

            return

        if not self.velocity.stopped and self.tick_counter % 2 == 0:

            pkt = self.position_look_packet()
            pkt.fields.x = self.position.x + self.velocity.x
            pkt.fields.y = self.position.y + self.velocity.y
            pkt.fields.z = self.position.z + self.velocity.z
            pkt.fields.yaw = self.facing.yaw
            pkt.fields.pitch = self.facing.pitch
            pkt.fields.onGround = True

            self.connection.send(pkt)

            self.position.x += self.velocity.x
            self.position.y += self.velocity.y
            self.position.z += self.velocity.z

        if self.dig_ticks_remaining is not None:

            self.dig_ticks_remaining -= 1

            if self.dig_ticks_remaining == 0:

                self.dig_ticks_remaining = None

                dig = self.block_dig_packet()

                dig.fields.status = 2
                dig.fields.location.x = 0
                dig.fields.location.y = 0
                dig.fields.location.z = 0
                dig.fields.face = 0
                self.connection.send(dig)

        if self.tick_counter % 20 == 0:

            pkt = self.position_look_packet()
            pkt.fields.x = self.position.x
            pkt.fields.y = self.position.y
            pkt.fields.z = self.position.z
            pkt.fields.yaw = self.facing.yaw
            pkt.fields.pitch = self.facing.pitch
            pkt.fields.onGround = True
            self.connection.send(pkt)

        elif self.tick_counter % 1 == 0:

            pkt = self.flying_packet()
            pkt.fields.onGround = True
            self.connection.send(pkt)

    @Signal.emitter
    def tick(self):
        pass

    @Signal.packet_listener(State.PLAY, 'login')
    def on_player_login(self, packet):

        self.game_info.entity_id = packet.fields.entityId
        self.game_info.game_mode = packet.fields.gameMode
        self.game_info.dimension = packet.fields.dimension
        self.game_info.difficulty = packet.fields.difficulty
        self.game_info.level_type = packet.fields.levelType

    @Signal.packet_listener(State.PLAY, 'update_time')
    def on_update_time(self, packet):

        if self.last_time is None:
            self.responder_thread.start()
            self.last_time = time.perf_counter()

    @Signal.packet_listener(State.PLAY, 'update_health')
    def on_health(self, packet):

        print('on_health: {}, food: {}, saturation: {}'.format(
            packet.fields.health, packet.fields.food, packet.fields.foodSaturation)
        )

        if packet.fields.health > 0:
            self.dead = False
        else:
            self.dead = True
            self.respawn_timer = 20

    @Signal.packet_listener(State.PLAY, 'respawn')
    def on_respawn(self, packet):

        print('on_respawn')

        packet = self.client_command_packet()
        packet.fields.actionId = 0
        self.connection.send(packet)

    @Signal.packet_listener(State.PLAY, 'position')
    def on_position(self, packet):

        self.position.x = packet.fields.x
        self.position.y = packet.fields.y
        self.position.z = packet.fields.z

        print(
            'on_position, X: {}, Y: {}, Z: {}, '
            'Yaw: {}, Pitch: {}, teleport ID: {}'.format(
                packet.fields.x,
                packet.fields.y,
                packet.fields.z,
                packet.fields.yaw,
                packet.fields.pitch,
                packet.fields.teleportId
            )
        )

        self.do_stop()

        # TODO need to develop a "mixin architecture" that will allow us
        # to define packet behavior, i.e. to deal with things like the .flags
        # field of player-position-and-look

        teleport_id = packet.fields.teleportId

        tpc = self.teleport_confirm_packet()
        tpc.fields.teleportId = teleport_id
        self.connection.send(tpc)

    @Signal.emitter
    def stop(self):
        pass

    def do_stop(self):

        self.velocity.reset()
        self.stop()

    # TODO turn this into a property?
    def set_active_hotbar_slot(self, slot_num):

        his = self.held_item_slot_packet()
        his.fields.slotId = slot_num
        self.connection.send(his)

    def swap_hands(self):

        bd = self.block_dig_packet()

        bd.fields.status = 6
        bd.fields.location.x = 0
        bd.fields.location.y = 0
        bd.fields.location.z = 0
        bd.fields.face = 0
        self.connection.send(bd)

    def drop(self, all=False):

        bd = self.block_dig_packet()

        if all:
            bd.fields.status = 3
        else:
            bd.fields.status = 4

        bd.fields.location.x = 0
        bd.fields.location.y = 0
        bd.fields.location.z = 0
        bd.fields.face = 0

        self.connection.send(bd)

    def crouch(self):

        ea = self.entity_action_packet()

        ea.fields.entityId = self.game_info.entity_id
        # TODO are there constants for these in minecraft-data?
        ea.fields.actionId = 0
        ea.fields.jumpBoost = 0

        self.connection.send(ea)


    def stand(self):

        ea = self.entity_action_packet()

        ea.fields.entityId = self.game_info.entity_id
        # TODO are there constants for these in minecraft-data?
        ea.fields.actionId = 1
        ea.fields.jumpBoost = 0

        self.connection.send(ea)

    def dig(self, target_location):

        if self.dig_ticks_remaining is not None:
            return

        # start digging
        dig = self.block_dig_packet()

        dig.fields.status = 0
        dig.fields.location.x = target_location.x
        dig.fields.location.y = target_location.y
        dig.fields.location.z = target_location.z
        # TODO this isn't accurate...but does it need to be?
        dig.fields.face = 0

        self.connection.send(dig)

        # schedule a "stop digging" response
        # TODO can we figure out how long this should actually be? or can
        # we wait for a packet from the server and then stop?
        self.dig_ticks_remaining = 20

    def place_block(self, target_location):

        bp = self.block_place_packet()

        bp.fields.location.x = target_location.x
        bp.fields.location.y = target_location.y
        bp.fields.location.z = target_location.z

        # TODO fix this so that placing slabs, trap doors, etc. works
        # as expected
        bp.fields.direction = 0

        bp.fields.hand = 0

        bp.fields.cursorX = 0.5
        bp.fields.cursorY = 0.5
        bp.fields.cursorZ = 0.5

        self.connection.send(bp)
