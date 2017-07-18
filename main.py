'''
'''

import os
import json

from protocol import State, Direction
from packet_reactor import PacketReactor
from protocol import PacketFactory
from connection import Connection
from agent_reactor import ModelReactor, StopEvent, TickEvent
from atoms import Position, Face, Direction
from observer import Event, Listener
from packet_event import PacketEvent

from map_chunk import parse_chunk_data, ChunkManager


class Config:

    MC_DATA_FOLDER = './minecraft-data/'
    PROTOCOL_VERSION = '1.11.2'

    SERVER = 'localhost'
    PORT = 25565


class Robot:
    def __init__(self, packet_factory, agent_reactor):

        self.factory = packet_factory
        self.model = agent_reactor

        self.destination = None

        self.chunk_manager = ChunkManager()

    @Listener(TickEvent)
    def on_tick(self, event):

        if self.destination is not None:

            distance_to_target = self.model.position.distance(self.destination)

            if distance_to_target <= 0.1:
                self.model.facing.pitch = 0.0
                self.model.do_stop()
            else:

                self.model.velocity = self.model.position.impulse(
                    self.destination)

    @Listener(PacketEvent, area=State.PLAY, key='chat')
    def on_chat(self, event):
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

        packet = event.packet

        data = json.loads(packet.fields.message)

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

            self.model.say(
                'Heading to destination: {}'.format(self.destination), sender)

        elif action == 'move':
            # format: move Direction

            direction = Direction[args[0].upper()]

            self.destination = Position.from_args(self.model.position, direction.value)

        elif action == 'stop':
            # format: stop

            self.model.do_stop()

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
            # format: break [~]x [~]y [~]z

            target = Position.from_args(self.model.position, args)

            self.model.dig(target)

        elif action == 'place':
            # format: place [~]x [~]y [~]z face

            position, face = args[0:3], args[-1]

            face = Face[face.title()]

            target = Position.from_args(self.model.position, position)

            self.model.place_block(target, face)

        elif action == 'location':
            # format: location

            print('--- location ---')

            self.model.say('I am at {}'.format(self.model.position), sender)

        elif action == 'drop':
            # format: drop
            # format: drop all

            all = False

            if args:

                assert args[0] == 'all', 'Expected "all" but got "{}".'.format(
                    args)

                all = True

            self.model.drop(all)

        elif action == 'select':
            # format: select slot_num (0-8)

            slot = int(args[0])

            self.model.active_hotbar_slot = slot

        elif action == 'swap':
            # format: swap

            self.model.swap_hands()

        elif action == 'use':
            # format: use
            # format: use other

            hand = 0     # main hand

            if args:

                assert len(args) == 1 and args[0] == 'other', 'Expected "other" but got "{}".'.format(
                    args)

                hand = 1

            self.model.use(hand)

        else:

            self.model.say("Sorry, I don't understand.", sender)

    @Listener(StopEvent)
    def on_stop(self, event):

        self.destination = None
        self.model.facing.pitch = 0.0


def main():

    protocol_path = os.path.normpath(os.path.expanduser(Config.MC_DATA_FOLDER))

    factory = PacketFactory(protocol_path, Config.PROTOCOL_VERSION)
    connection = Connection(Config.SERVER, Config.PORT)
    packet_reactor = PacketReactor(factory, connection)
    agent_reactor = ModelReactor(factory, connection)
    robot = Robot(factory, agent_reactor)

    # connection
    connection.packet_emitter.bind(packet_reactor)

    # packet_reactor
    packet_reactor.play_state_emitter.bind(agent_reactor)
    packet_reactor.play_state_emitter.bind(robot)

    # agent_reactor
    agent_reactor.stop_emitter.bind(robot)
    agent_reactor.tick_emitter.bind(robot)

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
