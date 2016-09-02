import unittest

import protocol
from responses import Responses

class TestPacket(unittest.TestCase):

    def test_complex_fields(self):

        factory = protocol.PacketFactory('minecraft-data', '1.10')

        packet = factory.create_by_name(
            protocol.State.PLAY,
            protocol.Direction.TO_SERVER,
            'block_dig'
        )

        # test positive and negative coordinates
        for x, y, z in (
            (-100, -200, -50),
            (100, 200, 50)
        ):

            packet.clear()

            packet.status = 6
            packet.location.x = x
            packet.location.y = y
            packet.location.z = z
            packet.face = 1

            # serialize it
            data = packet.render()

            # unserialize it

            packet.clear()
            # hydrate but skip the first byte (it's the packet ID)
            packet.hydrate(data[1:], len(data)-1)
            packet.resolve()

            self.assertEqual(packet.location.x, x)
            self.assertEqual(packet.location.y, y)
            self.assertEqual(packet.location.z, z)

    def test_complex_response(self):

        factory = protocol.PacketFactory('minecraft-data', '1.10')

        responses = Responses(factory)

        responses.add(protocol.State.PLAY, 'block_dig')

        # test positive and negative coordinates
        for x, y, z in (
            (-100, -200, -50),
            (100, 200, 50)
        ):
            with responses.block_dig as packet:

                packet.clear()

                packet.status = 6
                packet.location.x = x
                packet.location.y = y
                packet.location.z = z
                packet.face = 1

                # serialize it
                data = packet.render()

                # unserialize it

                packet.clear()
                # hydrate but skip the first byte (it's the packet ID)
                packet.hydrate(data[1:], len(data)-1)
                packet.resolve()

                self.assertEqual(packet.location.x, x)
                self.assertEqual(packet.location.y, y)
                self.assertEqual(packet.location.z, z)
