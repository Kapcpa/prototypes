import math
import pygame

from .pathfinding import *
from .ray_caster import *
from .map_converter import *
from .map_tiling import *
from .extra_functions import line_closest_point, clamp


def find_visible_edges(game_map, scroll):
    surf_rect = pygame.Rect(scroll[0], scroll[1], game_map.screen_size[0], game_map.screen_size[1])

    visible_edges = []
    edges_count = 0

    for edge in game_map.shadow_lines + game_map.wall_edges:
        if edges_count >= 100:
            return visible_edges, edges_count

        if surf_rect.clipline(edge.p1, edge.p2):
            visible_edges.append((edge.p1.x, edge.p1.y, edge.p2.x, edge.p2.y))
            edges_count += 1

    # print(100 - edges_count)

    for i in range(100 - edges_count):
        visible_edges.append((0.0, 0.0, 0.0, 0.0))

    return visible_edges, edges_count


def point_col(point, tiles):
    for tile in tiles:
        if tile.collidepoint(point):
            return tile

    return None


class Chunks:
    def __init__(self, chunk_size, screen_size=(800, 450)):
        self.size = chunk_size

        self.tile_size = 16

        self.chunks = {"sorted_wall_edges": {}, "draw_surfs": {}, "rects": {}, "col_lines": {"main": {}, "bullet_col": {}}}

        self.visible_chunks = [int(math.ceil(screen_size[0] / (16 * chunk_size))) + 2,
                               int(math.ceil(screen_size[1] / (16 * chunk_size))) + 2]

    def load_data(self, pixel_map, binary_map, tileset, rect_max_size=None):
        rects = []
        if rect_max_size is None:
            rect_max_size = self.tile_size * self.size

        # Load Draw Tiles

        for y in range(pixel_map.get_height()):
            for x in range(pixel_map.get_width()):
                if pixel_map.get_at([x, y]) == (0, 0, 0):  # Tile
                    rects.append(pygame.Rect(x * self.tile_size, y * self.tile_size, self.tile_size, self.tile_size))

                    draw_tile = [[x * self.tile_size,
                                  y * self.tile_size], find_tile_dir(binary_map, x, y)]

                    chunk_loc_str = str(int(x / self.size)) + ';' + str(int(y / self.size))
                    if chunk_loc_str not in self.chunks["draw_surfs"]:
                        surf = pygame.Surface((256, 256), pygame.SWSURFACE)
                        surf.blit(tileset[draw_tile[1]], (draw_tile[0][0] % 256, draw_tile[0][1] % 256))
                        self.chunks["draw_surfs"][chunk_loc_str] = surf
                    else:
                        self.chunks["draw_surfs"][chunk_loc_str].blit(tileset[draw_tile[1]], (draw_tile[0][0] % 256, draw_tile[0][1] % 256))

        # Merge Rects

        for i, rect in sorted(enumerate(rects), reverse=True):
            if i != 0:
                last_rect = rects[i - 1]
                if rect.width < rect_max_size and rect.y == last_rect.y and last_rect.right == rect.x:
                    last_rect.width += rect.width
                    rects.pop(i)
        for i, rect in sorted(enumerate(rects), reverse=True):
            rect_hit = point_col([rect.x, rect.y + rect.height], rects)

            if rect_hit is not None:
                if rect.x == rect_hit.x and rect.width == rect_hit.width and rect_hit.height < rect_max_size:
                    rect.height += rect_hit.height
                    rects.remove(rect_hit)

        # Rect Chunks

        for rect in rects:
            chunk_loc_str = str(int(rect.centerx / self.tile_size / self.size)) + ';' + str(int(rect.centery / self.tile_size / self.size))
            if chunk_loc_str not in self.chunks["rects"]:
                self.chunks["rects"][chunk_loc_str] = [rect.copy()]
            else:
                self.chunks["rects"][chunk_loc_str].append(rect.copy())

    def get_nearby_rects(self, point):
        nearby_rects = []

        grid_point = [int(point[0] / self.tile_size / self.size), int(point[1] / self.tile_size / self.size)]
        for y in range(grid_point[1] - 1, grid_point[1] + 2):
            for x in range(grid_point[0] - 1, grid_point[0] + 2):
                target_chunk = str(x) + ';' + str(y)

                if target_chunk in self.chunks["rects"]:
                    nearby_rects += self.chunks["rects"][target_chunk]

        return nearby_rects

    def get_nearby_lines(self, point, line_group="main"):
        nearby_rects = []

        grid_point = [int(point[0] / self.tile_size / self.size), int(point[1] / self.tile_size / self.size)]
        for y in range(grid_point[1] - 1, grid_point[1] + 2):
            for x in range(grid_point[0] - 1, grid_point[0] + 2):
                target_chunk = str(x) + ';' + str(y)

                if target_chunk in self.chunks["col_lines"][line_group]:
                    for polygon in self.chunks["col_lines"][line_group][target_chunk]:
                        nearby_rects += polygon

        return nearby_rects

    def load_polygon(self, lines, center, line_group="main"):
        chunk_loc_str = str(int(center[0] / self.tile_size / self.size)) + ';' + str(int(center[1] / self.tile_size / self.size))
        if chunk_loc_str not in self.chunks["col_lines"][line_group]:
            self.chunks["col_lines"][line_group][chunk_loc_str] = [lines]
        else:
            self.chunks["col_lines"][line_group][chunk_loc_str].append(lines)

    def unload_polygon(self, lines, center, line_group="main"):
        chunk_loc_str = str(int(center[0] / self.tile_size / self.size)) + ';' + str(int(center[1] / self.tile_size / self.size))
        if chunk_loc_str in self.chunks["col_lines"][line_group] and lines in self.chunks["col_lines"][line_group][chunk_loc_str]:
            self.chunks["col_lines"][line_group][chunk_loc_str].remove(lines)
        else:
            print('ERROR! Polygon lines not found')

    def draw(self, surf, scroll):
        for y in range(self.visible_chunks[1]):
            for x in range(self.visible_chunks[0]):
                chunk_x = x - 1 + int(round(scroll[0] / (16 * self.size)))
                chunk_y = y - 1 + int(round(scroll[1] / (16 * self.size)))
                target_chunk = str(chunk_x) + ';' + str(chunk_y)

                if target_chunk in self.chunks["draw_surfs"]:
                    chunk_pos = (chunk_x * self.size * 16 - scroll[0], chunk_y * self.size * 16 - scroll[1])
                    surf.blit(self.chunks["draw_surfs"][target_chunk], chunk_pos)

    def debug_draw(self, surf, scroll, color=(255, 0, 255)):
        for y in range(self.visible_chunks[1]):
            for x in range(self.visible_chunks[0]):
                chunk_x = x - 1 + int(round(scroll[0] / (16 * self.size)))
                chunk_y = y - 1 + int(round(scroll[1] / (16 * self.size)))
                target_chunk = str(chunk_x) + ';' + str(chunk_y)

                if target_chunk in self.chunks["rects"]:
                    for rect in self.chunks["rects"][target_chunk]:
                        draw_rect = pygame.Rect(rect.x - scroll[0], rect.y - scroll[1], rect.w, rect.h)

                        pygame.draw.rect(surf, color, draw_rect, 2)


