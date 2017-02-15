'''
'''

import os
import json

from protocol import State
from packet_reactor import PacketReactor
from protocol import PacketFactory
from connection import Connection
from agent_reactor import ModelReactor
from listener import Signal
from atoms import Position
from responses import Responses
from wiring import Wiring

from map_chunk import parse_chunk_data, ChunkManager

# DEBUG
import time

# TODO need the concept of a "commander" i.e. the entity
# that is authorized to give the bot commands. this ultimately may lead to
# categorizing commands according to privilege i.e. asking for bots
# position anyone can do, asking for materials certain trusted players might
# do, and telling them to do something destructive is for the very privileged

# TODO need to download blocks so we know when to fall ;)


class Config:

    MC_DATA_FOLDER = './minecraft-data/'
    PROTOCOL_VERSION = '1.11.2'

    SERVER = 'localhost'
    PORT = 25565


class Robot:

    def __init__(self, packet_factory, agent_reactor):

        self.factory = packet_factory
        self.connection = agent_reactor.connection
        self.model = agent_reactor

        self.responses = Responses(self.factory)

        self.responses.add(State.PLAY, 'chat')

        self.destination = None

        self.chunk_manager = ChunkManager()

        wiring = Wiring(self.factory)

        with wiring as wire:

            wire(self).to(self.model)
            wire(self).to(self)

    @Signal.receiver
    def on_tick(self, last_time):

        if self.destination is not None:

            distance_to_target = self.model.position.distance(self.destination)

            if distance_to_target <= 0.1:
                self.arrived()
                self.model.do_stop()
            else:

                self.model.velocity = self.model.position.impulse(self.destination)

#    @Signal.packet_listener(State.PLAY, 'map_chunk')
    def on_map_chunk(self, packet):

        # TODO for now just experiment with parsing the data - will need to
        # refactor it into its own "terrain reactor" or something

        #
        # convert packet.specifiedChunks from a bitmask to a list
        #

        specified_chunks = []

        bitMap = packet.bitMap
        mask = 0x1

        for n in range(0, 16):

            if mask & bitMap != 0:
                specified_chunks.append(n)

            mask = mask << 1

        print('--- chunk ---')

        # DEBUG
        start = time.process_time()

        parse_chunk_data(packet.x, packet.z, packet.groundUp, specified_chunks, packet.chunkData, packet.blockEntities,
                         self.chunk_manager, None)

        # DEBUG
        end = time.process_time()
        print('Elapsed: ', end-start)

        print('--- done ---')

#     @Signal.packet_listener(State.PLAY, 'unload_chunk')
    def on_unload_chunk(self, packet):

        self.chunk_manager.unload(packet.chunkX, packet.chunkZ)

    @Signal.packet_listener(State.PLAY, 'chat')
    def on_chat(self, packet):
        '''Ulitimately this needs to be refactored to be more comprehensive
        (not to mention robust) since this will be the robot's means
        of conversing with the world.

        For now though, we're using it as a way to send commands to it.

        ignored_topics = (
            # we get a chat.type.text when we receive an echo of what we said
            'chat.type.text',

            # ignore announcements
            'chat.type.announcement',

            # this is what we say
            'commands.message.display.outgoing',

            # multiplayer announcements
            'multiplayer.player.left',
            'multiplayer.player.joined',

            # this is when the server op types /me <action>
            'chat.type.emote'

            # when someone gets whacked
            'death.attack.mob'
            )
        '''

        data = json.loads(packet.message)

        translate = data['translate']

        if translate != 'commands.message.display.incoming':
            return

        sender = data['with'][0]['text']

        message = ''.join([x['text'] for x in data['with'][-1]['extra']])

        if message is None:
            return

        parts = message.split(' ')

        action = parts[0]
        args = parts[1:]

        if action == 'goto':
            # format: goto [~]x [~]y [~]z

            self.destination = Position.from_args(self.model.position, args)

            self.model.facing.at(self.model.position, self.destination)

            self.say('Heading to destination: {}'.format(self.destination), sender)

        elif action == 'stop':
            # format: stop

            self.model.do_stop()
            self.on_stop()

        elif action == 'look':
            # format: look [~]x [~]y [~]z

            target = Position.from_args(self.model.position, args)

            self.model.facing.at(self.model.position, target)

        elif action == 'crouch':
            # format: crouch

            self.model.crouch()

        elif action == 'stand':
            # format: stand

            self.model.stand()

        elif action == 'break':
            # format: break block at [~]x [~]y [~]z

            position = args[1:]

            target = Position.from_args(self.model.position, position)

            self.model.dig(target)

        elif action == 'place':
            # format: place at [~]x [~]y [~]z

            position = args[1:]

            target = Position.from_args(self.model.position, position)

            self.model.place_block(target)

        elif action == 'drop':
            # format: drop
            # format: drop n
            # format: drop all

            pass

        elif action == 'select':
            # format: select slot_num (0-8)

            slot = int(args[0])

            self.model.set_active_hotbar_slot(slot)

        elif action == 'swap':
            # format: swap

            self.model.swap_hands()

        else:

            self.say("Sorry, I don't understand.", sender)

    def say(self, message, sender=None):

        # TODO for some reason this only seems to work if sender != None
        # TODO we should probably, by default, only chat with our "owner"

        with self.responses.chat as chat:
            if sender != 'Server':
                chat.message = "/msg {} {}".format(sender, message)
            else:
                chat.message = message

            chat.send(self.connection)

    @Signal.receiver
    def on_stop(self):

        self.destination = None

        self.model.facing.pitch = 0.0

    @Signal.emitter
    def arrived(self):
        pass

    @Signal.receiver
    def on_arrived(self):

        self.model.facing.pitch = 0.0


def main():

    protocol_path = os.path.normpath(
        os.path.expanduser(
            Config.MC_DATA_FOLDER
        )
    )

    factory = PacketFactory(protocol_path, Config.PROTOCOL_VERSION)

    connection = Connection(Config.SERVER, Config.PORT)

    packet_reactor = PacketReactor(factory, connection)

    agent_reactor = ModelReactor(factory, connection)

    robot = Robot(factory, agent_reactor)

    wiring = Wiring(factory)

    with wiring as wire:

        wire(packet_reactor).to(connection)
        wire(agent_reactor).to(packet_reactor)
        wire(robot).to(packet_reactor)
        wire(robot).to(robot)

    connection.connect()

    packet_reactor.login('bobo')

    try:
        while True:
            connection.process()
    except:

        agent_reactor.respond = False

        raise

if __name__ == '__main__':

    main()
