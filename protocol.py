'''
'''

import copy
import enum
import json
import os

from datatypes import VarInt, UnsignedInt64, DATA_TYPE_REGISTRY

# TODO we need a base class for exceptions defined by this library


class NoSuchFieldException(RuntimeError):
    pass


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


class Packet:

    def __init__(self, name, packet_id):

        assert isinstance(packet_id, int), \
            'Expecting packet_id as int but got "{}".'\
            .format(type(packet_id).__name__)

        self.__dict__['name'] = name
        self.__dict__['packet_id'] = packet_id
        self.__dict__['fields'] = FieldManager()
        self.__dict__['resolved'] = False

        self.clear()

    def clear(self):

        self.__dict__['resolved'] = False
        self.__dict__['data'] = None
        self.__dict__['data_size'] = None
        self.__dict__['fields'].clear()

        return self

    def __getattr__(self, key):

        if key in self.__dict__:
            return self.__dict__[key]

        # try to delegate to FieldManager
        try:

            # automagically trigger resolve
            if not self.resolved and self.data is not None:
                self.resolve()

            return self.fields.get_field_value(key)

        except NoSuchFieldException:
            pass

        raise AttributeError("'{}' object has no attribute (or field) "
                             "'{}'".format(self.__class__.__name__, key))

    def __setattr__(self, key, value):

        if key in self.__dict__:
            self.__dict__[key] = value
            return

        # try to delegate to FieldManager
        try:
            self.fields.set_field_value(key, value)
            return
        except NoSuchFieldException:
            pass

        raise AttributeError('No attribute {} for {}.'.format(key, self))

    def render(self):
        '''Return a binary representation of this packet - ready to be sent.'''

        data = bytearray()

        # packet ID [varint]
        data.extend(VarInt.to_wire(self.packet_id))

        self.fields.render(data)

        return data

    def resolve(self):
        '''Parse data into object property values.'''

        self.fields.resolve(self.data, self.data_size)

        self.resolved = True

    def hydrate(self, data, data_size):

        self.data = data
        self.data_size = data_size

    def dump(self):

        return {
            'name': self.name,
            'packet_id': self.packet_id,
            'resolved': self.resolved,
            'data_size': self.data_size,
            'fields': self.fields.dump()
        }


class PacketFactory:

    def __init__(self, mcdata_base_dir, game_version):

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

        self.name_packet_map = {}
        self.id_packet_map = {}

        data = None

        with open(protocol_path, 'r') as fin:

            data = json.load(fin)

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
        self.fields = FieldManager()

    @classmethod
    def load(clz, state, direction, name, packet_id, data):

        template = PacketTemplate()

        template.state = state
        template.direction = direction
        template.name = name
        template.packet_id = packet_id

        assert isinstance(data, list)
        assert len(data) == 2
        assert data[0] == 'container'

        for item in data[1]:

            assert len(item) == 2

            type_name = item['type']

            if isinstance(type_name, list):
                type_name = type_name[0]

            template.fields.add(
                name=item['name'],
                type=type_name
            )

        return template

    def create(self):

        new_packet = Packet(self.name, self.packet_id)

        new_packet.fields.copy_fields_from(self.fields)

        return new_packet


class FieldManager:

    def __init__(self):

        self.fields = []
        self.field_map = {}

    def get_field_value(self, name):

        if name not in self.field_map:
            raise NoSuchFieldException(name)

        field = self.fields[self.field_map[name]]

        if isinstance(field, Field):

            # TODO this needs refactoring
            if isinstance(field, PositionField):
                return field

            return field.value

        return field

    def set_field_value(self, name, value):

        if name not in self.field_map:
            raise NoSuchFieldException(name)

        self.fields[self.field_map[name]].value = value

    def clear(self):

        for field in self.fields:
            field.clear()

    def add(self, name, type):

        field = None

        if type == 'position':
            field = PositionField(name, type)
        else:
            field = Field(name, type)

        self.fields.append(field)

        self.field_map[name] = len(self.fields) - 1

    def copy_fields_from(self, source):

        self.fields = []
        self.field_map = {}

        for field in source.fields:

            self.fields.append(copy.copy(field))
            self.field_map[field.name] = len(self.fields) - 1

    def render(self, data):

        for field in self.fields:

            field.render(data)

    def resolve(self, data, data_length):

        offset = 0

        for field in self.fields:

            bytes_consumed = field.resolve(data, offset, data_length)

            offset += bytes_consumed

    def dump(self):

        return {
            'fields': [field.dump() for field in self.fields]
        }


class Field:

    def __init__(self, name, type, value=None):

        self.name = name
        self.type = type
        self.value = value

    def clear(self):

        self.value = None

    def render(self, data):

        data_type = None

        try:
            data_type = DATA_TYPE_REGISTRY[self.type]
        except KeyError:
            raise Exception('Unrecognized data type "{}". '
                            'Is it implemented?'.format(self.type))

        data.extend(data_type.to_wire(self.value))

    def resolve(self, data, offset, data_length):

        data_type = None

        try:
            data_type = DATA_TYPE_REGISTRY[self.type]
        except KeyError:
            raise Exception('Unrecognized data type "{}". '
                            'Is it implemented?'.format(self.type))

        value, bytes_consumed = data_type.from_wire(
            data, offset, data_length
        )

        self.value = value

        return bytes_consumed

    def dump(self):

        return {
            'name': self.name,
            'type': self.type,
            'value': self.value
        }


class PositionField(Field):

    class Location:

        x = None
        y = None
        z = None

        def __init__(self, x=None, y=None, z=None):

            self.x = x
            self.y = y
            self.z = z

        def clear(self):

            self.x, self.y, self.z = None, None, None

    location = Location()

    def clear(self):

        self.location.clear()

    def render(self, data):

        assert self.x is not None
        assert self.y is not None
        assert self.z is not None

        x = int(self.x)
        y = int(self.y)
        z = int(self.z)

        if x < 0:
            x = x - (1 << 26)

        if y < 0:
            y = y - (1 << 12)

        if z < 0:
            z = z - (1 << 26)

        val = ((x & 0x3FFFFFF) << 38) | ((y & 0xFFF) << 26) | (z & 0x3FFFFFF)

        data.extend(UnsignedInt64.to_wire(val))

    def resolve(self, data, offset, data_length):

        value, bytes_consumed = UnsignedInt64.from_wire(data, offset, data_length)

        self.x = value >> 38
        self.y = (value >> 26) & 0xFFF
        self.z = value & 0x3ffffff

        if self.x >= (1 << 25):
            self.x = self.x - (1 << 26)

        if self.y > (1 << 11):
            self.y = self.y - (1 << 12)

        if self.z > (1 << 25):
            self.z = self.z - (1 << 26)

        return bytes_consumed
