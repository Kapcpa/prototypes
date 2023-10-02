def expo(value, n):
    for i in range(n - 1):
        value * value
    return value


class cubic_bezier:
    def __init__(self, p2, p3):
        #  p1 and p4 are the static ones
        self.p1 = [0, 0]
        self.p2 = p2
        self.p3 = p3
        self.p4 = [1, 1]

    def generate_coord(self, t):  # 0 < t <= 1
        x = expo((1 - t), 3) * self.p1[0] + 3 * t * expo((1 - t), 2) * self.p2[0] + 3 * (t * t) * (1 - t) * self.p3[0] + (t * t * t) * self.p4[0]
        y = expo((1 - t), 3) * self.p1[1] + 3 * t * expo((1 - t), 2) * self.p2[1] + 3 * (t * t) * (1 - t) * self.p3[1] + (t * t * t) * self.p4[1]
        return [x, y]
