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

    def dummy(clz):

        DATA_TYPE_REGISTRY[name] = clz

        class NewClass(clz):

            DATA_TYPE_NAME = name

        return NewClass

    return dummy


class DataType:

    @classmethod
    def default(clz):
        return None

    @classmethod
    def to_wire(clz, data):

        raise NotImplementedError('to_wire not implemented for {}'.format(clz))

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        raise NotImplementedError('from_wire not implemented for {}'.format(clz))


@data_type(name='varint')
class VarInt(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def from_wire(clz, data, offset, fullsize):
        '''Receives a bytearray and returns an integer.'''

        acc = []

        while True:

            acc.insert(0, data[offset] & 0x7f)

            if data[offset] & 0x80 == 0:
                break

            offset += 1

        shifts = (len(acc)-1) * 7

        data = 0

        for x in acc:

            data += (x << shifts)

            shifts -= 7

        return data, len(acc)

    @classmethod
    def to_wire(clz, data):
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
    def default(clz):
        return ''

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        # read length as varint
        string_length, varint_length = VarInt.from_wire(data, offset, fullsize)

        # read length bytes and convert to python string
        value = data[offset + varint_length:offset + varint_length + string_length]

        value = value.decode()

        return value, varint_length + string_length

    @classmethod
    def to_wire(clz, data):

        assert isinstance(data, (type(''), type(u'')))

        retval = bytearray()

        encoded_string = data.encode('utf-8')

        retval.extend(VarInt.to_wire(len(encoded_string)))
        retval.extend(encoded_string)

        return retval


@data_type(name='i8')
class Int8(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!b', data[offset: offset + 1])[0], 1

    @classmethod
    def to_wire(clz, data):

        return struct.pack('!b', data)


@data_type(name='u8')
class UnsignedInt8(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!B', data[offset: offset + 1])[0], 1


@data_type(name='u16')
class UnsignedInt16(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def to_wire(clz, data):

        # NOTE int.to_bytes is python3 specific
        return data.to_bytes(2, byteorder='big', signed=False)


@data_type(name='i16')
class Int16(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def to_wire(clz, data):

        return data.to_bytes(2, byteorder='big', signed=True)


@data_type(name='i32')
class Int32(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!l', data[offset: offset + 4])[0], 4

    @classmethod
    def to_wire(clz, data):

        return data.to_bytes(4, byteorder='big', signed=True)


@data_type(name='u32')
class UnsignedInt32(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!L', data[offset: offset + 4])[0], 4

    @classmethod
    def to_wire(clz, data):

        return data.to_bytes(4, byteorder='big', signed=False)


@data_type(name='i64')
class Int64(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!q', data[offset: offset + 8])[0], 8


@data_type(name='u64')
class UnsignedInt64(DataType):

    @classmethod
    def default(clz):
        return 0

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!Q', data[offset: offset + 8])[0], 8

    @classmethod
    def to_wire(clz, data):

        return struct.pack('!Q', data)


@data_type(name='f32')
class Float32(DataType):

    @classmethod
    def default(clz):
        return 0.0

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!f', data[offset: offset + 4])[0], 4

    @classmethod
    def to_wire(clz, data):

        return struct.pack('!f', data)


@data_type(name='f64')
class Float64(DataType):

    @classmethod
    def default(clz):
        return 0.0

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!d', data[offset: offset + 8])[0], 8

    @classmethod
    def to_wire(clz, data):

        return struct.pack('!d', data)


@data_type(name='bool')
class Bool(DataType):

    @classmethod
    def default(clz):
        return False

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        if data[offset] == 0x1:
            return True, 1
        else:
            return False, 1

    @classmethod
    def to_wire(clz, data):

        if data is True:
            return b'1'
        else:
            return b'0'


@data_type(name='restBuffer')
class RestBuffer(DataType):

    @classmethod
    def default(clz):
        return None

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return data[offset: fullsize - offset], fullsize - offset


@data_type(name='buffer')
class Buffer(DataType):

    @classmethod
    def default(clz):
        return None

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        # read the length (varint)
        packet_length, varint_length = VarInt.from_wire(data, offset, fullsize)

        # get the rest of the buffer
        return data[offset + varint_length: packet_length], varint_length + packet_length


@data_type(name='array')
class Array(DataType):

    @classmethod
    def default(clz):
        return None

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        # read the length (varint)
        packet_length, varint_length = VarInt.from_wire(data, offset, fullsize)

        # get the rest of the array
        return data[offset + varint_length: packet_length], varint_length + packet_length


@data_type(name='position')
class Position(DataType):

    @classmethod
    def default(clz):
        return Position()

    @classmethod
    def to_wire(clz, position):

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
    def from_wire(clz, data, offset, fullsize):

        value, bytes_consumed = UnsignedInt64.from_wire(data, offset, fullsize)

        self.x = value >> 38
        self.y = (value >> 26) & 0xFFF
        self.z = value & 0x3ffffff

        if self.x >= (1 << 25):
            self.x = self.x - (1 << 26)

        if self.y > (1 << 11):
            self.y = self.y - (1 << 12)

        if self.z > (1 << 25):
            self.z = self.z - (1 << 26)

        return value, varint_length + string_length
