'''
'''

import copy
import enum
import json
import os

from datatypes import VarInt, UnsignedInt64, DATA_TYPE_REGISTRY

class NoSuchFieldException(RuntimeError):
    pass


@enum.unique
class State(enum.Enum):
    '''This represents the different game states that our client can be in.'''

    HANDSHAKING = 'handshaking'
    LOGIN = 'login'
    PLAY = 'play'
    STATUS = 'status'


@enum.unique
class Direction(enum.Enum):
    '''The direction (to server, to client) that the packet is meant to go.'''

    TO_SERVER = 'toServer'
    TO_CLIENT = 'toClient'


class FieldManager:

    def __init__(self, parent):

        self.__dict__['parent'] = parent

    def __getattr__(self, name):

        for index, (field_name, field_type) in enumerate(self.parent.FIELDS):

            if field_name == name:

                return self.parent._values[index]

        raise AttributeError()

    def __setattr__(self, name, value):

        if name in self.__dict__:
            self.__dict__[name] = value
            return

        for index, (field_name, field_type) in enumerate(self.parent.FIELDS):

            if field_name == name:
                self.parent._values[index] = value
                return

        raise AttributeError()


# TODO create a context manager for Packe so that we can do:
#
# with PacketContext(packet : Packet, connection : Connection()) as fields:
#
#   fields.xyz = 1
#
# and then when it exits the context it sends the packet via the connection


class Packet:

    DIRECTION = None
    STATE = None
    NAME = None
    PACKET_ID = None
    FIELDS = [] # name, type

    _values = []
    fields = None

    def __init__(self):

        self.fields = FieldManager(self)

        # initialize values based on field type
        self._values = [DATA_TYPE_REGISTRY[field_type].default() for _, field_type in self.FIELDS]

    def to_wire(self):
        '''Return a binary representation of this packet - ready to be sent.'''

        data = bytearray()

        # packet ID [varint]
        data.extend(VarInt.to_wire(self.PACKET_ID))

        # serialize all the field values
        for (field_name, field_type), value in zip(self.FIELDS, self._values):

            data_type = None

            try:
                data_type = DATA_TYPE_REGISTRY[field_type]
            except KeyError:
                raise Exception('Unrecognized data type "{}". '
                                'Is it implemented?'.format(field_type))

            data.extend(data_type.to_wire(value))

        return data

    def from_wire(self, data, data_size):
        '''Parse data into object property values.'''

        offset = 0

        # serialize all the field values
        for value_index, (field_name, field_type) in enumerate(self.FIELDS):

            data_type = None

            try:
                data_type = DATA_TYPE_REGISTRY[field_type]
            except KeyError:
                raise Exception('Unrecognized data type "{}". '
                                'Is it implemented?'.format(field_type))

            value, bytes_consumed = data_type.from_wire(
                data, offset, data_size
            )

            self._values[value_index] = value

            offset += bytes_consumed


class PacketFactory:

    @classmethod
    def packet_name_to_classname(clz, name):

        return name.title().replace('_','') + 'Packet'

    def __init__(self, mcdata_base_dir, game_version):

        # [state][direction]([name] or [packet_id])
        self.lookup_map = {}

        base_path = os.path.join(mcdata_base_dir,
                                 'data',
                                 'pc',
                                 game_version)

        version_path = os.path.join(base_path, 'version.json')

        #
        # handle minecraft-data's "schema versioning" by looking up the
        # location of the protocol.json data via the majorVersion key.
        #

        version_data = None

        with open(version_path, 'r') as fin:

            version_data = json.load(fin)

        self.version = version_data['version']

        protocol_path = os.path.join(mcdata_base_dir,
                                     'data',
                                     'pc',
                                     version_data['majorVersion'],
                                     'protocol.json')

        data = None

        with open(protocol_path, 'r') as fin:

            data = json.load(fin)

        for state_name, directions in data.items():

            if state_name == 'types':
                continue

            state = State(state_name)

            for direction_name, types in directions.items():

                direction = Direction(direction_name)

                for _, packets in types.items():

                    packet_ids = {}

                    for name, packet_data in packets.items():

                        if name != 'packet':
                            continue

                        for packet_id, name in packet_data[1][0]['type'][1]['mappings'].items():

                            packet_ids[name] = int(packet_id, 16)

                    # process each packet
                    for name, packet_data in packets.items():

                        if name == 'packet':
                            continue

                        packet_name = name.replace('packet_', '')
                        packet_id = packet_ids[packet_name]

                        assert isinstance(packet_data, list)
                        assert len(packet_data) == 2
                        assert packet_data[0] == 'container'

                        # gather the packet fields (name and datatype)

                        fields = []

                        for item in packet_data[1]:

                            assert len(item) == 2

                            type_name = item['type']

                            if isinstance(type_name, list):
                                type_name = type_name[0]

                            fields.append((item['name'], type_name))

                        # now build the packet from the data we have

                        class_members = {
                            'DIRECTION': direction,
                            'STATE': state,
                            'NAME': packet_name,
                            'PACKET_ID': packet_id,
                            'FIELDS': fields,
                            '__doc__': ''   # TODO put something useful here
                        }

                        class_name = self.packet_name_to_classname(packet_name)
                        packet = type(class_name, (Packet, ), class_members)

                        self.lookup_map.setdefault(state, {}).setdefault(direction, {}).setdefault(packet_name, packet)
                        self.lookup_map[state][direction][packet_id] = packet

    def get_by_name(self, state: State, direction: Direction, name: str) -> Packet:

        return self.lookup_map[state][direction][name]

    def get_by_id(self, state: State, direction: Direction, packet_id: int) -> Packet:

        return self.lookup_map[state][direction][packet_id]
