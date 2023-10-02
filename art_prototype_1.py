import math
import random
import sys
import time

# initialize frameworks
import pygame.transform

pygame.init()

from pygame.locals import *
from Framework.collisions import *
from Framework.second_order_system import *
from Framework.main_framework import Font, clip
from Framework.pathfinding import *
from Framework.extra_functions import clamp

WINDOW_SIZE = (800, 450)  # to not use full screen (900, 504) full screen (1366, 768)

scale = 2

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)
pygame.display.set_caption("Art Prototype 1")

font = Font('Framework/font.png')

fps_clock = pygame.time.Clock()

display = pygame.Surface((WINDOW_SIZE[0] / scale, WINDOW_SIZE[1] / scale))

scroll = [0, 0]

colorkey = (172, 50, 50)
spritesheet = pygame.image.load("Sprites/spritesheet_1.png").convert()
head_spritesheet = pygame.image.load("Sprites/head_spritesheet.png").convert()


def point_col(point, tiles):
    for tile in tiles:
        if tile.collidepoint(point):
            return tile

    return None


class Map:
    def __init__(self, tile_size=32):
        self.tile_size = tile_size

        self.binary_map = [["0" for _ in range(28)] for _ in range(14)]

        self.room_pathfinder = AStarRegionSystem(self.binary_map, 14, is_char=True)

        # Draw stuff

        self.rects = []

        self.forbidden_tiles = [[12, 6], [12, 7], [13, 6], [13, 7], [14, 6], [14, 7],
                                [12, 5], [12, 8], [13, 5], [13, 8], [14, 5], [14, 8]]

        self.add_obstacles()

    def add_obstacle(self, binary_map, x, y, w, h, forbidden_nodes=[]):
        rects = []

        for y_pos in range(h):
            for x_pos in range(w):
                try:
                    if any(node == [x + x_pos, y + y_pos] for node in forbidden_nodes):
                        continue
                    binary_map[y + y_pos][x + x_pos] = "1"
                    rects.append(pygame.Rect((x + x_pos) * self.tile_size, (y + y_pos) * self.tile_size, self.tile_size, self.tile_size))
                except IndexError:
                    pass

        return binary_map, rects

    def add_obstacles(self):
        # Rects

        for _ in range(6):
            self.binary_map, obstacle_rects = self.add_obstacle(self.binary_map, random.randint(0, 25),
                                                                random.randint(0, 3) + 10 * random.randint(0, 1),
                                                                random.randint(2, 4), random.randint(2, 4), self.forbidden_tiles)
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

        self.room_pathfinder = AStarRegionSystem(self.binary_map, 14, is_char=True)

    def get_path(self, world_start, world_target):
        grid_start = [int(world_start[0] / self.tile_size), int(world_start[1] / self.tile_size)]
        grid_end = [int(world_target[0] / self.tile_size), int(world_target[1] / self.tile_size)]

        grid_start[0] = clamp(grid_start[0], 0, len(self.binary_map[0]))
        grid_start[1] = clamp(grid_start[1], 0, len(self.binary_map))

        grid_end[0] = clamp(grid_end[0], 0, len(self.binary_map[0]))
        grid_end[1] = clamp(grid_end[1], 0, len(self.binary_map))

        path = self.room_pathfinder.find_path(grid_start, grid_end)

        return path

    def world_pos(self, tile_pos):
        return [tile_pos[0] * self.tile_size, tile_pos[1] * self.tile_size]

    def draw(self, surf, scroll):
        for rect in self.rects:
            pygame.draw.rect(surf, (0, 0, 0), pygame.Rect(rect.x - scroll[0], rect.y - scroll[1], rect.w, rect.h))


class Hp:
    def __init__(self, max_hp, max_mana=0):
        self.hp = max_hp
        self.max_hp = max_hp

        self.mana_regeneration_cooldown = 0
        self.mana = max_mana
        self.max_mana = max_mana

        self.kb = 0

        self.alive = True

    def update(self, dt=1):
        self.kb -= 1 * dt
        self.mana_regeneration_cooldown -= 1 * dt

        if self.mana_regeneration_cooldown <= 0:
            self.mana_regeneration_cooldown = 0

            self.mana += 1 * dt

        self.mana = min(self.mana, self.max_mana)
        self.hp = clamp(self.hp, 0, self.max_hp)

    def drain_mana(self, amount, regeneration_cooldown=None):
        self.mana -= amount

        if regeneration_cooldown is None:
            regeneration_cooldown = amount * 2

        self.mana_regeneration_cooldown += regeneration_cooldown

        if self.mana < 0:
            self.hp += self.mana / 10

            if self.hp <= 0:
                self.alive = False

                self.hp = 0

        self.mana = max(0, self.mana)

    def damage(self, amount):
        if self.kb > 0:
            return

        self.hp -= amount

        self.kb = 30

        if self.hp <= 0:
            self.alive = False

            self.hp = 0

    def draw_bar(self, surf, scroll, percent, entity_pos, offset=[0, -20], color=(0, 255, 0)):
        line_a = [entity_pos[0] + offset[0] - 20 - scroll[0], entity_pos[1] + offset[1] - scroll[1]]
        line_b = [entity_pos[0] + offset[0] + 20 - scroll[0], entity_pos[1] + offset[1] - scroll[1]]

        pygame.draw.line(surf, (50, 50, 50), line_a, line_b, 4)

        if percent <= 0:
            return

        line_a[0] += 2
        line_b = [line_a[0] + 36 * percent, line_a[1]]

        pygame.draw.line(surf, color, line_a, line_b, 2)

    def draw(self, surf, scroll, entity_pos):
        self.draw_bar(surf, scroll, self.hp / self.max_hp, entity_pos, [0, -25], (0, 255, 0))

        if not self.max_mana:
            return

        self.draw_bar(surf, scroll, self.mana / self.max_mana, entity_pos, [0, -20], (0, 150, 150))


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


