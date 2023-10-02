import pygame
import math
import numpy


def rotate_rect_point(x, y, angle):
    return [x * math.cos(angle) - y * math.sin(angle), x * math.sin(angle) + y * math.cos(angle)]


def collision_test(rect, tiles):
    hit_list = []
    for tile in tiles:
        if rect.colliderect(tile):
            hit_list.append(tile)
    return hit_list


def polygon_collision(object_layer, obstacle_layer):
    obj_mask = pygame.mask.from_surface(object_layer)
    obstacle_mask = pygame.mask.from_surface(obstacle_layer)
    result = obstacle_mask.overlap(obj_mask, [0, 0])
    return result


def collision_circle(a_pos, a_size, b_pos, b_size):
    if math.dist(a_pos, b_pos) < a_size + b_size:
        return True

    return False


def line_closest_point(line_start, line_end, point):
    # Vectors

    ab = [line_end[0] - line_start[0], line_end[1] - line_start[1]]
    ap = [point[0] - line_start[0], point[1] - line_start[1]]

    # Dot Products

    proj = ap[0] * ab[0] + ap[1] * ab[1]

    # distance to travel along line to get to closest point

    ab_len = math.sqrt(ab[0] * ab[0] + ab[1] * ab[1])
    ab_len_sq = ab_len * ab_len

    d = proj / ab_len_sq

    # Closest Point

    if d <= 0:
        return line_start
    elif d >= 1:
        return line_end
    else:
        return [line_start[0] + ab[0] * d, line_start[1] + ab[1] * d]


def move_circle(circle_pos, circle_radius, circle_movement, tiles, lines, dt=1, move_iterations=1):
    potential_pos = circle_pos.copy()
    collide = None

    for iteration in range(move_iterations):
        potential_pos[0] += circle_movement[0] / move_iterations * dt
        potential_pos[1] += circle_movement[1] / move_iterations * dt

        for line in lines:
            nearest_point = line_closest_point(line[0], line[1], potential_pos)

            ray_to_nearest = [nearest_point[0] - potential_pos[0], nearest_point[1] - potential_pos[1]]
            ray_mag = numpy.sqrt(ray_to_nearest[0] * ray_to_nearest[0] + ray_to_nearest[1] * ray_to_nearest[1])
            overlap = circle_radius - ray_mag

            if numpy.isnan(overlap):
                overlap = 0

            if overlap > 0 and ray_mag != 0:
                collide = [ray_to_nearest[0] / ray_mag, ray_to_nearest[1] / ray_mag]
                potential_pos[0] -= collide[0] * overlap
                potential_pos[1] -= collide[1] * overlap

        for tile in tiles:
            nearest_point = [max(tile.x, min(potential_pos[0], tile.x + tile.width)),
                             max(tile.y, min(potential_pos[1], tile.y + tile.height))]

            ray_to_nearest = [nearest_point[0] - potential_pos[0], nearest_point[1] - potential_pos[1]]
            ray_mag = numpy.sqrt(ray_to_nearest[0] * ray_to_nearest[0] + ray_to_nearest[1] * ray_to_nearest[1])
            overlap = circle_radius - ray_mag

            if numpy.isnan(overlap):
                overlap = 0

            if overlap > 0 and ray_mag != 0:
                collide = [ray_to_nearest[0] / ray_mag, ray_to_nearest[1] / ray_mag]
                potential_pos[0] -= collide[0] * overlap
                potential_pos[1] -= collide[1] * overlap

    circle_pos = potential_pos

    return circle_pos, collide


def move(rect, movement, tiles):
    collision_types = {'top': False, 'bottom': False, 'right': False, 'left': False}

    rect.x += movement[0]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[0] > 0:
            rect.right = tile.left
            collision_types['right'] = True
        elif movement[0] < 0:
            rect.left = tile.right
            collision_types['left'] = True
    rect.y += movement[1]
    hit_list = collision_test(rect, tiles)
    for tile in hit_list:
        if movement[1] > 0:
            rect.bottom = tile.top
            collision_types['bottom'] = True
        elif movement[1] < 0:
            rect.top = tile.bottom
            collision_types['top'] = True
    return rect, collision_types
