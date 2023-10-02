import random
import sys
import time

# initialize frameworks
import pygame.transform

pygame.init()

from pygame.locals import *
from Framework.collisions import *
from Framework.second_order_system import *
from Framework.main_framework import Font
from Framework.pathfinding import *
from Framework.extra_functions import clamp

WINDOW_SIZE = (800, 450)  # to not use full screen (900, 504) full screen (1366, 768)

global col_rects, ladders, defence_points

scale = 1

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)
pygame.display.set_caption("Prototype 1 - Tower Defence Post Apo Game")

font = Font('Framework/font.png')

fps_clock = pygame.time.Clock()

display = pygame.Surface((WINDOW_SIZE[0] / scale, WINDOW_SIZE[1] / scale))

scroll = [0, 0]


def point_col(point, tiles):
    for tile in tiles:
        if tile.collidepoint(point):
            return tile

    return None

# TODO:
#   - player can die/be knocked out?
#   - player must sit in the train to make it go forward?


class Map:
    def __init__(self, tile_size=32):
        self.tile_size = tile_size

        self.binary_map = [
            ["1" for _ in range(32)],
            ["1" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["0" for _ in range(32)],
            ["1" for _ in range(32)],
            ["1" for _ in range(32)],
            ["1" for _ in range(32)],
            ["1" for _ in range(32)],
        ]
        self.last_chunk = [row.copy() for row in self.binary_map]

        # Chunk: "x;y": {"start_y": 0-16, "end_y": 0-16, "binary_map": []}
        self.chunks = [{"start_y": 8, "end_y": 8, "binary_map": [row.copy() for row in self.binary_map]}]

        self.train_path = [[16 * self.tile_size, self.chunks[0]["end_y"] * self.tile_size]]

        self.room_pathfinder = AStarRegionSystem(self.binary_map)

        self.max_updated_chunks = 5

        self.x_chunk_shift = -(self.max_updated_chunks - 1) * 16 * self.tile_size

        # Draw stuff

        self.train_draw_path = []
        self.rects = []

        self.add_chunks(self.max_updated_chunks - 1)

    def add_obstacle(self, binary_map, x, y, w, h, train_path):
        rects = []

        for y_pos in range(h):
            for x_pos in range(w):
                try:
                    if any(node.grid_pos == [x + x_pos, y + y_pos] for node in train_path):
                        continue
                    binary_map[y + y_pos][x + x_pos] = "1"
                    rects.append(pygame.Rect((x + x_pos) * self.tile_size + self.x_chunk_shift, (y + y_pos) * self.tile_size, self.tile_size, self.tile_size))
                except IndexError:
                    pass

        return binary_map, rects

    def add_chunks(self, chunks):
        self.x_chunk_shift += chunks * 16 * self.tile_size

        for y, row in enumerate(self.last_chunk):
            for x, tile in enumerate(row):
                if tile == "1":
                    self.rects.append(pygame.Rect(x * self.tile_size + self.x_chunk_shift - 16 * self.tile_size,
                                                  y * self.tile_size, self.tile_size, self.tile_size))

        start_chunks = len(self.chunks)
        self.binary_map = [row.copy() for row in self.last_chunk]
        for _ in range(chunks):
            binary_map = [["0" for _ in range(16)] for _ in range(16)]

            for i in range(len(self.binary_map)):
                self.binary_map[i] += binary_map[i]

            self.chunks.append({"start_y": self.chunks[-1]["end_y"], "end_y": random.randint(6, 10), "binary map": binary_map})

        for i in range(start_chunks, start_chunks + chunks):
            self.train_path.append([(i + 1) * 16 * self.tile_size - self.tile_size, self.chunks[i]["end_y"] * self.tile_size])

        # Train path

        self.room_pathfinder = AStarRegionSystem(self.binary_map, is_char=True)
        for point in self.train_draw_path:
            point.grid_pos[0] -= (len(self.chunks) - self.max_updated_chunks) * 16
        if self.train_draw_path:
            path = self.get_path(self.world_pos(self.train_draw_path[-1].grid_pos), self.train_path[0])
            self.train_draw_path += path
            if len(path) == 1:
                self.train_draw_path += self.get_path(self.world_pos(path[0].grid_pos), self.train_path[0])
        for i in range(len(self.train_path) - 1):
            path = self.get_path(self.train_path[i], self.train_path[i + 1])
            self.train_draw_path += path
            if len(path) == 1:
                self.train_draw_path += self.get_path(self.world_pos(path[0].grid_pos), self.train_path[i + 1])

        # Rects

        for _ in range(10):
            self.binary_map, obstacle_rects = self.add_obstacle(self.binary_map, random.randint(16, 16 * self.max_updated_chunks),
                                                                random.randint(0, 6) + 10 * random.randint(0, 1),
                                                                random.randint(1, 5), random.randint(1, 5), self.train_draw_path)
            self.rects += obstacle_rects

        # Merge Rects

        for i, rect in sorted(enumerate(self.rects), reverse=True):
            if i != 0:
                last_rect = self.rects[i - 1]
                if rect.width < 512 and rect.y == last_rect.y and last_rect.right == rect.x:
                    last_rect.width += rect.width
                    self.rects.pop(i)
        for i, rect in sorted(enumerate(self.rects), reverse=True):
            rect_hit = point_col([rect.x, rect.y + rect.height], self.rects)

            if rect_hit is not None:
                if rect.x == rect_hit.x and rect.width == rect_hit.width and rect_hit.height < 512:
                    rect.height += rect_hit.height
                    self.rects.remove(rect_hit)

        self.last_chunk = [row.copy()[-16:] for row in self.binary_map]

        self.room_pathfinder = AStarRegionSystem(self.binary_map, is_char=True)

    def get_path(self, world_start, world_target):
        grid_start = [int(max(0, world_start[0] - self.x_chunk_shift) / self.tile_size), int(world_start[1] / self.tile_size)]
        grid_end = [int(max(0, world_target[0] - self.x_chunk_shift) / self.tile_size), int(world_target[1] / self.tile_size)]

        grid_start[0] = clamp(grid_start[0], 0, len(self.binary_map[0]))
        grid_start[1] = clamp(grid_start[1], 0, len(self.binary_map))

        grid_end[0] = clamp(grid_end[0], 0, len(self.binary_map[0]))
        grid_end[1] = clamp(grid_end[1], 0, len(self.binary_map))

        path = self.room_pathfinder.find_path(grid_start, grid_end)

        return path

    def world_pos(self, tile_pos):
        return [tile_pos[0] * self.tile_size + self.x_chunk_shift, tile_pos[1] * self.tile_size]

    def draw(self, surf, scroll):
        for rect in self.rects:
            pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(rect.x - scroll[0], rect.y - scroll[1], rect.w, rect.h))

        for node in self.train_draw_path:
            world_pos = self.world_pos(node.grid_pos)

            pygame.draw.rect(surf, (75, 75, 75), pygame.Rect(world_pos[0] - scroll[0], world_pos[1] - scroll[1], 32, 32))

        if self.train_path:
            pygame.draw.circle(surf, (255, 255, 0), [self.train_path[-1][0] + self.tile_size / 2 - scroll[0],
                                                     self.train_path[-1][1] + self.tile_size / 2 - scroll[1]], self.tile_size / 2)


