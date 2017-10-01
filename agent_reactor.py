'''
'''

import threading
import time

from protocol import State, Direction
from facing import Facing
from atoms import Position, Velocity, Face
from observer import Emitter, Listener, Event
from packet_event import PacketEvent


class TickEvent(Event):
    pass


class StopEvent(Event):
    pass


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

        self.tick_emitter = Emitter(TickEvent)
        self.stop_emitter = Emitter(StopEvent)

        RESPONSE_PACKETS = ('client_command', 'teleport_confirm', 'flying',
                            'position_look', 'block_dig',
                            'entity_action', 'block_place', 'chat',
                            'use_entity')

        for name in RESPONSE_PACKETS:

            prop_name = name + '_packet'

            packet = packet_factory.get_by_name(State.PLAY,
                                                Direction.TO_SERVER, name)

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

        self.respond = True
        self.responder_thread = threading.Thread(target=self.responder)

        # map of (x,z) --> chunk data
        self.chunks = {}

    def stop(self):

        #TODO use a queue.Queue for this instead?
        self.respond = False

        if self.responder_thread.is_alive():
            self.responder_thread.join()

    def responder(self):
        '''This is the method that gets called in a separate thread.'''

        #TODO use a queue.Queue for this instead?
        while self.respond:

            if self.last_time is not None:

                now = time.perf_counter()

                if (now - self.last_time) >= self.SECONDS_PER_GAME_TICK:

                    self.last_time = now
                    self.on_tick_local()

                    self.tick_emitter()

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

    @Listener(PacketEvent, area=State.PLAY, key='login')
    def on_player_login(self, event):

        packet = event.packet

        self.game_info.entity_id = packet.fields.entityId
        self.game_info.game_mode = packet.fields.gameMode
        self.game_info.dimension = packet.fields.dimension
        self.game_info.difficulty = packet.fields.difficulty
        self.game_info.level_type = packet.fields.levelType

        settings = self.factory.get_by_name(State.PLAY, Direction.TO_SERVER,
                                            'settings')()

        settings.fields.locale = 'en_CA'
        settings.fields.viewDistance = 3
        settings.fields.chatFlags = 0
        settings.fields.chatColors = False
        settings.fields.skinParts = 0x7d
        settings.fields.mainHand = 0

        self.connection.send(settings)

    @Listener(PacketEvent, area=State.PLAY, key='update_time')
    def on_update_time(self, event):

        packet = event.packet

        if self.last_time is None:
            self.last_time = time.perf_counter()
            self.responder_thread.start()

    @Listener(PacketEvent, area=State.PLAY, key='update_health')
    def on_health(self, event):

        packet = event.packet

        print('on_health: {}, food: {}, saturation: {}'.format(
            packet.fields.health, packet.fields.food,
            packet.fields.foodSaturation))

        if packet.fields.health > 0:
            self.dead = False
        else:
            self.dead = True
            self.respawn_timer = 20

    @Listener(PacketEvent, area=State.PLAY, key='respawn')
    def on_respawn(self, event):

        packet = event.packet

        print('on_respawn')

        packet = self.client_command_packet()
        packet.fields.actionId = 0
        self.connection.send(packet)

    @Listener(PacketEvent, area=State.PLAY, key='position')
    def on_position(self, event):

        packet = event.packet

        self.position.x = packet.fields.x
        self.position.y = packet.fields.y
        self.position.z = packet.fields.z

        print('on_position, X: {}, Y: {}, Z: {}, '
              'Yaw: {}, Pitch: {}, teleport ID: {}'.format(
                  packet.fields.x, packet.fields.y, packet.fields.z,
                  packet.fields.yaw, packet.fields.pitch,
                  packet.fields.teleportId))

        self.do_stop()

        teleport_id = packet.fields.teleportId

        tpc = self.teleport_confirm_packet()
        tpc.fields.teleportId = teleport_id
        self.connection.send(tpc)

    @Listener(PacketEvent, area=State.PLAY, key='map_chunk')
    def on_map_chunk(self, event):

        packet = event.packet

        x, z = packet.fields.x, packet.fields.z

        self.chunks[(x, z)] = packet

    @Listener(PacketEvent, area=State.PLAY, key='unload_chunk')
    def on_unload_chunk(self, event):

        packet = event.packet

        x, z = packet.fields.chunkX, packet.fields.chunkZ

        self.chunks.pop((x, z), None)

    def do_stop(self):

        self.velocity.reset()
        self.stop_emitter()

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

    def place_block(self, target_location, face):

        assert isinstance(face, Face)

        bp = self.block_place_packet()

        bp.fields.location.x = target_location.x
        bp.fields.location.y = target_location.y
        bp.fields.location.z = target_location.z

        bp.fields.direction = face

        bp.fields.hand = 0

        bp.fields.cursorX = 0.5
        bp.fields.cursorY = 0.5
        bp.fields.cursorZ = 0.5

        self.connection.send(bp)

    def say(self, message, sender=None):

        # TODO for some reason this only seems to work if sender != None
        # TODO we should probably, by default, only chat with our "owner"

        chat = self.chat_packet()

        if sender != 'Server':
            chat.fields.message = "/msg {} {}".format(sender, message)
        else:
            chat.fields.message = message

        self.connection.send(chat)

    def use_entity(self, target_entity_id, hand):

        assert(hand in [0, 1])

        use_packet = self.use_entity_packet()

        use_packet.fields.target = target_entity_id
        use_packet.fields.mouse = 0 # 0=interact, 1=attack, 2=interact at
        use_packet.fields.hand = hand   # 0=main, 1=offhand

        self.connection.send(use_packet)

