'''
'''

import os
import json

from protocol import State
from packet_reactor import PacketReactor
from protocol import PacketFactory
from connection import Connection
from model_reactor import ModelReactor
from listener import Signal
from atoms import Position
from responses import Responses
from wiring import Wiring

# TODO need the concept of a "commander" i.e. the entity
# that is authorized to give the bot commands. this ultimately may lead to
# categorizing commands according to privilege i.e. asking for bots
# position anyone can do, asking for materials certain trusted players might
# do, and telling them to do something destructive is for the very privileged

# TODO need to download blocks so we know when to fall ;)


class Config:

    MC_DATA_FOLDER = '~/projects/minecraft-data/'
    PROTOCOL_VERSION = '1.9.2'

    SERVER = 'localhost'
    PORT = 25565


class Robot:

    def __init__(self, packet_factory, model_reactor):

        self.factory = packet_factory
        self.connection = model_reactor.connection
        self.model = model_reactor

        self.responses = Responses(self.factory)

        self.responses.add(State.PLAY, 'chat')

        self.destination = None

        wiring = Wiring(self.factory)

        with wiring as wire:

            wire(self).to(self.model)
            wire(self).to(self)

    @Signal.receiver
    def on_tick(self):

        if self.destination is not None:

            distance_to_target = self.model.position.distance(self.destination)

            if distance_to_target <= 0.5:
                self.model.do_stop()
                self.arrived()
            else:

                self.model.velocity = self.model.position.impulse(self.destination)

    # self.reactor.subscribe(State.PLAY, 'chat', self.on_chat)
    @Signal.packet_listener(State.PLAY, 'chat')
    def on_chat(self, packet):

        '''
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

        if message is not None:

            parts = message.split(' ')

            action = parts[0]
            args = parts[1:]

            if action == 'goto':

                self.destination = Position.from_args(self.model.position, args)

                self.model.facing.at(self.model.position, self.destination)

                with self.responses.chat as chat:
                    msg = 'Heading to destination: {}'.format(self.destination)
                    if sender != 'Server':
                        chat.message = "/msg {} {}".format(sender, msg)
                    else:
                        chat.message = msg

                    chat.send(self.connection)

            elif action == 'stop':

                self.model.do_stop()
                self.on_stop()

            elif action == 'look':

                target = Position.from_args(self.model.position, args)

                self.model.facing.at(self.model.position, target)

            elif action == 'break':

                pass

            elif action == 'place':

                pass

            else:

                with self.responses.chat as chat:
                    msg = "Sorry, I don't understand."
                    if sender != 'Server':
                        chat.message = "/msg {} {}".format(sender, msg)
                    else:
                        chat.message = msg

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

    model_reactor = ModelReactor(factory, connection)

    robot = Robot(factory, model_reactor)

    wiring = Wiring(factory)

    with wiring as wire:

        wire(packet_reactor).to(connection)
        wire(model_reactor).to(packet_reactor)
        wire(robot).to(packet_reactor)
        wire(robot).to(robot)

    connection.connect()

    packet_reactor.login('bobo')

    try:
        while True:
            connection.process()
    except:

        model_reactor.respond = False

        raise

if __name__ == '__main__':

    main()
