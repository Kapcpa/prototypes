import heapq
import math


# AStar


class Node:
    def __init__(self, grid_pos, walkable):
        self.grid_pos = grid_pos
        self.walkable = walkable

        self.g_cost = 0
        self.h_cost = 0

        self.parent = None

    def f_cost(self):
        return self.g_cost + self.h_cost


class AStar:
    def __init__(self, game_map, corners=False, is_char=False):
        self.node_grid = []

        self.corners = corners

        self.wall_symbol = 1
        if is_char:
            self.wall_symbol = '1'

        y = 0
        for layer in game_map:
            self.node_grid.append([])
            x = 0
            for tile in layer:
                if tile == self.wall_symbol:
                    self.node_grid[y].append(Node([x, y], False))
                else:
                    self.node_grid[y].append(Node([x, y], True))
                x += 1
            y += 1

        self.neighbours_pos = [[-1, 0], [0, -1], [1, 0], [0, 1]]
        if self.corners:
            self.neighbours_pos += [[1, 1], [1, -1], [-1, -1], [-1, 1]]

    def update_map(self, data):
        for tile in data:
            self.node_grid[tile["pos"][1]][tile["pos"][0]] = Node(tile["pos"], tile["walkable"])

    def get_neighbours(self, node):
        neighbours = []

        for neighbour in self.neighbours_pos:
            check_x = node.grid_pos[0] + neighbour[0]
            check_y = node.grid_pos[1] + neighbour[1]

            if 0 <= check_x < len(self.node_grid[0]) and 0 <= check_y < len(self.node_grid):
                neighbours.append(self.node_grid[check_y][check_x])  # Dont know if i shouldn't do .copy() here

        return neighbours

    @staticmethod
    def get_dist(node_a, node_b):
        dist_x = abs(node_a.grid_pos[0] - node_b.grid_pos[0])
        dist_y = abs(node_a.grid_pos[1] - node_b.grid_pos[1])

        if dist_x > dist_y:
            return 14 * dist_y + 10 * (dist_x - dist_y)
        return 14 * dist_x + 10 * (dist_y - dist_x)

    @staticmethod
    def retrace_path(start_node, end_node):
        path = []
        current = end_node

        while (current != start_node or current.parent is not None) and current is not None:
            path.append(current)
            current = current.parent

        path.reverse()

        return path

    def find_path(self, world_start_pos, world_target_pos, tile_size=16):  # Not On Grid
        open_set = []
        heapq.heapify(open_set)
        closed_set = []

        try:
            start_node = Node([int(world_start_pos[0] / tile_size), int(world_start_pos[1] / tile_size)], True)
            target_node = self.node_grid[int(world_target_pos[1] / tile_size)][int(world_target_pos[0] / tile_size)]
        except IndexError:
            return []

        if target_node.walkable:
            open_set.append(start_node)

            while len(open_set) > 0:
                open_set.sort(key=lambda node: node.f_cost(), reverse=False)
                current = open_set[0]

                open_set.remove(current)
                closed_set.append(current)

                if current.grid_pos == target_node.grid_pos:
                    return self.retrace_path(start_node, target_node)

                for neighbour in self.get_neighbours(current):
                    if not neighbour.walkable or closed_set.count(neighbour):
                        continue

                    move_cost_to_neighbour = current.g_cost + self.get_dist(current, neighbour)
                    if move_cost_to_neighbour < neighbour.g_cost or not open_set.count(neighbour):
                        neighbour.g_cost = move_cost_to_neighbour
                        neighbour.h_cost = self.get_dist(neighbour, target_node)

                        neighbour.parent = current

                        if not open_set.count(neighbour):
                            open_set.append(neighbour)

        return []


# FlowFields


class FlowFieldNode:
    def __init__(self, grid_pos, walkable):
        self.grid_pos = grid_pos
        self.walkable = walkable

        self.parent = None
        self.iterated = False