class PlayerCosmetic:
    def __init__(self, entity):
        self.entity = entity

        self.flip = False

        """
        "hat": clip(spritesheet, 0, 0, 23, 19, colorkey),
        "head": clip(spritesheet, 24, 0, 16, 16, colorkey),
        """

        self.sprites = {
            "head": [clip(head_spritesheet, i * 16, 0, 16, 16, colorkey) for i in range(10)],
            "body": clip(spritesheet, 41, 0, 22, 17, colorkey),
            "broom": clip(spritesheet, 0, 21, 46, 11, colorkey),
        }

        self.head_pos = [SecondOrderDynamics(4, 0.3, 0, self.entity.pos[0]),
                         SecondOrderDynamics(4, 0.3, 0, self.entity.pos[1] - 12)]
        self.head_bobbing = 0

    def update(self, dt=1):
        self.flip = bool(self.entity.movement_dynamics[0].y < 0)

        self.head_pos[0].update(self.entity.pos[0] - self.entity.movement_dynamics[0].y * 2, dt / 60)

        self.head_bobbing += 1 * dt
        if abs(self.entity.movement_dynamics[0].y) < 0.2:
            self.head_pos[1].update(self.entity.pos[1] - 12 + math.sin(self.head_bobbing / 20) * 2, dt / 60)
        else:
            self.head_pos[1].update(self.entity.pos[1] - 12 + math.sin(self.head_bobbing / 5) * 2, dt / 60)

    def draw_part(self, surf, scroll, part_name, angle, offset):
        img = pygame.transform.flip(self.sprites[part_name], self.flip, False)
        img = pygame.transform.rotate(img, angle)
        surf.blit(img, [self.entity.pos[0] - scroll[0] - int(img.get_width() / 2) + offset[0],
                        self.entity.pos[1] - scroll[1] - int(img.get_height() / 2) + offset[1]])

    def draw_spritestack(self, surf, scroll, part_name, angle, offset, y_offset=-1):
        for i, img in enumerate(self.sprites[part_name]):
            img = pygame.transform.rotate(img, angle)
            surf.blit(img, [self.entity.pos[0] - scroll[0] - int(img.get_width() / 2) + offset[0],
                            self.entity.pos[1] - scroll[1] - int(img.get_height() / 2) + offset[1] + y_offset * i])

    def draw(self, surf, scroll):
        broom_angle = self.entity.movement_dynamics[0].y * 5 + (self.entity.movement_dynamics[1].y * 15 * math.copysign(1, -self.entity.movement_dynamics[0].y))
        self.draw_part(surf, scroll, "broom", broom_angle, [0, 5])

        body_angle = self.entity.movement_dynamics[0].y * 5 + (self.entity.movement_dynamics[1].y * 7.5 * math.copysign(1, -self.entity.movement_dynamics[0].y))
        self.draw_part(surf, scroll, "body", body_angle, [0, 0])

        head_angle = math.degrees(math.atan2(self.entity.movement_dynamics[1].y, -self.entity.movement_dynamics[0].y) - math.pi / 2)
        self.draw_spritestack(surf, scroll, "head", head_angle, [self.head_pos[0].y - self.entity.pos[0], self.head_pos[1].y - self.entity.pos[1]])

        """
        self.draw_part(surf, scroll, "head", head_angle, [self.head_pos[0].y - self.entity.pos[0], self.head_pos[1].y - self.entity.pos[1]])
        self.draw_part(surf, scroll, "hat", head_angle, [-self.entity.movement_dynamics[0].y * 10, self.head_pos[1].y - self.entity.pos[1] - 12])
        """


class Player(Entity):
    def __init__(self, pos):
        self.hp = Hp(30, 50)

        self.movement_scheme = {"up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d, "attack": pygame.K_LSHIFT}

        self.color = (0, 255, 0)

        super().__init__(pos, 12)

        self.cosmetic = PlayerCosmetic(self)

    def update(self, dt: int or float = 1):
        self.hp.update(dt)

        keys = pygame.key.get_pressed()

        if keys[self.movement_scheme["left"]]:
            self.movement[0] += -2
        if keys[self.movement_scheme["right"]]:
            self.movement[0] += 2
        if keys[self.movement_scheme["up"]]:
            self.movement[1] += -2
        if keys[self.movement_scheme["down"]]:
            self.movement[1] += 2

        self.move(dt, 1)
        self.movement = [0, 0]

        self.cosmetic.update(dt)

    def draw(self, surf, scroll):
        # super().debug_draw(surf, scroll, self.color)
        self.cosmetic.draw(surf, scroll)

        # ddself.hp.draw(surf, scroll, self.pos)


game_map = Map()

player = Player([400, 200])

dt = 1

last_time = time.time() - 1


while True:
    dt = time.time() - last_time
    dt *= 60
    last_time = time.time()

    display.fill((100, 100, 100))

    mx, my = pygame.mouse.get_pos()
    mx /= scale
    my /= scale

    # Update

    game_map.draw(display, scroll)

    player.update(dt)
    player.draw(display, scroll)

    # Inputs

    for event in pygame.event.get():  # event loop
        if event.type == QUIT:  # check for window quit
            pygame.quit()  # stop pygame
            sys.exit()  # stop script
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

    surf = pygame.transform.scale(display, WINDOW_SIZE)
    screen.blit(surf, (0, 0))
    fps_clock.tick(120)
    pygame.display.update()