class Hp:
    def __init__(self, max_hp):
        self.hp = max_hp
        self.max_hp = max_hp

        self.kb = 0

        self.alive = True

    def update(self, dt=1):
        self.kb -= 1 * dt

    def damage(self, amount):
        if self.kb > 0:
            return

        self.hp -= amount

        self.kb = 15

        if self.hp <= 0:
            self.alive = False

    def draw(self, surf, scroll, entity_pos, offset=[0, -20]):
        line_a = [entity_pos[0] + offset[0] - 20 - scroll[0], entity_pos[1] + offset[1] - scroll[1]]
        line_b = [entity_pos[0] + offset[0] + 20 - scroll[0], entity_pos[1] + offset[1] - scroll[1]]

        pygame.draw.line(surf, (50, 50, 50), line_a, line_b, 4)

        if not self.alive:
            return

        line_a[0] += 2
        line_b = [line_a[0] + 36 * (self.hp / self.max_hp), line_a[1]]

        pygame.draw.line(surf, (0, 255, 0), line_a, line_b, 2)


class Entity:
    def __init__(self, pos, size, speed=2, movement_reaction=3):
        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.size = size
        self.col = False

        self.movement = pygame.Vector2(0, 0)
        self.movement_dynamics = [SecondOrderDynamics(movement_reaction, 1, 0, 0),
                                  SecondOrderDynamics(movement_reaction, 1, 0, 0)]

        self.speed_dynamics = SecondOrderDynamics(1, 1, 0, speed)
        self.speed_target = speed

    def move(self, dt=1, move_iterations=1):
        self.speed_dynamics.update(self.speed_target, dt / 60)

        self.movement_dynamics[0].update(self.movement[0], dt / 60)
        self.movement_dynamics[1].update(self.movement[1], dt / 60)

        movement = [self.movement_dynamics[0].y * self.speed_dynamics.y,
                    self.movement_dynamics[1].y * self.speed_dynamics.y]
        self.pos, self.col = move_circle(self.pos, self.size, movement, game_map.rects, [], dt, move_iterations)

    def move_collisionless(self, dt=1, move_iterations=1):
        self.speed_dynamics.update(self.speed_target, dt / 60)

        self.movement_dynamics[0].update(self.movement[0], dt / 60)
        self.movement_dynamics[1].update(self.movement[1], dt / 60)

        movement = [self.movement_dynamics[0].y * self.speed_dynamics.y,
                    self.movement_dynamics[1].y * self.speed_dynamics.y]
        self.pos, self.col = move_circle(self.pos, self.size, movement, [], [], dt, move_iterations)

    def debug_draw(self, surf, scroll, color=(255, 0, 0)):
        pygame.draw.circle(surf, color, [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], self.size)


