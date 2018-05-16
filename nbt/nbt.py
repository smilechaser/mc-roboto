import gzip
import inspect
import sys
import struct

# DEBUG
import pprint


class Buffer:

    def __init__(self, data):

        self._buffer = data
        self._buffer_length = len(data)
        self._ptr = 0

    def consume(self, amount):

        assert amount != 0

        retval = self._buffer[self._ptr: self._ptr + amount]
        self._ptr += amount

        print('read: ', amount)
        print([x for x in retval])

        return retval

    @property
    def empty(self):
        return self._ptr >= self._buffer_length

    def decode_short(self):

        return struct.unpack('>H', self.consume(2))[0]

    def decode_byte(self):

        return struct.unpack('!b', self.consume(1))[0]


class Parser:

    def __init__(self):

        # auto-register the Tags from this module

        tags = []

        for item in globals().values():

            if inspect.isclass(item) and issubclass(item, Tag):
                tags.append(item)

        self.registry = {tag.key: tag for tag in tags if tag.key is not None}

    def decode(self, buffer):

        root = None

        while not buffer.empty:

            tag_type = buffer.decode_byte()

            tag = parser.registry[tag_type].decode(buffer, nameless=False)

            if not tag:
                return CompoundTag(name=None)

            tag.hydrate(self, buffer)

            if not root:
                root = tag

        return root


class Tag:

    key = None

    @classmethod
    def decode(clz, buffer, nameless=False):
        pass

    @property
    def as_dict(self):

        return {
            'type': self.__class__.__name__,
            'key': self.key,
            'name': self.name,
            **self.as_dict_sub
        }

    @property
    def as_dict_sub(self):
        return {}

    def to_python(self):
        pass

    def hydrate(self, parser, buffer):
        pass


class NumberTag(Tag):

    key = None
    struct_format = None
    byte_size = None

    @classmethod
    def decode(clz, buffer, nameless=False):

        name = None

        if not nameless:

            size = buffer.decode_short()
            name = buffer.consume(size).decode()

        value = clz.extract_value(buffer)

        return clz(name=name, value=value)

    @classmethod
    def extract_value(clz, buffer):

        return struct.unpack(clz.struct_format, buffer.consume(clz.byte_size))[0]

    def __init__(self, name, value):

        self.name = name
        self.value = value

    @property
    def as_dict_sub(self):

        return {
            'value': self.value
        }

    def to_python(self):

        return self.value


class ArrayTag(Tag):

    key = None
    sub_struct_format = None
    sub_byte_size = None

    @classmethod
    def decode(clz, buffer, nameless=False):

        # TODO the docs say this is a SIGNED 4-byte integer...but why would
        # it be signed???

        name = None

        if not nameless:

            size = buffer.decode_short()
            name = buffer.consume(size).decode()

        size = struct.unpack('!l', buffer.consume(4))[0]

        values = []

        for n in range(0, size):

            values.append(struct.unpack(clz.sub_struct_format, buffer.consume(clz.sub_byte_size))[0])

        return clz(name=name, values=values)

    def __init__(self, name, values):

        self.name = name
        self.values = values

    def to_python(self):

        return self.values

    @property
    def as_dict_sub(self):

        return {
            'values': self.values
        }


class EndTag(Tag):

    key = 0


class ByteTag(NumberTag):

    key = 1
    struct_format = '!b'
    byte_size = 1


class ShortTag(NumberTag):

    key = 2

    @classmethod
    def extract_value(clz, buffer):

        return int.from_bytes(buffer.consume(2), 'big', signed=True)


class IntTag(NumberTag):

    key = 3
    struct_format = '!l'
    byte_size = 4


class LongTag(NumberTag):

    key = 4
    struct_format = '!q'
    byte_size = 8


class FloatTag(NumberTag):

    key = 5
    struct_format = '!f'
    byte_size = 4


class DoubleTag(NumberTag):

    key = 6
    struct_format = '!d'
    byte_size = 8


class ByteArrayTag(ArrayTag):

    key = 7
    sub_struct_format = '!b'
    sub_byte_size = 1


class StringTag(Tag):

    key = 8

    @classmethod
    def decode(clz, buffer, nameless=False):

        name = None

        if not nameless:

            size = buffer.decode_short()
            name = buffer.consume(size).decode()

        size = buffer.decode_short()
        value = buffer.consume(size).decode()

        return clz(name=name, value=value)

    def __init__(self, name, value):

        self.name = name
        self.value = value

    @property
    def as_dict_sub(self):

        return {
            'value': self.value
        }

    def to_python(self):

        return self.value


class ListTag(Tag):

    key = 9

    @classmethod
    def decode(clz, buffer, nameless=False):

        name = None

        if not nameless:

            size = buffer.decode_short()
            name = buffer.consume(size).decode()

        subtype = buffer.decode_byte()
        length = struct.unpack('!l', buffer.consume(4))[0]

        return clz(name=name, subtype=subtype, expected_length=length)

    def __init__(self, name, subtype, expected_length):

        self.name = name
        self.items = []
        self.subtype = subtype
        self.expected_length = expected_length

    def add(self, tag):

        self.items.append(tag)

    @property
    def as_dict_sub(self):

        return {
            'subtype': self.subtype,
            'items': self.items,
            'expected_length': self.expected_length
        }

    @property
    def filled(self):

        return len(self.items) == self.expected_length

    def hydrate(self, parser, buffer):

        while not self.filled:

            tag = parser.registry[self.subtype].decode(buffer, nameless=True)

            tag.hydrate(parser, buffer)

            self.add(tag)

    def to_python(self):

        return [tag.to_python() for tag in self.items]


class CompoundTag(Tag):

    key = 10

    @classmethod
    def decode(clz, buffer, nameless=False):

        name = None

        if not nameless:

            size = buffer.decode_short()

            if size > 0:
                name = buffer.consume(size).decode()

        return clz(name=name)

    def __init__(self, name):

        self.name = name
        self.items = []

    def add(self, tag):

        self.items.append(tag)

    def hydrate(self, parser, buffer):

        while True:

            tag_type = buffer.decode_byte()

            tag = parser.registry[tag_type].decode(buffer, nameless=False)

            if not tag:

                return None

            tag.hydrate(parser, buffer)

            self.add(tag)

    def to_python(self):

        return {self.name: {tag.name: tag.to_python() for tag in self.items}}

    @property
    def as_dict_sub(self):

        return {
            'items': self.items
        }


class IntArrayTag(ArrayTag):

    key = 11
    sub_struct_format = '!l'
    sub_byte_size = 4


class LongArrayTag(ArrayTag):

    key = 12
    sub_struct_format = '!q'
    sub_byte_size = 8


def nbt_to_python(nbt_root):

    return nbt_root.to_python()


if __name__ == '__main__':

    parser = Parser()

    filename = sys.argv[1]

    data = None
    try:
        data = gzip.open(filename, 'rb').read()
    except OSError as exc:
        # TODO I don't like that we can't narrow this exception
        data = open(filename, 'rb').read()

    buff = Buffer(data)

    root = parser.decode(buff)

    print('--- root ---')
    pprint.pprint(root.as_dict)

    print('=' * 55)
    pprint.pprint(nbt_to_python(root))
