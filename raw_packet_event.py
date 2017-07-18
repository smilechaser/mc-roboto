from observer import Event


class RawPacketEvent(Event):
    '''
    '''

    def __init__(self, emitter, packet_id, packet_data, packet_length):

        super().__init__(emitter)

        self.packet_id = packet_id
        self.data = packet_data
        self.length = packet_length