class Bullet(Entity):
    def __init__(self, owner_type, pos, angle, speed=4, size=4, dmg=1, color=(255, 255, 255)):
        self.owner_type = owner_type

        self.lifetime = 720

        self.angle = angle

        self.alive = True

        self.color = color

        self.dmg = dmg

        super().__init__(pos, size, speed, 6)

    def update(self, enemies, allies, dt=1.0):
        self.lifetime -= 1 * dt

        self.movement = [math.cos(self.angle), math.sin(self.angle)]

        if self.col or self.lifetime <= 0:
            self.alive = False

        if self.owner_type != Enemy:
            for enemy in enemies:
                self.hit(enemy)

        if self.owner_type != Ally:
            for ally in allies:
                self.hit(ally)

        self.move(dt, 1)

    def hit(self, other):
        if collision_circle(self.pos, self.size, other.pos, other.size):
            other.hp.damage(self.dmg)
            self.alive = False

    def draw(self, surf, scroll):
        super().debug_draw(surf, scroll, self.color)


class Weapon:
    def __init__(self, dmg, radius, cooldown, range_weapon=False):
        self.range_weapon = range_weapon

        self.dmg = dmg
        self.radius = radius

        self.cooldown_time = 0
        self.attack_time = 0
        self.cooldown = cooldown

    def update(self, dt=1):
        self.attack_time -= 1 * dt
        self.cooldown_time -= 1 * dt

    def hit(self, entity, other):
        if self.range_weapon:
            return

        if self.attack_time > 0 and collision_circle(entity.pos, entity.weapon.radius, other.pos, other.size):
            other.hp.damage(self.dmg)

    def attack(self, entity, other):
        if self.cooldown_time > 0:
            return

        self.cooldown_time = self.cooldown
        if not self.range_weapon:
            self.attack_time = 5
            return

        angle = math.atan2(other.pos[1] - entity.pos[1], other.pos[0] - entity.pos[0])
        pos = entity.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * entity.size * 2

        bullets.append(Bullet(type(entity), pos, angle, dmg=self.dmg))

    def draw(self, surf, pos, color):
        if self.attack_time > 0:
            pygame.draw.circle(surf, color, pos, self.radius, 4)


