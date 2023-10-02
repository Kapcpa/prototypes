import math


class SecondOrderDynamics:
    def __init__(self, f, z, r, start_value):
        self.k1 = z / (math.pi * f)
        self.k2 = 1 / ((2 * math.pi * f) * (2 * math.pi * f))
        self.k3 = r * z / (2 * math.pi * f)
        self.xp = start_value
        self.y = start_value
        self.yd = 0

    def update_k(self, f, z, r):
        self.k1 = z / (math.pi * f)
        self.k2 = 1 / ((2 * math.pi * f) * (2 * math.pi * f))
        self.k3 = r * z / (2 * math.pi * f)

    def update(self, target_value, dt=1, xd=None):
        if dt == 0:
            return

        x = target_value
        if xd is None:
            xd = (x - self.xp) / dt
            self.xp = x
        k2_stable = max(self.k2, dt * dt / 2 + dt * self.k1 / 2, dt * self.k1)
        self.y = self.y + dt * self.yd
        self.yd = self.yd + dt * (x + self.k3 * xd - self.y - self.k1 * self.yd) / k2_stable
