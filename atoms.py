'''
'''

import math


class Vector3:

    def __init__(self, x=0.0, y=0.0, z=0.0):

        self.x = x
        self.y = y
        self.z = z

    def __str__(self):

        return '{:.1f} {:.1f} {:.1f}'.format(self.x, self.y, self.z)

    def distance(self, other):

        x = other.x - self.x
        y = other.y - self.y
        z = other.z - self.z

        result = math.sqrt((x * x) + (y * y) + (z * z))

        return result

    def reset(self):

        self.x = self.y = self.z = 0.0

    def __eq__(self, tgt):

        return self.x == tgt.x and self.y == tgt.y and self.z == tgt.z


class Position(Vector3):

    def impulse(self, dest):

        values = []

        for a, b in (
            (self.x, dest.x),
            (self.y, dest.y),
            (self.z, dest.z)
        ):

            result = b - a

            if result > 0:
                result = min(result, 1)
            else:
                result = max(result, -1)

            values.append(result)

        return Velocity(*values)

    @classmethod
    def from_args(self, current, args):

        values = [current.x, current.y, current.z]

        for n in range(0, 3):
            if args[n].startswith('~'):
                if len(args[n]) == 1:
                    continue
                values[n] += int(args[n][1:])
            else:
                values[n] = int(args[n])

        return Position(*values)


class Velocity(Vector3):

    @property
    def stopped(self):

        return self.x == self.y == self.z == 0.0