class Player(Entity):
    def __init__(self, pos):
        self.weapon = Weapon(1, 24, 15)

        self.regroup = False
        self.regroup_range = 80

        super().__init__(pos, 12)

    def update(self, dt: int or float = 1):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_a]:
            self.movement[0] += -2
        if keys[pygame.K_d]:
            self.movement[0] += 2
        if keys[pygame.K_w]:
            self.movement[1] += -2
        if keys[pygame.K_s]:
            self.movement[1] += 2

        if keys[pygame.K_SPACE]:
            self.weapon.attack(self, self)

        self.regroup = keys[pygame.K_LSHIFT]

        self.move(dt, 1)
        self.weapon.update(dt)

        self.movement = [0, 0]

    def draw(self, surf, scroll, color=(0, 255, 0)):
        self.weapon.draw(surf, [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], (150, 255, 0))

        super().debug_draw(surf, scroll, color)

        if self.regroup:
            pygame.draw.circle(surf, (175, 175, 255), [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], self.regroup_range, 2)


class Enemy(Entity):
    def __init__(self, pos, hp=3, speed=2, flying=False, size=12, dmg=0.5, color=(255, 0, 0)):
        self.color = color
        self.hp = Hp(hp)

        self.weapon = Weapon(dmg, size + 4, 60)

        self.speed = speed

        self.move_func = super().move
        if flying:
            self.move_func = super().move_collisionless

        self.target_path = []

        super().__init__(pos, size, self.speed)

    def follow_path(self, target, min_target_dist=48):
        if self.move_func == super().move_collisionless:
            angle = math.atan2(target[1] - self.pos[1], target[0] - self.pos[0])

            return [math.cos(angle), math.sin(angle)]

        if math.dist(self.pos, target) <= min_target_dist:
            self.target_path = []

            angle = math.atan2(target[1] - self.pos[1], target[0] - self.pos[0])

            return [math.cos(angle), math.sin(angle)]

        if not self.target_path or math.dist(game_map.world_pos(self.target_path[-1].grid_pos), target) > 80:
            self.target_path = game_map.get_path(self.pos, target)

            if self.target_path:
                path_pos = game_map.world_pos(self.target_path[0].grid_pos)
                path_pos = [path_pos[0] + game_map.tile_size / 2, path_pos[1] + game_map.tile_size / 2]

                angle = math.atan2(path_pos[1] - self.pos[1], path_pos[0] - self.pos[0])

                return [math.cos(angle), math.sin(angle)]

            angle = math.atan2(target[1] - self.pos[1], target[0] - self.pos[0])

            return [math.cos(angle), math.sin(angle)]

        path_pos = game_map.world_pos(self.target_path[0].grid_pos)
        path_pos = [path_pos[0] + game_map.tile_size / 2, path_pos[1] + game_map.tile_size / 2]

        angle = math.atan2(path_pos[1] - self.pos[1], path_pos[0] - self.pos[0])

        if math.dist(self.pos, path_pos) <= 16:
            self.target_path.pop(0)

        return [math.cos(angle), math.sin(angle)]

    def update(self, player, train, allies, dt: int or float = 1):
        self.hp.update(dt)
        self.weapon.update(dt)

        player.weapon.hit(player, self)

        valid_attack_points = []
        for point in train.defence_points:
            if point.hp.alive:
                valid_attack_points.append(point)

        for ally in sorted(allies, key=lambda x: math.dist(x.pos, self.pos)):
            ally_dist = math.dist(ally.pos, self.pos)
            if ally_dist < self.weapon.radius:
                self.weapon.attack(self, ally)
            elif ally_dist < 96:
                self.movement = self.follow_path(ally.pos)
                self.speed_target = self.speed

            self.weapon.hit(self, ally)

        if not valid_attack_points:
            return

        target = sorted(valid_attack_points, key=lambda point: math.dist(point.pos, self.pos))[0]

        self.movement = self.follow_path(target.pos)

        if self.hp.kb > 0:
            self.speed_target = abs(self.speed_target) * -0.99
        else:
            self.speed_target = self.speed

            self.weapon.attack(self, target)
            self.weapon.hit(self, target)

        self.move_func(dt, 1)

    def draw(self, surf, scroll):
        super().debug_draw(surf, scroll, self.color)

        self.hp.draw(surf, scroll, self.pos)


