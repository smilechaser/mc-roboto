'''
'''

import os
import enum
import json

from datatypes import VarInt, DATA_TYPE_REGISTRY


@enum.unique
class State(enum.Enum):

    HANDSHAKING = 'handshaking'
    LOGIN = 'login'
    PLAY = 'play'
    STATUS = 'status'


@enum.unique
class Direction(enum.Enum):

    TO_SERVER = 'toServer'
    TO_CLIENT = 'toClient'


class FieldManager:

    def __init__(self):

        self.fields = {}
        self.field_order = []

    def add(self, name, type):

        self.field_order.append(name)

        self.fields[name] = type


class Packet:

    def __init__(self, name, packet_id):

        assert isinstance(packet_id, int), \
            'Expecting packet_id as int but got "{}".'\
            .format(type(packet_id).__name__)

        self.__dict__['name'] = name
        self.__dict__['packet_id'] = packet_id
        self.__dict__['fields'] = FieldManager()

        self.clear()

    def clear(self):

        self.__dict__['values'] = {}
        self.__dict__['resolved'] = False
        self.__dict__['data'] = None
        self.__dict__['data_size'] = None

        return self

    def __getattr__(self, key):

        if key in self.__dict__:
            return self.__dict__[key]

        # if this is a field we need to resolve our values
        if key in self.fields.fields and not self.resolved:
            self.resolve()

        if key in self.values:
            return self.values[key]

        raise AttributeError("'{}' object has no attribute "
                             "'{}'".format(self.__class__.__name__, key))

    def __setattr__(self, key, value):

        if key in self.__dict__:
            self.__dict__[key] = value
            return

        if key not in self.__dict__['fields'].fields:
            raise AttributeError("'{}' object has no attribute "
                                 "'{}'".format(self.__class__.__name__, key))

        self.__dict__['values'][key] = value

    def render(self):

        # TODO this does not handle encryption

        data = bytearray()

        # packet ID [varint]
        data.extend(VarInt.to_wire(self.packet_id))

        for field_name in self.fields.field_order:

            data_type_name = self.fields.fields[field_name]

            data_type = None

            try:
                data_type = DATA_TYPE_REGISTRY[data_type_name]
            except KeyError:
                raise Exception('Unrecognized data type "{}". '
                                'Is it implemented?'.format(data_type_name))

            data.extend(data_type.to_wire(self.values[field_name]))

        return data

    def resolve(self):
        '''Parse data into object propery values.'''

        offset = 0

        for field_name in self.fields.field_order:

            data_type_name = self.fields.fields[field_name]

            data_type = None

            try:
                data_type = DATA_TYPE_REGISTRY[data_type_name]
            except KeyError:
                raise Exception('Unrecognized data type "{}". '
                                'Is it implemented?'.format(data_type_name))

            value, bytes_consumed = data_type.from_wire(
                self.data, offset, self.data_size
            )

            offset += bytes_consumed

            self.values[field_name] = value

        self.resolved = True

    def hydrate(self, data, data_size):

        self.data = data
        self.data_size = data_size


class PacketFactory:

    def __init__(self, mcdata_base_dir, game_version):

        base_path = os.path.join(mcdata_base_dir,
                                 'data',
                                 'pc',
                                 game_version)

        protocol_path = os.path.join(base_path, 'protocol.json')
        version_path = os.path.join(base_path, 'version.json')

        self.name_packet_map = {}
        self.id_packet_map = {}

        data = json.load(open(protocol_path, 'r'))

        for state, directions in data.items():

            if state == 'types':
                continue

            state_enum = State(state)

            for direction, types in directions.items():

                direction_enum = Direction(direction)

                for _, packets in types.items():

                    # this is packetID --> name
                    packet_id_mappings = data[state][direction]['types']['packet'][1][0]['type'][1]['mappings']  # NOQA

                    # reverse it so we have name --> packetID
                    packet_id_mappings = \
                        {v: int(k, 16) for k, v in packet_id_mappings.items()}

                    # process each packet
                    for name, packet_data in packets.items():

                        if name == 'packet':
                            continue

                        name = name.replace('packet_', '')

                        packet_id = packet_id_mappings[name]

                        packet = PacketTemplate.load(
                            state_enum,
                            direction_enum,
                            name,
                            packet_id,
                            packet_data
                        )

                        self.name_packet_map \
                            .setdefault(state_enum, {}) \
                            .setdefault(direction_enum, {}) \
                            .setdefault(name, packet)

                        # update the map of packet_id --> packet
                        self.id_packet_map \
                            .setdefault(state_enum, {}) \
                            .setdefault(direction_enum, {}) \
                            .setdefault(packet_id, packet)

        data = json.load(open(version_path, 'r'))

        self.version = data['version']

    def create_by_name(self, state, direction, name):

        template = self.name_packet_map[state][direction][name]

        return template.create()

    def create_by_id(self, state, direction, packet_id):

        template = self.id_packet_map[state][direction][packet_id]

        return template.create()


class PacketTemplate:

    def __init__(self):

        self.state = None
        self.direction = None
        self.packet_id = None
        self.name = None
        self.fields = None

    @classmethod
    def load(clz, state, direction, name, packet_id, data):

        packet = PacketTemplate()

        packet.state = state
        packet.direction = direction
        packet.name = name
        packet.packet_id = packet_id

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0] == 'container'

        packet.fields = []

        for item in data[1]:

            assert len(item) == 2

            field = Field.load(item)

            packet.fields.append(field)

        return packet

    def create(self):

        new_packet = Packet(self.name, self.packet_id)

        for field in self.fields:

            new_packet.fields.add(field.name, field.type.name)

        return new_packet

    @property
    def pprint_data(self):

        return {
            'state': self.state,
            'direction': self.direction,
            'packet_id': self.packet_id,
            'name': self.name,
            'fields': [x.pprint_data for x in self.fields]
        }


class Field:

    def __init__(self):

        self.name = None
        self.type = None

    @classmethod
    def load(clz, data):

        field = Field()

        field.name = data['name']

        field.type = FieldType.load(data['type'])

        return field

    @property
    def pprint_data(self):

        return (self.name, self.type.pprint_data)


class FieldType:

    def __init__(self):

        self.name = None

    @classmethod
    def load(clz, data):

        obj = clz()

        if isinstance(data, list):
            obj.name = data[0]
        else:
            obj.name = data

        return obj

    @property
    def pprint_data(self):

        return {
            'style': self.name
        }
