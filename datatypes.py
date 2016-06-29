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
    def to_wire(clz, data):
        raise NotImplementedError

    @classmethod
    def from_wire(clz, data, offset, fullsize):
        raise NotImplementedError


@data_type(name='varint')
class VarInt(DataType):

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
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!b', data[offset: offset + 1])[0], 1


@data_type(name='u8')
class UnsignedInt8(DataType):

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!B', data[offset: offset + 1])[0], 1


@data_type(name='i64')
class Int64(DataType):

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!q', data[offset: offset + 8])[0], 8


@data_type(name='f32')
class Float32(DataType):

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!f', data[offset: offset + 4])[0], 4

    @classmethod
    def to_wire(clz, data):

        return struct.pack('!f', data)


@data_type(name='f64')
class Float64(DataType):

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!d', data[offset: offset + 8])[0], 8

    @classmethod
    def to_wire(clz, data):

        return struct.pack('!d', data)


@data_type(name='bool')
class Bool(DataType):

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
    def from_wire(clz, data, offset, fullsize):

        return data[offset: fullsize - offset], fullsize - offset


@data_type(name='i32')
class Int32(DataType):

    @classmethod
    def from_wire(clz, data, offset, fullsize):

        return struct.unpack('!l', data[offset: offset + 4])[0], 4


@data_type(name='u16')
class UnsignedInt16(DataType):

    @classmethod
    def to_wire(clz, data):

        # NOTE int.to_bytes is python3 specific
        return data.to_bytes(2, byteorder='big', signed=False)


@data_type(name='i16')
class Int16(DataType):

    @classmethod
    def to_wire(clz, data):

        return data.to_bytes(2, byteorder='big', signed=True)