class Ally(Entity):
    def __init__(self, train, pos, speed=2, size=12, dmg=1, range_ally=False, color=(150, 150, 255)):
        self.color = color

        self.hp = Hp(10)

        self.weapon = Weapon(dmg, size + 4, 20)
        if range_ally:
            self.weapon = Weapon(dmg, 100, 40, True)

        self.speed = speed

        self.train_offset = [pos[0] - train.pos[0], pos[1] - train.pos[1]]

        self.target_path = []

        super().__init__(pos, size, self.speed)

    def follow_path(self, target, min_target_dist=48):
        if math.dist(self.pos, target) <= min_target_dist:
            self.target_path = []

            angle = math.atan2(target[1] - self.pos[1], target[0] - self.pos[0])

            return [math.cos(angle), math.sin(angle)]

        if not self.target_path:
            self.target_path = game_map.get_path(self.pos, target)

            angle = math.atan2(target[1] - self.pos[1], target[0] - self.pos[0])

            return [math.cos(angle), math.sin(angle)]

        path_pos = game_map.world_pos(self.target_path[0].grid_pos)
        path_pos = [path_pos[0] + game_map.tile_size / 2, path_pos[1] + game_map.tile_size / 2]

        angle = math.atan2(path_pos[1] - self.pos[1], path_pos[0] - self.pos[0])

        if math.dist(self.pos, path_pos) <= 16:
            self.target_path.pop(0)

        return [math.cos(angle), math.sin(angle)]

    def update(self, player, train, enemies, allies, dt: int or float = 1):
        self.hp.update(dt)
        self.weapon.update(dt)

        if not self.hp.alive:
            if collision_circle(player.pos, player.size, self.pos, self.size):
                self.hp = Hp(10)

            return

        if player.regroup and math.dist(self.pos, player.pos) <= player.regroup_range:
            self.train_offset = [player.pos[0] - train.pos[0], player.pos[1] - train.pos[1]]

            self.movement = self.follow_path(player.pos)
            self.move(dt, 1)

            return

        target = [train.pos[0] + self.train_offset[0], train.pos[1] + self.train_offset[1]]

        self.movement = self.follow_path(target)

        if math.dist(target, self.pos) < 32:
            self.speed_target = 0.5
        else:
            self.speed_target = self.speed

        for enemy in sorted(enemies, key=lambda x: math.dist(x.pos, self.pos)):
            enemy_dist = math.dist(enemy.pos, self.pos)
            if enemy_dist < self.weapon.radius:
                self.weapon.attack(self, enemy)
            elif enemy_dist < self.weapon.radius * 6:
                self.movement = self.follow_path(enemy.pos)
                self.speed_target = self.speed

            self.weapon.hit(self, enemy)

        boid_entities = 1
        for other in allies:
            if other is self:
                continue

            if other.hp.alive and self.pos.distance_to(other.pos) <= 32:
                boid_entities += 1
                enemy_angle = math.atan2(self.pos[1] - other.pos[1], self.pos[0] - other.pos[0])
                self.movement[0] += math.cos(enemy_angle)
                self.movement[1] += math.sin(enemy_angle)

        self.movement[0] /= boid_entities
        self.movement[1] /= boid_entities

        self.move(dt, 1)

    def draw(self, surf, scroll):
        if not self.hp.alive:
            super().debug_draw(surf, scroll, (150, 150, 150))

            # Drawing X

            draw_pos = [self.pos[0] - scroll[0], self.pos[1] - scroll[1]]
            pygame.draw.line(surf, (255, 50, 50),
                             [draw_pos[0] - self.size, draw_pos[1] - self.size],
                             [draw_pos[0] + self.size, draw_pos[1] + self.size], 6)
            pygame.draw.line(surf, (255, 50, 50),
                             [draw_pos[0] + self.size, draw_pos[1] - self.size],
                             [draw_pos[0] - self.size, draw_pos[1] + self.size], 6)
            for y in [-1, 1]:
                for x in [-1, 1]:
                    pygame.draw.circle(surf, (255, 50, 50), [draw_pos[0] + self.size * x, draw_pos[1] + self.size * y], 3)

            return

        self.weapon.draw(surf, [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], (175, 175, 255))

        super().debug_draw(surf, scroll, self.color)

        self.hp.draw(surf, scroll, self.pos)


