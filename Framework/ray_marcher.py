import math


def length(v):
    return math.sqrt(v[0] * v[0] + v[1] * v[1])


def signedDstToCircle(p, centre, radius):
    return length([centre[0] - p[0], centre[1] - p[1]]) - radius


def signedDstToBox(p, centre, size):
    dx = max(abs(p[0] - centre[0]) - size[0] / 2, 0)
    dy = max(abs(p[1] - centre[1]) - size[1] / 2, 0)

    return length([dx, dy])


def signedDstToScene(p, sphere_list, box_list):
    dstToScene = math.inf

    for sphere in sphere_list:
        dstToCircle = signedDstToCircle(p, [sphere[0], sphere[1]], sphere[2])
        dstToScene = min(dstToCircle, dstToScene)

    for box in box_list:
        dstToBox = signedDstToBox(p, [box[0], box[1]], [box[2], box[3]])
        dstToScene = min(dstToBox, dstToScene)

    return dstToScene


def signedDstToTileScene(p, tile_list):
    dstToScene = math.inf

    for box in tile_list:
        dstToBox = signedDstToBox(p, [box.centerx, box.centery], [box.width, box.height])
        dstToScene = min(dstToBox, dstToScene)

    return dstToScene


def cast_ray(p, angle, spheres, boxes, min_dist=1, max_dist=math.inf):
    cur_p = p.copy()

    point_list = []

    dst = math.inf

    iterations = 0

    while iterations < 20 and dst > 0:
        if iterations > 0 and (dst < min_dist or math.dist(cur_p, p) > max_dist):
            break
        dst = signedDstToScene(cur_p, spheres, boxes)
        point_list.append([cur_p.copy(), dst])

        cur_p[0] += math.sin(-angle - 1.57) * dst
        cur_p[1] += math.cos(-angle - 1.57) * dst

        iterations += 1

    return point_list


def cast_tile_ray(p, angle, tiles, min_dist=1, max_dist=math.inf, max_iterations=20):
    cur_p = p.copy()

    point_list = []

    dst = math.inf

    iterations = 0

    while iterations < max_iterations and dst > 0:
        if iterations > 0 and (dst < min_dist or math.dist(cur_p, p) > max_dist):
            break
        dst = signedDstToTileScene(cur_p, tiles)
        point_list.append([cur_p.copy(), dst])

        cur_p[0] += math.sin(-angle - 1.57) * dst
        cur_p[1] += math.cos(-angle - 1.57) * dst

        iterations += 1

    return point_list
