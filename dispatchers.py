'''
'''

import queue
import threading


class ThreadedDispatcher:
    '''
    '''

    class StopExecutionBaton:
        pass

    def __init__(self):

        self.queue = queue.Queue()

        self.worker_thread = threading.Thread(target=self.worker_loop)
        self.worker_thread.start()

    def stop(self):

        self.queue.put((self.StopExecutionBaton, None, None))

        self.worker_thread.join()

    def enqueue(self, emitter, event, key=None):

        self.queue.put(
            (emitter, event, key)
        )

    def dispatch(self):
        # we have our own version of dispatch, but we turn this into a
        # no-op just in case someone calls it directly
        pass

    def worker_loop(self):

        while True:

            emitter, event, key = self.queue.get()

            if emitter == self.StopExecutionBaton:
                break

            emitter.notify(event, key)

            self.queue.task_done()