class DefencePoint:
    def __init__(self, pos, hp=10):
        self.pos = pos
        self.size = 12

        self.hp = Hp(hp)

    def draw(self, surf, scroll, color=(255, 255, 0)):
        pygame.draw.circle(surf, color, [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], self.size)
        self.hp.draw(surf, scroll, self.pos)


class Train:
    def __init__(self, pos, defence_points=3):
        self.pos = pygame.math.Vector2(pos[0], pos[1])
        self.last_pos = [self.pos.copy() for _ in range(360)]

        self.movement = [0, 0]

        self.stopped = False

        self.target_path = []

        self.defence_points = []
        for i in range(defence_points):
            self.defence_points.append(DefencePoint([pos[0] - (i + 1) * 50, pos[1]], 10))

    def follow_path(self, target):
        if not self.target_path:
            self.target_path = game_map.get_path(self.pos, target)

            return [0, 0]

        path_pos = game_map.world_pos(self.target_path[0].grid_pos)
        path_pos = [path_pos[0] + game_map.tile_size / 2, path_pos[1] + game_map.tile_size / 2]

        angle = math.atan2(path_pos[1] - self.pos[1], path_pos[0] - self.pos[0])

        if math.dist(self.pos, path_pos) <= 16:
            self.target_path.pop(0)

        return [math.cos(angle), math.sin(angle)]

    def update(self, dt: int or float = 1):
        if self.stopped:
            return

        self.movement = self.follow_path(game_map.train_path[0])
        if math.dist(self.pos, game_map.train_path[0]) < 32:
            game_map.train_path.pop(0)

        self.pos[0] += self.movement[0] * 0.5 * dt
        self.pos[1] += self.movement[1] * 0.5 * dt

        self.last_pos.append(self.pos.copy())
        if len(self.last_pos) > 360:
            self.last_pos.pop(0)

        for i, point in enumerate(self.defence_points):
            point.hp.update(dt)

            try:
                point.pos[0] = self.last_pos[i * 120][0]
                point.pos[1] = self.last_pos[i * 120][1]
            except IndexError:
                pass

    def draw(self, surf, scroll, color=(255, 255, 0)):
        angle = math.atan2(self.movement[1], self.movement[0])

        pygame.draw.circle(surf, color, [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], 12)
        pygame.draw.line(surf, color, [self.pos[0] - scroll[0], self.pos[1] - scroll[1]],
                         [self.pos[0] + 24 * math.cos(angle) - scroll[0], self.pos[1] + 24 * math.sin(angle) - scroll[1]], 6)

        for point in self.defence_points:
            point.draw(surf, scroll, color)


