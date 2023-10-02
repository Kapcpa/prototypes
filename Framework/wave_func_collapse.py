import pygame.surface
import random

from Data.Scripts.Framework.extra_functions import floodfill


# Tile Class


class Tile:
    def __init__(self, img, sides, name):
        self.img = img  # img is already rotated
        self.sides = sides

        self.name = name  # "tiletype_id_rotation"
        self.tile_name = self.name_info()  # "tiletype_id"
        self.rot = self.rotation_info()

    def name_info(self):
        tile_name = self.name

        while tile_name[-1] != "_":
            tile_name = tile_name[:-1]
        return tile_name[:-1]

    def rotation_info(self):
        tile_name = self.name
        rotation = ""

        while tile_name[-1] != "_":
            rotation += tile_name[-1]
            tile_name = tile_name[:-1]
        return int(rotation[::-1])


def rotate_list(list_value, num):
    new_list = []
    for i in range(len(list_value)):
        new_list.append(list_value[(i + num) % len(list_value)])
    return new_list


# Base algorithm


def can_use(tile, restricted_tiles):
    if tile.name in restricted_tiles and restricted_tiles[tile.name] <= 0:
        return False

    if tile.name[0:3] in restricted_tiles and restricted_tiles[tile.name[0:3]] <= 0:
        return False

    if tile.name[0] in restricted_tiles and restricted_tiles[tile.name[0]] <= 0:
        return False

    return True


def remove_use(tile, restricted_tiles):
    if tile.name in restricted_tiles:
        restricted_tiles[tile.name] -= 1

    if tile.name[0:3] in restricted_tiles:
        restricted_tiles[tile.name[0:3]] -= 1

    if tile.name[0] in restricted_tiles:
        restricted_tiles[tile.name[0]] -= 1


def random_tile_type(tile_type, pos, grid_size, grid_data, tile_base, boundary_id=None, rules={}):
    grid_layout = []

    for y in range(grid_size[1]):
        grid_layout.append([])
        for x in range(grid_size[0]):
            loc_str = str(x) + ';' + str(y)
            if loc_str in grid_data:
                grid_layout[y].append(grid_data[loc_str])
                continue

            grid_layout[y].append(-1)

    x, y = pos

    up = None
    if y - 1 >= 0:
        if grid_layout[y - 1][x] != -1:
            up = tile_base[grid_layout[y - 1][x]].sides[2]
    else:
        up = boundary_id

    down = None
    if y + 1 <= grid_size[1] - 1:
        if grid_layout[y + 1][x] != -1:
            down = tile_base[grid_layout[y + 1][x]].sides[0]
    else:
        down = boundary_id

    left = None
    if x - 1 >= 0:
        if grid_layout[y][x - 1] != -1:
            left = tile_base[grid_layout[y][x - 1]].sides[1]
    else:
        left = boundary_id

    right = None
    if x + 1 <= grid_size[0] - 1:
        if grid_layout[y][x + 1] != -1:
            right = tile_base[grid_layout[y][x + 1]].sides[3]
    else:
        right = boundary_id

    cur_tile_dirs = [up, right, down, left]

    possible_tiles = []

    for tile_index, tile in enumerate(tile_base):
        if tile_type not in tile.name:
            continue
        if tile.name in rules and rules[tile.name] <= 0:
            continue
        is_possible = True
        for i in range(4):
            if cur_tile_dirs[i] is not None:
                if tile.sides[i] != cur_tile_dirs[i][::-1]:  # reversed string
                    is_possible = False
                    break
        if is_possible:
            possible_tiles.append(tile_index)

    return possible_tiles[random.randint(0, len(possible_tiles) - 1)]


def wfc(grid_size, tile_base, grid_data, boundary_id=None, restricted_tiles={}):
    grid_layout = []

    for y in range(grid_size[1]):
        grid_layout.append([])
        for x in range(grid_size[0]):
            loc_str = str(x) + ';' + str(y)
            if loc_str in grid_data:
                grid_layout[y].append(grid_data[loc_str])
                continue

            grid_layout[y].append(-1)

    all_collapsed = False
    while all_collapsed is False:
        cur_tile = [0, 0]
        cur_tile_dirs = [None, None, None, None]

        cur_min_dirs = 4
        for y in range(grid_size[1]):
            for x in range(grid_size[0]):
                if grid_layout[y][x] == -1:
                    set_dirs = 4

                    up = None
                    if y - 1 >= 0:
                        if grid_layout[y - 1][x] != -1:
                            up = tile_base[grid_layout[y - 1][x]].sides[2]
                            set_dirs -= 1
                    else:
                        up = boundary_id

                    down = None
                    if y + 1 <= grid_size[1] - 1:
                        if grid_layout[y + 1][x] != -1:
                            down = tile_base[grid_layout[y + 1][x]].sides[0]
                            set_dirs -= 1
                    else:
                        down = boundary_id

                    left = None
                    if x - 1 >= 0:
                        if grid_layout[y][x - 1] != -1:
                            left = tile_base[grid_layout[y][x - 1]].sides[1]
                            set_dirs -= 1
                    else:
                        left = boundary_id

                    right = None
                    if x + 1 <= grid_size[0] - 1:
                        if grid_layout[y][x + 1] != -1:
                            right = tile_base[grid_layout[y][x + 1]].sides[3]
                            set_dirs -= 1
                    else:
                        right = boundary_id

                    if set_dirs <= cur_min_dirs:
                        cur_tile = [x, y]
                        cur_tile_dirs = [up, right, down, left]

        possible_tiles = []

        for tile_index, tile in enumerate(tile_base):
            if not can_use(tile, restricted_tiles):
                continue
            is_possible = True
            for i in range(4):
                if cur_tile_dirs[i] is not None:
                    if tile.sides[i] != cur_tile_dirs[i][::-1]:
                        is_possible = False
                        break
            if is_possible:
                possible_tiles.append(tile_index)

        # check if can be solved
        if len(possible_tiles) - 1 >= 0:
            tile_index = random.randint(0, len(possible_tiles) - 1)
            grid_layout[cur_tile[1]][cur_tile[0]] = possible_tiles[tile_index]

            remove_use(tile_base[possible_tiles[tile_index]], restricted_tiles)
        else:
            # print('map creation error')
            return None

        all_collapsed = True
        for y in range(grid_size[1]):
            for x in range(grid_size[0]):
                if grid_layout[y][x] == -1:
                    all_collapsed = False
                    break
            if not all_collapsed:
                break

    return grid_layout


# Level Gen / Surface Blit

# grid_data {"tile_x;tile_y": tile_id}
# restricted_tiles {"tile_name or tile_type": times_allowed_to_use}
def wfc_surface(grid_size, tile_data, grid_data={}, tile_size=16, boundary_id=None, restricted_tiles={}):
    wfc_layout = None
    map_fails = -1

    while wfc_layout is None:
        wfc_layout = wfc(grid_size, tile_data, grid_data.copy(), boundary_id, restricted_tiles.copy())
        map_fails += 1
    print(f"map creation fails: {map_fails}")

    surface = pygame.Surface((grid_size[0] * tile_size, grid_size[1] * tile_size))

    for y in range(grid_size[1]):
        for x in range(grid_size[0]):
            tile_img = tile_data[wfc_layout[y][x]].img
            surface.blit(tile_img, (x * tile_size, y * tile_size))

    return surface
