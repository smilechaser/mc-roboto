import unittest

import protocol


class TestProtocolFactory(unittest.TestCase):
    def _check_packet(self, block_dig_packet):

        self.assertEqual(block_dig_packet.STATE, protocol.State.PLAY)
        self.assertEqual(block_dig_packet.DIRECTION,
                         protocol.Direction.TO_SERVER)
        self.assertEqual(block_dig_packet.NAME, 'block_dig')
        self.assertEqual(block_dig_packet.PACKET_ID, 0x13)

        EXPECTED_FIELDS = [('status', 'i8'), ('location', 'position'), ('face',
                                                                        'i8')]

        # test fields
        for expected, actual in zip(EXPECTED_FIELDS, block_dig_packet.FIELDS):

            self.assertEqual(
                expected[0],
                actual[0],
                msg='Expected field name "{}" but got "{}".'.format(
                    expected[0], actual[0]))
            self.assertEqual(
                expected[1],
                actual[1],
                msg='Expected field type "{}" but got "{}".'.format(
                    expected[1], actual[1]))

    def test_packet_by_name(self):

        factory = protocol.PacketFactory('minecraft-data', '1.10')

        block_dig_packet = factory.get_by_name(
            protocol.State.PLAY, protocol.Direction.TO_SERVER, 'block_dig')()

        self._check_packet(block_dig_packet)

    def test_packet_by_id(self):

        factory = protocol.PacketFactory('minecraft-data', '1.10')

        block_dig_packet = factory.get_by_id(
            protocol.State.PLAY, protocol.Direction.TO_SERVER, 0x13)()

        self._check_packet(block_dig_packet)


class TestProtocolFields(unittest.TestCase):
    def setUp(self):

        self.factory = protocol.PacketFactory('minecraft-data', '1.10')

    def test_simple_packet_fields(self):

        packet = self.factory.get_by_name(protocol.State.HANDSHAKING,
                                          protocol.Direction.TO_SERVER,
                                          'set_protocol')()

        # setters
        packet.fields.protocolVersion = 1234
        packet.fields.serverHost = 'localhost'
        packet.fields.serverPort = 25565

        # getters
        self.assertEqual(packet.fields.protocolVersion, 1234)
        self.assertEqual(packet.fields.serverHost, 'localhost')
        self.assertEqual(packet.fields.serverPort, 25565)

    def test_position_packet_fields(self):

        packet = self.factory.get_by_name(protocol.State.PLAY,
                                          protocol.Direction.TO_CLIENT,
                                          'block_action')()

        FIELD_VALUES = (('x', 1), ('y', 2), ('z', 3))

        for name, value in FIELD_VALUES:
            setattr(packet.fields.location, name, value)

        for name, value in FIELD_VALUES:
            self.assertEqual(value, getattr(packet.fields.location, name))


class TestProtocolSerialization(unittest.TestCase):
    def setUp(self):

        self.factory = protocol.PacketFactory('minecraft-data', '1.10')

    def test_serialization(self):

        packet = self.factory.get_by_name(protocol.State.HANDSHAKING,
                                          protocol.Direction.TO_SERVER,
                                          'set_protocol')()

        packet.fields.protocolVersion = 1234
        packet.fields.serverHost = 'localhost'
        packet.fields.serverPort = 25565

        expected = bytearray(b'\x00\xd2\t\tlocalhostc\xdd\x00')
        actual = packet.to_wire()

        self.assertEqual(expected, actual)

    def test_deserialization(self):

        packet = self.factory.get_by_name(
            protocol.State.PLAY, protocol.Direction.TO_CLIENT, 'animation')()

        data = bytearray(b'\x01\x02')
        packet.from_wire(data, 0)

        self.assertEqual(packet.fields.entityId, 1)
        self.assertEqual(packet.fields.animation, 2)