game_map = Map()

player = Player([400, 200])

coins = 0

bullets = []

enemies = []

train = Train([400, 225], 3)
allies = [Ally(train, [400, 200]), Ally(train, [400, 250]), Ally(train, [425, 225]),
          Ally(train, [400, 225]), Ally(train, [375, 225])]


enemy_types = [
    {"hp": 6, "speed": 2, "flying": False, "size": 12, "dmg": 0.5, "color": (255, 0, 0)},
    {"hp": 2, "speed": 3, "flying": False, "size": 6, "dmg": 0.125, "color": (255, 0, 255)},
    {"hp": 12, "speed": 1, "flying": False, "size": 18, "dmg": 1, "color": (255, 0, 0)},
    {"hp": 3, "speed": 2, "flying": True, "size": 6, "dmg": 0.25, "color": (255, 150, 0)},
]

enemy_waves = [[0, 0, 0], [3, 3, 3, 3], [1, 1, 1, 1, 1], [2], [2, 0, 0], [2, 1, 1, 1, 1], [2, 3], [3, 3, 1, 1, 1]]

threat_level = 60

dt = 1

last_time = time.time() - 1


def generate_random_polygon(center, verticies=4, min_dist=16, max_dist=32):
    polygon_lines = []

    corners = []
    angle = random.randint(0, 180)

    for i in range(verticies):
        angle += 360 / verticies

        dist = random.randint(min_dist, max_dist)

        corners.append([center[0] + math.sin(math.radians(angle)) * dist,
                        center[1] + math.cos(math.radians(angle)) * dist])

    for i in range(len(corners)):
        polygon_lines.append([corners[i].copy(), corners[i - 1].copy()])

    return polygon_lines