class FlowField:
    def __init__(self, game_map, corners=False, is_char=False):
        self.node_grid = []

        self.corners = corners

        self.wall_symbol = 1
        if is_char:
            self.wall_symbol = '1'

        self.reset_map(game_map)

        self.neighbours_pos = [[-1, 0], [0, -1], [1, 0], [0, 1]]
        if self.corners:
            self.neighbours_pos += [[1, 1], [1, -1], [-1, -1], [-1, 1]]

    def reset_map(self, new_map):
        self.node_grid = []

        y = 0
        for layer in new_map:
            self.node_grid.append([])
            x = 0
            for tile in layer:
                if tile == self.wall_symbol:
                    self.node_grid[y].append(FlowFieldNode([x, y], False))
                else:
                    self.node_grid[y].append(FlowFieldNode([x, y], True))
                x += 1
            y += 1

    def get_neighbours(self, node):
        neighbours = []

        for neighbour in self.neighbours_pos:
            check_x = node.grid_pos[0] + neighbour[0]
            check_y = node.grid_pos[1] + neighbour[1]

            if 0 <= check_x < len(self.node_grid[0]) and 0 <= check_y < len(self.node_grid):
                neighbours.append(self.node_grid[check_y][check_x])  # Dont know if i shouldn't do .copy() here

        return neighbours

    def retrace_path(self, world_start_pos, tile_size=16, path_max_len=math.inf):  # If the path to the target was calculated
        path = []
        current = self.node_grid[int(world_start_pos[1] / tile_size)][int(world_start_pos[0] / tile_size)]

        while current.parent is not None and current.iterated is True and len(path) < path_max_len:
            path.append(current)
            current = current.parent

        return path

    def calculate_flowfield(self, world_target_pos, tile_size=16):  # Not On Grid
        open_set = []
        heapq.heapify(open_set)
        closed_set = []

        try:
            target_node = self.node_grid[int(world_target_pos[1] / tile_size)][int(world_target_pos[0] / tile_size)]
            target_node.iterated = True
        except IndexError:
            return

        open_set.append(target_node)

        if target_node.walkable:
            open_set.append(target_node)

            while len(open_set) > 0:
                current = open_set[0]

                open_set.remove(current)
                closed_set.append(current)

                for neighbour in self.get_neighbours(current):
                    if neighbour.walkable and neighbour.parent is None and neighbour.iterated is False:
                        open_set.append(neighbour)
                        neighbour.parent = current
                        neighbour.iterated = True

        return


# A* Region System


