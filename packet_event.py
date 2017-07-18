'''
'''


from observer import Event


class PacketEvent(Event):
    '''
    '''

    def __init__(self, emitter, packet):

        super().__init__(emitter)

        self.packet = packet
