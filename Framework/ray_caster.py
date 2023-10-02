import pygame

from .extra_functions import line_closest_point


class Line:
    def __init__(self, point_1, point_2):
        self.p1 = pygame.Vector2(point_1)
        self.p2 = pygame.Vector2(point_2)

    def intersect_with(self, other):
        x1 = other.p1[0]
        y1 = other.p1[1]
        x2 = other.p2[0]
        y2 = other.p2[1]

        x3 = self.p1[0]
        y3 = self.p1[1]
        x4 = self.p2[0]
        y4 = self.p2[1]

        den = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)

        if den == 0:
            return None

        t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / den
        u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / den

        if 0 <= t <= 1 and 0 <= u <= 1:
            intersection = [x1 + t * (x2 - x1), y1 + t * (y2 - y1)]
            return intersection

        return None

# Sorting ray hits
# ray_hits.sort(key=lambda ray_hit: (ray_hit[0] - start_pos[0]) * (ray_hit[0] - start_pos[0]) +
# (ray_hit[1] - start_pos[1]) * (ray_hit[1] - start_pos[1]))
