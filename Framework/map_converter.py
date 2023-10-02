from dataclasses import dataclass
from .ray_caster import Line


@dataclass()
class Cell:
    edge_id: list[int]
    edge_exist: list[bool]
    exist: bool = False


NORTH = 0
SOUTH = 1
EAST = 2
WEST = 3


def convert_to_lines(binary_map, world_tile_size=16):
    width = len(binary_map[0])
    height = len(binary_map)

    edge_pool = []

    cells = []
    for y in range(height):
        cells.append([])
        for x in range(width):
            exist = False
            if binary_map[y][x] == '1':
                exist = True
            cells[y].append(Cell([0, 0, 0, 0], [False, False, False, False], exist))

    for y in range(1, height - 1):
        for x in range(1, width - 1):
            i = [x, y]
            n = [x, y - 1]
            s = [x, y + 1]
            w = [x - 1, y]
            e = [x + 1, y]

            if cells[i[1]][i[0]].exist:
                # Check for western edge
                if not cells[w[1]][w[0]].exist:
                    if cells[n[1]][n[0]].edge_exist[WEST]:
                        edge_pool[cells[n[1]][n[0]].edge_id[WEST]].p2[1] += world_tile_size
                        cells[i[1]][i[0]].edge_id[WEST] = cells[n[1]][n[0]].edge_id[WEST]
                        cells[i[1]][i[0]].edge_exist[WEST] = True
                    else:
                        start = [x * world_tile_size, y * world_tile_size]
                        end = [start[0], start[1] + world_tile_size]

                        edge_pool.append(Line(start, end))

                        edge_id = len(edge_pool) - 1
                        cells[i[1]][i[0]].edge_id[WEST] = edge_id
                        cells[i[1]][i[0]].edge_exist[WEST] = True

                # Check for eastern edge
                if not cells[e[1]][e[0]].exist:
                    if cells[n[1]][n[0]].edge_exist[EAST]:
                        edge_pool[cells[n[1]][n[0]].edge_id[EAST]].p2[1] += world_tile_size
                        cells[i[1]][i[0]].edge_id[EAST] = cells[n[1]][n[0]].edge_id[EAST]
                        cells[i[1]][i[0]].edge_exist[EAST] = True
                    else:
                        start = [(x + 1) * world_tile_size, y * world_tile_size]
                        end = [start[0], start[1] + world_tile_size]

                        edge_pool.append(Line(start, end))

                        edge_id = len(edge_pool) - 1
                        cells[i[1]][i[0]].edge_id[EAST] = edge_id
                        cells[i[1]][i[0]].edge_exist[EAST] = True

                # Check for northern edge
                if not cells[n[1]][n[0]].exist:
                    if cells[w[1]][w[0]].edge_exist[NORTH]:
                        edge_pool[cells[w[1]][w[0]].edge_id[NORTH]].p2[0] += world_tile_size
                        cells[i[1]][i[0]].edge_id[NORTH] = cells[w[1]][w[0]].edge_id[NORTH]
                        cells[i[1]][i[0]].edge_exist[NORTH] = True
                    else:
                        start = [x * world_tile_size, y * world_tile_size]
                        end = [start[0] + world_tile_size, start[1]]

                        edge_pool.append(Line(start, end))

                        edge_id = len(edge_pool) - 1
                        cells[i[1]][i[0]].edge_id[NORTH] = edge_id
                        cells[i[1]][i[0]].edge_exist[NORTH] = True

                # Check for southern edge
                if not cells[s[1]][s[0]].exist:
                    if cells[w[1]][w[0]].edge_exist[SOUTH]:
                        edge_pool[cells[w[1]][w[0]].edge_id[SOUTH]].p2[0] += world_tile_size
                        cells[i[1]][i[0]].edge_id[SOUTH] = cells[w[1]][w[0]].edge_id[SOUTH]
                        cells[i[1]][i[0]].edge_exist[SOUTH] = True
                    else:
                        start = [x * world_tile_size, (y + 1) * world_tile_size]
                        end = [start[0] + world_tile_size, start[1]]

                        edge_pool.append(Line(start, end))

                        edge_id = len(edge_pool) - 1
                        cells[i[1]][i[0]].edge_id[SOUTH] = edge_id
                        cells[i[1]][i[0]].edge_exist[SOUTH] = True

    return edge_pool
