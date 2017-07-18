import math


class Facing:
    def __init__(self, pitch=0.0, yaw=0.0):

        self.pitch = pitch
        self.yaw = yaw

    def at(self, current, target):

        if current == target:
            return

        #
        # adapted from: http://wiki.vg/Protocol#Player_Look
        #

        dx = target.x - current.x
        dy = target.y - current.y
        dz = target.z - current.z
        r = math.sqrt(dx * dx + dy * dy + dz * dz)

        yaw = math.degrees(-1.0 * math.atan2(dx, dz))
        if yaw < 0.0:
            yaw = yaw + 360.0
        pitch = math.degrees(-math.asin(dy / r))

        self.yaw = yaw
        self.pitch = pitch