class AStarRegionSystem:
    def __init__(self, binary_map, region_size=16, corners=False, is_char=False):
        self.binary_map = binary_map
        self.regions_binary_map = []

        self.regions = {}
        self.region_neighbours = {}
        self.region_sides = {}

        self.region_size = region_size

        # Initialization

        self.load_map(binary_map)

        # Pathfinders

        self.corners = corners
        self.is_char = is_char

        self.region_pathfinder = AStar(self.regions_binary_map, corners=corners, is_char=is_char)

    def load_map(self, binary_map):
        self.split_into_regions(binary_map)
        self.set_region_neighbours()
        self.set_minimap(binary_map)

    def split_into_regions(self, binary_map):
        regions_x = int(len(binary_map[0]) / self.region_size)
        regions_y = int(len(binary_map) / self.region_size)

        self.regions = {}

        for y in range(regions_y):
            for x in range(regions_x):
                region_binary_map = []

                for region_y in range(self.region_size):
                    region_binary_map.append([])
                    for region_x in range(self.region_size):
                        region_binary_map[region_y].append(binary_map[y * self.region_size + region_y][x * self.region_size + region_x])

                self.regions[f"{x};{y}"] = region_binary_map

    def set_region_neighbours(self):
        self.region_sides = {}

        for region in self.regions:
            self.region_sides[region] = {
                "0;-1": [tile for tile in self.regions[region][0]],
                "0;1": [tile for tile in self.regions[region][-1]],
                "-1;0": [row[0] for row in self.regions[region]],
                "1;0": [row[-1] for row in self.regions[region]]
            }

        self.region_neighbours = {}

        for region in self.regions:
            self.region_neighbours[region] = [
                ["1", "1", "1"],
                ["1", "0", "1"],
                ["1", "1", "1"]
            ]

            x, y = region.split(';')

            for offset in [[-1, 0], [0, -1], [1, 0], [0, 1]]:
                neighbour_x, neigbour_y = int(x) + offset[0], int(y) + offset[1]
                neighbour_pos = f"{neighbour_x};{neigbour_y}"

                if neighbour_pos not in self.regions:
                    continue

                region_side = self.region_sides[region][f"{offset[0]};{offset[1]}"]
                neighbour_side = self.region_sides[neighbour_pos][f"{offset[0] * -1};{offset[1] * -1}"]

                if any((neighbour_side[i] == region_side[i] == "0") for i in range(self.region_size)):
                    self.region_neighbours[region][offset[1] + 1][offset[0] + 1] = "0"

    def set_minimap(self, binary_map):
        regions_x = int(len(binary_map[0]) / self.region_size)
        regions_y = int(len(binary_map) / self.region_size)

        self.regions_binary_map = []

        for y in range(regions_y):
            for x in range(regions_x):
                region = self.region_neighbours[f"{x};{y}"]
                for i, row in enumerate(region):
                    if len(self.regions_binary_map) <= y * len(region) + i:
                        self.regions_binary_map.append(row)
                        continue

                    self.regions_binary_map[y * len(region) + i] += row

    def update_map(self, data):
        for tile in data:
            tile_type = '1'
            if tile["walkable"]:
                tile_type = '0'

            self.binary_map[tile["pos"][1]][tile["pos"][0]] = tile_type

        self.load_map(self.binary_map)
        self.region_pathfinder = AStar(self.regions_binary_map, corners=self.corners, is_char=self.is_char)

    def find_region_path(self, region_a, region_b):
        a = [region_a[0] * 3 + 1, region_a[1] * 3 + 1]
        b = [region_b[0] * 3 + 1, region_b[1] * 3 + 1]

        return self.region_pathfinder.find_path(a, b, tile_size=1)

    def merge_regions(self, region_a_pos, region_b_pos):
        offset = [region_b_pos[0] - region_a_pos[0], region_b_pos[1] - region_a_pos[1]]

        region_a = self.regions[f"{region_a_pos[0]};{region_a_pos[1]}"]
        region_b = self.regions[f"{region_b_pos[0]};{region_b_pos[1]}"]

        if offset == [1, 0]:
            return [region_a[i] + [region_b[i][0]] for i in range(self.region_size)]
        if offset == [-1, 0]:
            return [[region_b[i][-1]] + region_a[i] for i in range(self.region_size)]
        if offset == [0, 1]:
            return region_a + [region_b[0]]
        if offset == [0, -1]:
            return [region_b[-1]] + region_a

    def furthest_tiles_in_direction(self, region, direction, tile_type="0"):
        possible_tile_list = []

        if direction == [1, 0]:
            for i in range(self.region_size):
                if region[i][-1] == tile_type:
                    possible_tile_list.append([len(region[i]) - 1, i])
            return possible_tile_list
        if direction == [-1, 0]:
            for i in range(self.region_size):
                if region[i][0] == tile_type:
                    possible_tile_list.append([0, i])
            return possible_tile_list
        if direction == [0, 1]:
            for i in range(self.region_size):
                if region[-1][i] == tile_type:
                    possible_tile_list.append([i, len(region) - 1])
            return possible_tile_list
        if direction == [0, -1]:
            for i in range(self.region_size):
                if region[0][i] == tile_type:
                    possible_tile_list.append([i, 0])
            return possible_tile_list

        return None

    def find_path(self, tile_a, tile_b):
        region_a = [tile_a[0] // self.region_size, tile_a[1] // self.region_size]
        region_b = [tile_b[0] // self.region_size, tile_b[1] // self.region_size]

        region_path = self.find_region_path(region_a, region_b)
        if not region_path:
            return []

        if region_a == region_b:
            pathfinder = AStar(self.regions[f"{region_a[0]};{region_a[1]}"], self.corners, self.is_char)
            path = pathfinder.find_path([tile_a[0] % self.region_size, tile_a[1] % self.region_size],
                                        [tile_b[0] % self.region_size, tile_b[1] % self.region_size], 1)

            return self.turn_to_world_path(tile_a, path)

        # Pathfinding to neighbour region

        region_dir = [region_path[1].grid_pos[0] - region_path[0].grid_pos[0],
                      region_path[1].grid_pos[1] - region_path[0].grid_pos[1]]

        # Finding a tile near the neighbour region to pathfind to

        merged_region = self.merge_regions(region_a, [region_a[0] + region_dir[0], region_a[1] + region_dir[1]])

        tile_pos = [tile_a[0] % self.region_size + int(region_dir[0] < 0), tile_a[1] % self.region_size + int(region_dir[1] < 0)]
        target_pos = sorted(self.furthest_tiles_in_direction(merged_region, region_dir), key=lambda x: math.dist(tile_pos, x))[0]

        path = AStar(merged_region, self.corners, self.is_char).find_path(tile_pos, target_pos, 1)

        return self.turn_to_world_path(tile_a, path, [-1 * int(region_dir[0] < 0), -1 * int(region_dir[1] < 0)])

    def turn_to_world_path(self, start_tile, path, offset=[0, 0]):
        for node in path:
            node.grid_pos[0] += int(start_tile[0] // self.region_size) * self.region_size + offset[0]
            node.grid_pos[1] += int(start_tile[1] // self.region_size) * self.region_size + offset[1]

        return path
