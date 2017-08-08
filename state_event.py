'''
'''


from observer import Event


class StateChangeEvent(Event):
    '''
    '''

    def __init__(self, emitter, old_state, new_state):

        super().__init__(emitter)

        self.old_state = old_state
        self.new_state = new_state
