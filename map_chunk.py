'''
'''

from datatypes import UnsignedInt8, VarInt

BYTES_PER_LONG = 8

# 4096 blocks at 1/2 byte per block --> 2048 bytes
BLOCK_LIGHT_BYTES = 4096 // 2

# 4096/2 --> 2048 *IF* in overworld, otherwise not present!!!
SKY_LIGHT_BYTES = 4096 // 2


def parse_chunk_data(chunk_x, chunk_z, ground_up, specified_chunks,
                     chunk_data, block_entities,
                     chunk_manager, entity_manager,
                     overworld=True):
    '''Parse chunk data and store a) chunk data to topology, and b) entity data into the entity_manager.'''

    # specified_chunks = primary_bitmask --> [0,...,15]

    column = chunk_manager.get(chunk_x, chunk_z)

    offset = 0

    for current_chunk in specified_chunks:

        slice = column.get_slice(current_chunk * 16)

        bits_per_block, increment = UnsignedInt8.from_wire(chunk_data, offset, len(chunk_data))
        offset += increment

        palette_length, increment = VarInt.from_wire(chunk_data, offset, len(chunk_data))
        offset += increment

        palette = None

        if palette_length > 0:

            palette = []

            for n in range(0, palette_length):

                val, increment = VarInt.from_wire(chunk_data, offset, len(chunk_data))
                offset += increment

                palette.append(val)

        data_length, increment = VarInt.from_wire(chunk_data, offset, len(chunk_data))
        offset += increment

        data_array = chunk_data[offset:offset+(data_length * BYTES_PER_LONG)]
        offset += (data_length * BYTES_PER_LONG)

        # TODO deal with block lights
        offset += BLOCK_LIGHT_BYTES

        if overworld:

            # TODO deal with sky lights
            offset += SKY_LIGHT_BYTES

        # TODO create columns and slices and insert into chunk_manager

        assert data_length > 0

        mask = (1 << bits_per_block) - 1

        bit_index = 0

        for x_coord in range(0, 16):
            for z_coord in range(0, 16):
                for y_coord in range(0, 16):

                    lower_word = bit_index // 64
                    upper_word = (bit_index + bits_per_block - 1) // 64

                    lower_shift = bit_index % 64
                    upper_shift = 64 - lower_shift

                    bit_index += bits_per_block

                    if lower_word == upper_word:
                        block = (data_array[lower_word] >> lower_shift) & mask
                    else:
                        block = (data_array[lower_word] >> lower_shift |
                                 data_array[upper_word] << upper_shift) & mask

                    if palette:
                        block = palette[block]

                    slice.set_block(x_coord, y_coord, z_coord, block)


class ChunkManager:

    columns = {}

    def __init__(self):

        self.flush()

    def flush(self):

        self.columns = {}

    def get(self, chunk_x, chunk_z):

        key = self._make_column_key(chunk_x, chunk_z)

        return self.columns.setdefault(key, Column(x=chunk_x, z=chunk_z))

    def unload(self, chunk_x, chunk_z):

        key = self._make_column_key(chunk_x, chunk_z)

        del(self.columns[key])

    def _make_column_key(self, chunk_x, chunk_z):

        return '{}:{}'.format(chunk_x, chunk_z)


class Column:

    x = None
    z = None

    slices = {}

    def __init__(self, x=None, z=None):

        self.x = x
        self.z = z

    def get_slice(self, y):

        return self.slices.setdefault(y, StrataSlice(y=y))


class StrataSlice:
    '''
    This is a 16x16x16 block within a column (chunk).
    '''

    y = None

    # if all blocks in this slice are the same, then this will be
    # the block type
    fill_block = None

    blocks = {}

    def __init__(self, y=None):

        self.y = y

    def set_block(self, x, y, z, block_id):

        key = self._make_key(x, y, z)

        self.blocks[key] = block_id

    def _make_key(self, x, y, z):

        return '{}:{}:{}'.format(x, y, z)
