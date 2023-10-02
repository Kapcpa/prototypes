import math

""" Thats how updating this stuff works (line with 3 points where 1st one is fixed to mouse position)
for line in lines:
    line.update(points)
    start = [points[line.index_1].x, points[line.index_1].y]
    end = [points[line.index_2].x, points[line.index_2].y]
    pygame.draw.line(display, (0, 0, 0), start, end, 1)

i = 0
for point in points:
    if i == 0:
        point.update([mx, my])
    else:
        point.update()
    pygame.draw.circle(display, (255, 0, 0), [point.x, point.y], 3)
    i += 1
"""


class vertex:
    def __init__(self, x, y, drag=0.9, grav=0):
        self.x = x
        self.y = y
        self.last_x = x
        self.last_y = y
        self.drag = drag
        self.grav = grav

    def update(self, fixed=[0, 0]):
        if fixed == [0, 0]:
            dx = (self.x - self.last_x) * self.drag
            dy = (self.y - self.last_y) * self.drag
            self.last_x = self.x
            self.last_y = self.y
            self.x += dx
            self.y += dy
            self.y += self.grav
        else:
            self.x = fixed[0]
            self.y = fixed[1]
            self.last_x = self.x
            self.last_y = self.y


class line:
    def __init__(self, index_1, index_2, length):
        self.index_1 = index_1
        self.index_2 = index_2
        self.length = length

    def update(self, points):
        p1 = points[self.index_1]
        p2 = points[self.index_2]

        dx = p2.x - p1.x
        dy = p2.y - p1.y
        distance = math.sqrt(dx * dx + dy * dy)
        if distance != 0:
            fraction = ((self.length - distance) / distance) / 2
        else:
            fraction = self.length / 2

        dx *= fraction
        dy *= fraction

        p1.x -= dx
        p1.y -= dy
        p2.x += dx
        p2.y += dy