class Map:
    def __init__(self, map_surface, chunk_size=16, screen_size=(800, 450)):
        self.base_binary_map = load_from_png(map_surface)
        self.binary_map = load_from_png(map_surface)

        self.shadow_lines = []

        self.tilesets = {'visible': load_tileset(pygame.image.load('Data/Sprites/Spritesheets/wall_spritesheet.png').convert())}

        self.tile_size = 16

        self.room_pathfinder = AStarRegionSystem(self.binary_map, is_char=True)

        self.chunk_system = Chunks(chunk_size, screen_size)
        self.chunk_system.load_data(map_surface, self.base_binary_map, self.tilesets["visible"])

        self.wall_edges = []

        self.screen_size = screen_size

        self.world_size = [map_surface.get_width() * 16, map_surface.get_height() * 16]

        self.floor_surface = pygame.Surface(self.world_size, pygame.SWSURFACE | pygame.SRCALPHA)
        self.floor_surface.fill((0, 0, 0, 0))

    def load_wall_edges(self):
        self.wall_edges = []

        self.wall_edges += convert_to_lines(self.base_binary_map, self.tile_size)

        # Chunk part of this system

        for y in range(int(self.world_size[1] / 256)):
            for x in range(int(self.world_size[0] / 256)):
                chunk_center = [x * 256 + 128, y * 256 + 128]
                self.chunk_system.chunks["sorted_wall_edges"][f"{x};{y}"] = sorted(self.wall_edges, key=lambda line: math.dist((line.p1 + line.p2) / 2, chunk_center))

        print(f"Wall edges in the world: {len(self.wall_edges)}")

    def world_pos(self, tile_pos):
        return [tile_pos[0] * self.tile_size, tile_pos[1] * self.tile_size]

    def tiles_occupied_by_polygons(self, polygon_lines, checked_tiles='0'):
        occupied_tiles = []

        y = 0
        for layer in self.binary_map:
            x = 0
            for tile in layer:
                if tile == checked_tiles:
                    point_world_pos = [(x + 0.5) * self.tile_size, (y + 0.5) * self.tile_size]
                    point_ray = Line(point_world_pos, [len(self.binary_map[0]) * self.tile_size, point_world_pos[1]])

                    intersections = 0
                    for line in polygon_lines:
                        if point_ray.intersect_with(Line(line[0], line[1])):
                            intersections += 1

                    if intersections % 2 != 0:
                        occupied_tiles.append([x, y])
                x += 1
            y += 1

        return occupied_tiles

    def update_binary_map(self, data):
        for tile in data:
            tile_type = '1'
            if tile["walkable"]:
                tile_type = '0'
            self.binary_map[tile["pos"][1]][tile["pos"][0]] = tile_type

    def update_pathfinders(self, data):
        self.room_pathfinder.update_map(data)

    def load_polygon(self, polygon_lines, polygon_center, line_name="main", update_tilemap=True):
        self.chunk_system.load_polygon(polygon_lines, polygon_center, line_name)

        if not update_tilemap:
            return

        updated_tiles = [{"pos": [tile[0], tile[1]], "walkable": False} for tile in self.tiles_occupied_by_polygons(polygon_lines)]

        self.update_binary_map(updated_tiles)
        self.update_pathfinders(updated_tiles)

    def unload_polygon(self, polygon_lines, polygon_center, line_name="main", update_tilemap=False):
        self.chunk_system.unload_polygon(polygon_lines, polygon_center, line_name)

        if not update_tilemap:
            return

        updated_tiles = [{"pos": [tile[0], tile[1]], "walkable": True} for tile in self.tiles_occupied_by_polygons(polygon_lines, '1')]

        self.update_binary_map(updated_tiles)
        self.update_pathfinders(updated_tiles)

    def can_get_to(self, world_start, world_target):
        region_size = self.tile_size * self.tile_size

        return self.room_pathfinder.find_region_path([int(world_start[0] / region_size), int(world_start[1] / region_size)],
                                                     [int(world_target[0] / region_size), int(world_target[1] / region_size)])

    def get_path(self, world_start, world_target):
        return self.room_pathfinder.find_path([int(world_start[0] / self.tile_size), int(world_start[1] / self.tile_size)],
                                              [int(world_target[0] / self.tile_size), int(world_target[1] / self.tile_size)])

    def shadow_update(self):
        self.shadow_lines = []

        for chunk in self.chunk_system.chunks["col_lines"]["bullet_col"]:
            for lines in self.chunk_system.chunks["col_lines"]["bullet_col"][chunk]:
                for line in lines:
                    self.shadow_lines.append(Line(line[0], line[1]))

    def raycast(self, pos, ray_angle, dist, line_name=None):
        ray = Line(pos, [pos[0] + math.cos(ray_angle) * dist, pos[1] + math.sin(ray_angle) * dist])

        if line_name is None:
            for edge in self.chunk_system.chunks["sorted_wall_edges"][f"{int(pos[0] / 256)};{int(pos[1] / 256)}"]:
                edge_hit = edge.intersect_with(ray)
                if edge_hit:
                    return True
        else:
            # Its kinda sketchy since it checks lines only nearby / one chunk to all sides
            # but nothing should have that big vision anyway so its good performance boost (i hope)
            for line in self.chunk_system.get_nearby_lines(pos, line_name):
                edge = Line(line[0], line[1])
                edge_hit = edge.intersect_with(ray)
                if edge_hit:
                    return True

        return False

    def raycast_hits(self, pos, ray_angle, dist):
        ray = Line(pos, [pos[0] + math.cos(ray_angle) * dist, pos[1] + math.sin(ray_angle) * dist])
        edge_hits = []

        for edge in self.wall_edges:
            edge_hit = edge.intersect_with(ray)
            if edge_hit:
                edge_hits.append(edge_hit)

        edge_hits.sort(key=lambda hit: (hit[0] - pos[0]) * (hit[0] - pos[0]) + (hit[1] - pos[1]) * (hit[1] - pos[1]))

        return edge_hits

    def can_draw(self, pos, scroll, offscreen=128):
        screen_pos = [(pos[0] - scroll[0]), (pos[1] - scroll[1])]
        if -offscreen <= screen_pos[0] <= self.screen_size[0] + offscreen and -offscreen <= screen_pos[1] <= self.screen_size[1] + offscreen:
            return True
        return False

    def draw(self, surf, scroll):
        self.chunk_system.draw(surf, scroll)

    def draw_floor(self, surf, scroll):
        surf.blit(self.floor_surface, [-scroll[0], -scroll[1]])

    def debug_draw(self, surf, scroll, color=(255, 0, 255)):
        for i, edge in enumerate(self.chunk_system.chunks["sorted_wall_edges"][f"{int(scroll[0] / 256)};{int(scroll[1] / 256)}"]):
            p1 = [edge.p1[0] - scroll[0], edge.p1[1] - scroll[1]]
            p2 = [edge.p2[0] - scroll[0], edge.p2[1] - scroll[1]]

            importance_color = [color[0], color[1], color[2], clamp(255 - i * 2, 0, 255)]

            pygame.draw.line(surf, importance_color, p1, p2, 2)
