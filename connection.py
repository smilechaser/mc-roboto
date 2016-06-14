'''
'''

import socket
import zlib

from datatypes import VarInt
from splitbuffer import SplitBuffer
from listener import Signal


class Connection:

    MAX_BUFFER_LENGTH = 1024
    DEFAULT_COMPRESSION_THRESHOLD = 1000

    def __init__(self, server, port):

        self.server = server
        self.port = port

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.compression_threshold = -1

    def connect(self):

        self.socket.connect((self.server, self.port))

    @property
    def compression(self):

        return self.compression_threshold > 0

    @compression.setter
    def compression(self, threshold):

        if threshold is True:
            self.compression_threshold = self.DEFAULT_COMPRESSION_THRESHOLD
        elif threshold is False:
            self.compression_threshold = 0
        else:
            self.compression_threshold = threshold

    def send(self, packet):

        buffer = bytearray()

        payload = packet.render()

        if self.compression:

            uncompressed_size = len(payload)

            if uncompressed_size > self.compression_threshold:
                # compress the payload
                payload = zlib.compress(payload, zlib.MAX_WBITS)
            else:
                uncompressed_size = 0

            # calculate data length
            data_len = VarInt.to_wire(uncompressed_size)

            # packet length
            buffer.extend(VarInt.to_wire(len(payload) + len(data_len)))

            buffer.extend(data_len)

        else:

            buffer.extend(VarInt.to_wire(len(payload)))

        buffer.extend(payload)

        self.socket.send(buffer)

    def receive_varint(self):

        acc = bytearray()

        while True:

            data = self.socket.recv(1)

            if data == b'':
                raise Exception('No data!')

            data = data[0]

            acc.append(data)

            if data & 0x80 == 0:
                break

        return acc

    def receive(self):

            # grab the packet length
            packet_len_buffer = self.receive_varint()
            length, _ = VarInt.from_wire(
                packet_len_buffer,
                0,
                len(packet_len_buffer)
            )

            if length == 0:
                return None, None, None

            sb = SplitBuffer()

            bytes_remaining = length

            while bytes_remaining > 0:

                bytes_to_receive = min(bytes_remaining, self.MAX_BUFFER_LENGTH)

                temp_buffer = bytearray(bytes_to_receive)
                view = memoryview(temp_buffer)
                bytes_received = self.socket.recv_into(view, bytes_to_receive)

                sb.deposit(temp_buffer, bytes_received)

                bytes_remaining -= bytes_received

            data_length_size = 0
            data_length = length

            if self.compression:

                data_length, data_length_size = VarInt.from_wire(
                    sb.buffer, 0, sb.size
                )

                if data_length > 0:
                    sb.buffer = zlib.decompress(sb.buffer[data_length_size:],
                                                zlib.MAX_WBITS)

            # read the packet ID
            packet_id, id_length = VarInt.from_wire(sb.buffer,
                                                    data_length_size,
                                                    sb.size)

            return packet_id, sb.buffer[data_length_size + id_length:], sb.size

    def process(self):

        packet_id, packet_data, packet_length = self.receive()

        self.packet(packet_id, packet_data, packet_length)

    @Signal.emitter
    def packet(self, packet_id, packet_data, packet_length):
        pass
