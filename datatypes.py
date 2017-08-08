'''
'''

import struct


# this gets populated via the class decorators on the DataType subclasses
DATA_TYPE_REGISTRY = {}


def data_type(name):
    '''Decorator that:

        a) populates the DATA_TYPE_REGISTRY
        b) modifies the decorated class to include a DATA_TYPE_NAME field
    '''

    def dummy(cls):

        DATA_TYPE_REGISTRY[name] = cls

        class NewClass(cls):

            DATA_TYPE_NAME = name

        return NewClass

    return dummy


class DataType:
    @classmethod
    def default(cls):
        return None

    @classmethod
    def to_wire(cls, data):

        raise NotImplementedError('to_wire not implemented for {}'.format(cls))

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        raise NotImplementedError(
            'from_wire not implemented for {}'.format(cls))


@data_type(name='varint')
class VarInt(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def from_wire(cls, data, offset, fullsize):
        '''Receives a bytearray and returns an integer.'''

        acc = []

        while True:

            acc.insert(0, data[offset] & 0x7f)

            if data[offset] & 0x80 == 0:
                break

            offset += 1

        shifts = (len(acc) - 1) * 7

        data = 0

        for x in acc:

            data += (x << shifts)

            shifts -= 7

        return data, len(acc)

    @classmethod
    def to_wire(cls, data):
        '''Receives an integer and returns a bytearray.'''

        acc = bytearray()

        val = data

        while val > 0x7f:

            seg = val & 0x7f

            rem = val >> 7

            acc.append(seg | 0x80)

            val = rem

        acc.append(val)

        return acc


@data_type(name='string')
class String(DataType):
    @classmethod
    def default(cls):
        return ''

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        # read length as varint
        string_length, varint_length = VarInt.from_wire(data, offset, fullsize)

        # read length bytes and convert to python string
        value = data[offset + varint_length:
                     offset + varint_length + string_length]

        value = value.decode()

        return value, varint_length + string_length

    @classmethod
    def to_wire(cls, data):

        assert isinstance(data, (type(''), type(u'')))

        retval = bytearray()

        encoded_string = data.encode('utf-8')

        retval.extend(VarInt.to_wire(len(encoded_string)))
        retval.extend(encoded_string)

        return retval


@data_type(name='i8')
class Int8(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return struct.unpack('!b', data[offset:offset + 1])[0], 1

    @classmethod
    def to_wire(cls, data):

        return struct.pack('!b', data)


@data_type(name='u8')
class UnsignedInt8(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def to_wire(cls, data):

        return struct.pack('!B', data)

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return struct.unpack('!B', data[offset:offset + 1])[0], 1


@data_type(name='u16')
class UnsignedInt16(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def to_wire(cls, data):

        # NOTE int.to_bytes is python3 specific
        return data.to_bytes(2, byteorder='big', signed=False)


@data_type(name='i16')
class Int16(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return int.from_bytes(data[offset:offset + 2], 'big', signed=True), 2

    @classmethod
    def to_wire(cls, data):

        return data.to_bytes(2, byteorder='big', signed=True)


@data_type(name='i32')
class Int32(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return struct.unpack('!l', data[offset:offset + 4])[0], 4

    @classmethod
    def to_wire(cls, data):

        return data.to_bytes(4, byteorder='big', signed=True)


@data_type(name='u32')
class UnsignedInt32(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return struct.unpack('!L', data[offset:offset + 4])[0], 4

    @classmethod
    def to_wire(cls, data):

        return data.to_bytes(4, byteorder='big', signed=False)


@data_type(name='i64')
class Int64(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return struct.unpack('!q', data[offset:offset + 8])[0], 8


@data_type(name='u64')
class UnsignedInt64(DataType):
    @classmethod
    def default(cls):
        return 0

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return struct.unpack('!Q', data[offset:offset + 8])[0], 8

    @classmethod
    def to_wire(cls, data):

        return struct.pack('!Q', data)


@data_type(name='entityMetadata')
class EntityMetadata(DataType):
    @classmethod
    def default(cls):
        return None

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        # TODO
        return None, 0

    @classmethod
    def to_wire(cls, data):

        raise NotImplementedError()


@data_type(name='slot')
class Slot(DataType):

    @classmethod
    def default(cls):
        return Slot()

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        new_offset = offset

        block_id, consumed = Int16.from_wire(data, new_offset, fullsize)
        new_offset += consumed

        if block_id == -1:

            return Slot(block_id=block_id), consumed

        item_count, consumed = Int8.from_wire(data, new_offset, fullsize)
        new_offset += consumed

        item_damage, consumed = Int16.from_wire(data, new_offset, fullsize)
        new_offset += consumed

        # TODO need to parse NBT data and return the calculated offset (which should == fullsize)
        new_offset = fullsize

        return Slot(block_id=block_id, item_count=item_count, item_damage=item_damage), new_offset

    @classmethod
    def to_wire(cls, data):

        raise NotImplementedError()

    def __init__(self, block_id=-1, item_count=None, item_damage=None, nbt=None):

        self.block_id = block_id
        self.item_count = item_count
        self.item_damage = item_damage
        self.nbt = nbt


@data_type(name='UUID')
class UUID(DataType):
    @classmethod
    def default(cls):
        return (None, None)

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        lower = struct.unpack('!Q', data[offset:offset + 8])[0], 8
        upper = struct.unpack('!Q', data[offset:offset + 8])[0], 8

        return (upper, lower), 16

    @classmethod
    def to_wire(cls, data):

        upper, lower = data

        return struct.pack('!Q', lower)
        return struct.pack('!Q', upper)


@data_type(name='f32')
class Float32(DataType):
    @classmethod
    def default(cls):
        return 0.0

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return struct.unpack('!f', data[offset:offset + 4])[0], 4

    @classmethod
    def to_wire(cls, data):

        return struct.pack('!f', data)


@data_type(name='f64')
class Float64(DataType):
    @classmethod
    def default(cls):
        return 0.0

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return struct.unpack('!d', data[offset:offset + 8])[0], 8

    @classmethod
    def to_wire(cls, data):

        return struct.pack('!d', data)


@data_type(name='bool')
class Bool(DataType):
    @classmethod
    def default(cls):
        return False

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        if data[offset] == 0x1:
            return True, 1
        else:
            return False, 1

    @classmethod
    def to_wire(cls, data):

        if data is True:
            return b'1'
        else:
            return b'0'


@data_type(name='restBuffer')
class RestBuffer(DataType):
    @classmethod
    def default(cls):
        return None

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        return data[offset:fullsize - offset], fullsize - offset


@data_type(name='buffer')
class Buffer(DataType):
    @classmethod
    def default(cls):
        return None

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        # read the length (varint)
        packet_length, varint_length = VarInt.from_wire(data, offset, fullsize)

        # get the rest of the buffer
        return data[offset + varint_length:
                    packet_length], varint_length + packet_length


@data_type(name='array')
class Array(DataType):
    @classmethod
    def default(cls):
        return None

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        # read the length (varint)
        packet_length, varint_length = VarInt.from_wire(data, offset, fullsize)

        # get the rest of the array
        return data[offset + varint_length:
                    packet_length], varint_length + packet_length


@data_type(name='position')
class Position(DataType):
    @classmethod
    def default(cls):
        return Position()

    @classmethod
    def to_wire(cls, position):

        x = int(position.x)
        y = int(position.y)
        z = int(position.z)

        if x < 0:
            x = x - (1 << 26)

        if y < 0:
            y = y - (1 << 12)

        if z < 0:
            z = z - (1 << 26)

        val = ((x & 0x3FFFFFF) << 38) | ((y & 0xFFF) << 26) | (z & 0x3FFFFFF)

        return UnsignedInt64.to_wire(val)

    @classmethod
    def from_wire(cls, data, offset, fullsize):

        value, bytes_consumed = UnsignedInt64.from_wire(data, offset, fullsize)

        x = value >> 38
        y = (value >> 26) & 0xFFF
        z = value & 0x3ffffff

        if x >= (1 << 25):
            x = x - (1 << 26)

        if y > (1 << 11):
            y = y - (1 << 12)

        if z > (1 << 25):
            z = z - (1 << 26)

        obj = Position(x, y, z)

        return obj, bytes_consumed

    def __init__(self, x=0, y=0, z=0):

        self.x, self.y, self.z = (x, y, z)
