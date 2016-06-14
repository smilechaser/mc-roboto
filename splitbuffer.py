'''
'''


class SplitBuffer:

    def __init__(self, split_size=None):

        self.buffer = b''
        self.size = 0

    def deposit(self, data, data_length):

        self.buffer += data[0:data_length]
        self.size += data_length

    def __getitem__(self, index):

        if hasattr(index, 'start'):
            return self.buffer[index.start:index.stop:index.step]
        else:
            return self.buffer[index]


if __name__ == '__main__':

    data = bytearray(b'010203')
    sb = SplitBuffer()
    sb.deposit(data, 3)
    assert(sb[0] == ord(b'0'))

    data = bytearray(b'0123456789')
    sb = SplitBuffer(split_size=3)
    sb.deposit(data, 10)
    assert(sb[1:6] == b'12345')
