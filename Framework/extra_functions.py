import math
import pygame
import random
import string

from .main_framework import tiled_dda, dda


def id_generator(size=9, chars=string.ascii_uppercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


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

    return [line_start[0] + ab[0] * d, line_start[1] + ab[1] * d]


def clamp(value, value_min, value_max):
    if value < value_min:
        return value_min

    if value > value_max:
        return value_max

    return value


def random_spawn(info):
    if "random" not in info:
        return True
    return random.randint(0, 100) < info["random"]


def load_bonus_property(value, info, default):
    if value in info and value:
        return info[value]

    return default


def random_weight(item_list={}):
    random_item_list = []
    for item_name in item_list:
        random_item_list += [item_name for _ in range(item_list[item_name])]

    return random.choice(random_item_list)


def screen_norm(pos, scroll, screen_dimension):
    pos_norm = [0, 0]
    pos_norm[0] = (pos[0] - scroll[0]) / screen_dimension[0]
    pos_norm[1] = (pos[1] - scroll[1]) / screen_dimension[1]

    return pos_norm


def sound_location(source_pos, listener_pos, max_sound_dist=512):
    angle = math.degrees(math.atan2(source_pos.y - listener_pos.y, source_pos.x - listener_pos.x)) + 90
    distance_percent = source_pos.distance_to(listener_pos) / max_sound_dist

    return angle, distance_percent


def angle_between_vectors(vector_1, vector_2):
    v1_mag = math.sqrt(vector_1[0] * vector_1[0] + vector_1[1] * vector_1[1])
    v2_mag = math.sqrt(vector_2[0] * vector_2[0] + vector_2[1] * vector_2[1])

    dot_product = vector_1[0] * vector_2[0] + vector_1[1] * vector_2[1]

    angle = math.acos(max(-1, min(1, dot_product / (v1_mag * v2_mag))))

    return angle


def dist_to_wall(angle, pos, max_dist, tiles):
    grid_start_pos = [pos[0] / 16, pos[1] / 16]
    grid_end_pos = [(pos[0] + math.cos(angle) * max_dist) / 16,
                    (pos[1] + math.sin(angle) * max_dist) / 16]
    hit = tiled_dda(int(grid_start_pos[0]), int(grid_start_pos[1]),
                    int(grid_end_pos[0]), int(grid_end_pos[1]), tiles)

    if hit is not None:
        return math.dist([hit[0] * 16 + 8, hit[1] * 16 + 8], pos)
    return None


def accurate_wall_dist(angle, pos, max_dist, tiles):
    start_pos = [pos[0], pos[1]]
    end_pos = [start_pos[0] + math.sin(angle) * max_dist,
               start_pos[1] + math.cos(angle) * max_dist]

    hit = dda(start_pos[0], start_pos[1], end_pos[0], end_pos[1], tiles)

    if hit is not None:
        return math.dist(start_pos, hit)
    return None


def draw_smeer(surf, smeer_points, max_width, color=(255, 255, 255)):
    smeer_polygon = []
    i = 0
    for point_angle in smeer_points:
        point = point_angle[0]
        angle = point_angle[1]

        size = i / len(smeer_points) * max_width

        point1 = [point[0] + math.sin(angle) * size,
                  point[1] + math.cos(angle) * size]
        point2 = [point[0] - math.sin(angle) * size,
                  point[1] - math.cos(angle) * size]

        smeer_polygon.append(point1)
        smeer_polygon.insert(-len(smeer_polygon), point2)
        i += 1

    pygame.draw.polygon(surf, color, smeer_polygon)


def get_gradient_circle(radius, shade_step=-1, base_color=(255, 255, 255)):
    circle_gradient_surf = pygame.Surface((radius, radius))
    circle_gradient_surf.fill((0, 0, 0))

    if shade_step == -1:
        shade_step = 255 / radius

    shade_value = 0
    radius_value = radius
    while shade_value < 255 and radius_value > 0:
        shade_value += shade_step
        shade_value = min(shade_value, 255)

        step_surf = pygame.Surface((radius_value, radius_value))
        step_surf.set_colorkey((0, 0, 0))
        step_surf.fill((0, 0, 0))
        pygame.draw.circle(step_surf, base_color, (radius_value / 2, radius_value / 2), radius_value / 2)

        step_surf.set_alpha(shade_value)

        circle_gradient_surf.blit(step_surf, (radius / 2 - radius_value / 2, radius / 2 - radius_value / 2))

        radius_value -= 1

    return circle_gradient_surf


def img_flash(img, alpha=255, color=(255, 255, 255)):
    img_mask = pygame.mask.from_surface(img)
    flash_img = img_mask.to_surface(setcolor=(color[0], color[1], color[2], alpha), unsetcolor=(0, 0, 0, 0))

    return flash_img


def floodfill(start_point, map_surf, wall=(0, 0, 0), corners=False):
    region_tiles = [start_point.copy()]

    while True:
        all_tiles = True

        for tile in region_tiles:
            if not corners:
                checks = [[0, 1], [0, -1], [1, 0], [-1, 0]]
            else:
                checks = [[0, 1], [0, -1], [1, 0], [-1, 0], [-1, -1], [1, -1], [1, 1], [-1, 1]]

            for check in checks:
                try:
                    if map_surf.get_at([tile[0] + check[0], tile[1] + check[1]]) != wall:
                        if region_tiles.count([tile[0] + check[0], tile[1] + check[1]]) == 0:
                            all_tiles = False
                            region_tiles.append([tile[0] + check[0], tile[1] + check[1]])
                except IndexError:
                    continue

        if all_tiles:
            break

    return region_tiles
