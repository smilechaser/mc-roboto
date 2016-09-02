'''
'''

import threading
import time

from protocol import State
from facing import Facing
from atoms import Position, Velocity
from responses import Responses
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

        #
        # responses
        #

        self.responses = Responses(self.factory)

        self.responses.add(State.PLAY, 'client_command')
        self.responses.add(State.PLAY, 'teleport_confirm')
        self.responses.add(State.PLAY, 'flying')
        self.responses.add(State.PLAY, 'position_look')
        self.responses.add(State.PLAY, 'held_item_slot')
        self.responses.add(State.PLAY, 'block_dig')
        self.responses.add(State.PLAY, 'entity_action')

        self.dead = True
        self.respawn_timer = None

        self.facing = Facing()

        self.position = Position()
        self.velocity = Velocity()

        self.last_time = None
        self.tick_counter = 0

        self.game_info = GameInfo()

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

                with self.responses.client_command as status:

                    status.actionId = 0

                    status.send(self.connection)

                self.respawn_timer = None

            return

        if not self.velocity.stopped and self.tick_counter % 2 == 0:

            with self.responses.position_look as pkt:

                pkt.x = self.position.x + self.velocity.x
                pkt.y = self.position.y + self.velocity.y
                pkt.z = self.position.z + self.velocity.z
                pkt.yaw = self.facing.yaw
                pkt.pitch = self.facing.pitch
                pkt.onGround = True

                pkt.send(self.connection)

            self.position.x += self.velocity.x
            self.position.y += self.velocity.y
            self.position.z += self.velocity.z

        if self.tick_counter % 20 == 0:

            with self.responses.position_look as pkt:

                pkt.x = self.position.x
                pkt.y = self.position.y
                pkt.z = self.position.z
                pkt.yaw = self.facing.yaw
                pkt.pitch = self.facing.pitch
                pkt.onGround = True

                pkt.send(self.connection)

        elif self.tick_counter % 1 == 0:

            with self.responses.flying as pkt:
                pkt.onGround = True

                pkt.send(self.connection)

    @Signal.emitter
    def tick(self):
        pass

    @Signal.packet_listener(State.PLAY, 'login')
    def on_player_login(self, packet):

        self.game_info.entity_id = packet.entityId
        self.game_info.game_mode = packet.gameMode
        self.game_info.dimension = packet.dimension
        self.game_info.difficulty = packet.difficulty
        self.game_info.level_type = packet.levelType

    @Signal.packet_listener(State.PLAY, 'update_time')
    def on_update_time(self, packet):

        if self.last_time is None:
            self.responder_thread.start()
            self.last_time = time.perf_counter()

    @Signal.packet_listener(State.PLAY, 'update_health')
    def on_health(self, packet):

        print('on_health: {}, food: {}, saturation: {}'.format(
            packet.health, packet.food, packet.foodSaturation)
        )

        if packet.health > 0:
            self.dead = False
        else:
            self.dead = True
            self.respawn_timer = 20

    @Signal.packet_listener(State.PLAY, 'respawn')
    def on_respawn(self, packet):

        print('on_respawn')

        with self.responses.client_command as status:
            status.actionId = 0

            status.send(self.connection)

    @Signal.packet_listener(State.PLAY, 'position')
    def on_position(self, packet):

        self.position.x = packet.x
        self.position.y = packet.y
        self.position.z = packet.z

        print(
            'on_position, X: {}, Y: {}, Z: {}, '
            'Yaw: {}, Pitch: {}, teleport ID: {}'.format(
                packet.x,
                packet.y,
                packet.z,
                packet.yaw,
                packet.pitch,
                packet.teleportId
            )
        )

        self.do_stop()

        # TODO need to develop a "mixin architecture" that will allow us
        # to define packet behavior, i.e. to deal with things like the .flags
        # field of player-position-and-look

        teleport_id = packet.teleportId

        with self.responses.teleport_confirm as tpc:

            tpc.teleportId = teleport_id

            tpc.send(self.connection)

    @Signal.emitter
    def stop(self):
        pass

    def do_stop(self):

        self.velocity.reset()
        self.stop()

    # TODO turn this into a property?
    def set_active_hotbar_slot(self, slot_num):

        with self.responses.held_item_slot as his:

            his.slotId = slot_num

            his.send(self.connection)

    def swap_hands(self):

        with self.responses.block_dig as bd:

            bd.status = 6
            bd.location.x = 0
            bd.location.y = 0
            bd.location.z = 0
            bd.face = 0

            bd.send(self.connection)

    def crouch(self):

        with self.responses.entity_action as ea:

            ea.entityId = self.game_info.entity_id

            # TODO are there constants for these in minecraft-data?
            ea.actionId = 0
            ea.jumpBoost = 0

            ea.send(self.connection)

    def stand(self):

        with self.responses.entity_action as ea:

            ea.entityId = self.game_info.entity_id

            # TODO are there constants for these in minecraft-data?
            ea.actionId = 1
            ea.jumpBoost = 0

            ea.send(self.connection)