while True:
    dt = time.time() - last_time
    dt *= 60
    last_time = time.time()

    if any(point.hp.alive for point in train.defence_points):
        display.fill((100, 100, 100))

        mx, my = pygame.mouse.get_pos()
        mx /= scale
        my /= scale

        scroll[0] += (train.pos[0] - scroll[0] - int(display.get_width() / 2)) / 100

        # Update

        game_map.draw(display, scroll)

        player.update(dt)
        player.draw(display, scroll)

        train.update(dt)
        train.draw(display, scroll)

        for i, enemy in enumerate(enemies):
            enemy.update(player, train, allies, dt)
            enemy.draw(display, scroll)

            if not enemy.hp.alive:
                enemies.pop(i)

        for i, ally in enumerate(allies):
            ally.update(player, train, enemies, allies, dt)
            ally.draw(display, scroll)

            if not ally.hp.alive and ally.pos[0] < scroll[0] - ally.size:
                allies.pop(i)

        for i, bullet in enumerate(bullets):
            bullet.update(enemies, allies, dt)
            bullet.draw(display, scroll)

            if not bullet.alive:
                bullets.pop(i)

        if train.pos[0] > 800 and not train.stopped:
            threat_level += 1 * dt

            # Spawn Allies

            if not game_map.train_path:
                train.stopped = True
                train.target_path = []
                game_map.add_chunks(game_map.max_updated_chunks)

                coins += 60 + int(threat_level / 60 / 100) * 30

                # print('reached station, 1 new ally found')

                for _ in range(1):
                    allies.append(Ally(train, train.pos.copy()))

            # Spawn enemies

            # print(f"spawn freq: {int(60 + threat_level / 300) / 60}")

            if int(threat_level % (60 + threat_level / 300)) == 0 and random.randint(0, 100) < 15 + threat_level / 360:
                for enemy_type in random.choice(enemy_waves):
                    stats = enemy_types[enemy_type]

                    enemies.append(Enemy([train.pos[0] + 400 + random.randint(16, 80),
                                          train.pos[1] + (255 + random.randint(16, 80)) * random.choice([1, -1])],
                                         stats["hp"], stats["speed"], stats["flying"], stats["size"], stats["dmg"], stats["color"]))

        if train.stopped:
            font_size = font.get_font_size(f"THE TRAIN IS NOW STOPPED. PRESS ENTER TO CONTINUE THE RIDE", 2)
            font.render(display, f"THE TRAIN STOPPED. PRESS ENTER TO CONTINUE THE RIDE", [400 - font_size[0] / 2, 335], 2)

            font_size = font.get_font_size(f"NUM 1-3 TO REPAIR A TRAIN PART, 4 TO BUY MELEE ALLY, 5 TO BUY RANGE ALLY", 2)
            font.render(display, f"NUM 1-3 TO REPAIR A TRAIN PART, 4 TO BUY MELEE ALLY, 5 TO BUY RANGE ALLY", [400 - font_size[0] / 2, 355], 2)

            font_size = font.get_font_size(f"MELEE ALLY - 55, RANGE ALLY - 70, REPAIR - 20, REPAIR DEAD PART - 60", 2)
            font.render(display, f"MELEE ALLY - 55, RANGE ALLY - 70, REPAIR - 20, REPAIR DEAD PART - 60", [400 - font_size[0] / 2, 375], 2)
        else:
            font_size = font.get_font_size(f"PROTECT THE TRAIN UNTIL IT REACHES THE STATION", 2)
            font.render(display, f"PROTECT THE TRAIN UNTIL IT REACHES THE STATION", [400 - font_size[0] / 2, 375], 2)

        font.render(display, f"FPS: {round(fps_clock.get_fps(), 0)} [{fps_clock.get_rawtime()} MS]", [10, 10], 2)
        font.render(display, f"TIME SURVIVED: {int(threat_level / 60)}", [10, 50], 2)
        font.render(display, f"COINS: {coins}", [10, 70], 2)
    else:
        font.render(display, "GAME OVER", [316, 150], 4)

    # Inputs

    for event in pygame.event.get():  # event loop
        if event.type == QUIT:  # check for window quit
            pygame.quit()  # stop pygame
            sys.exit()  # stop script
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if train.stopped:
                if coins >= 20:
                    if event.key == K_1 and train.defence_points[0].hp.alive:
                        train.defence_points[0].hp.hp = train.defence_points[0].hp.max_hp
                        coins -= 20
                    if event.key == K_2 and train.defence_points[1].hp.alive:
                        train.defence_points[1].hp.hp = train.defence_points[1].hp.max_hp
                        coins -= 20
                    if event.key == K_3 and train.defence_points[2].hp.alive:
                        train.defence_points[2].hp.hp = train.defence_points[2].hp.max_hp
                        coins -= 20
                if coins >= 55:
                    if event.key == K_4:
                        allies.append(Ally(train, train.pos.copy()))
                        coins -= 55
                if coins >= 70:
                    if event.key == K_5:
                        allies.append(Ally(train, train.pos.copy(), speed=1, dmg=3, range_ally=True, color=(50, 50, 255)))
                        coins -= 70
                if coins >= 60:
                    if event.key == K_1 and not train.defence_points[0].hp.alive:
                        train.defence_points[0].hp.hp = train.defence_points[0].hp.max_hp
                        train.defence_points[0].hp.alive = True
                        coins -= 60
                    if event.key == K_2 and not train.defence_points[1].hp.alive:
                        train.defence_points[1].hp.hp = train.defence_points[1].hp.max_hp
                        train.defence_points[1].hp.alive = True
                        coins -= 60
                    if event.key == K_3 and not train.defence_points[2].hp.alive:
                        train.defence_points[2].hp.hp = train.defence_points[2].hp.max_hp
                        train.defence_points[2].hp.alive = True
                        coins -= 60

                if event.key == K_RETURN:
                    train.stopped = False
                    threat_level += 60

    surf = pygame.transform.scale(display, WINDOW_SIZE)
    screen.blit(surf, (0, 0))
    fps_clock.tick(120)
    pygame.display.update()
