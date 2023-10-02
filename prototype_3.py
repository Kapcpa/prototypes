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

scale = 1

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)
pygame.display.set_caption("Prototype 3 - submarine with a fricking payload idk")

font = Font('Framework/font.png')

fps_clock = pygame.time.Clock()

display = pygame.Surface((WINDOW_SIZE[0] / scale, WINDOW_SIZE[1] / scale))

scroll = [0, 0]


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
    def __init__(self, owner_type, pos, angle, speed=6, size=6, dmg=1, color=(255, 255, 255)):
        self.owner_type = owner_type

        self.lifetime = 720

        self.angle = angle

        self.alive = True

        self.color = color

        self.dmg = dmg

        super().__init__(pos, size, speed, 10)

    def update(self, enemies, player, defence_object, dt=1.0):
        self.lifetime -= 1 * dt

        self.movement = [math.cos(self.angle), math.sin(self.angle)]

        if self.owner_type != Enemy:
            for enemy in enemies:
                self.hit(enemy)

        if self.owner_type != Player:
            self.hit(player)

        self.hit(defence_object)

        if self.col or self.lifetime <= 0:
            self.alive = False

        self.move(dt, 1)

    def hit(self, other):
        if collision_circle(self.pos, self.size, other.pos, other.size):
            other.hp.damage(self.dmg)
            other.movement = self.movement.copy()
            other.speed_dynamics.y *= 1.5
            other.speed_dynamics.y = min(other.speed_dynamics.y, 6)
            self.alive = False

    def draw(self, surf, scroll):
        super().debug_draw(surf, scroll, self.color)


class Weapon:
    def __init__(self, dmg, cooldown, bullets_amount=1):
        self.dmg = dmg

        self.bullets_amount = bullets_amount

        self.cooldown_time = 0
        self.cooldown = cooldown

    def update(self, dt=1):
        self.cooldown_time -= 1 * dt

    def attack(self, entity, target=None):
        if self.cooldown_time > 0:
            return

        self.cooldown_time = self.cooldown

        for i in range(self.bullets_amount):
            if target is None:
                angle = entity.angle + (i - self.bullets_amount / 2 + 0.5) * math.pi / 8
            else:
                angle = math.atan2(target.pos[1] - entity.pos[1], target.pos[0] - entity.pos[0]) + (i - self.bullets_amount / 2 + 0.5) * math.pi / 8

            pos = entity.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * entity.size * 2

            bullets.append(Bullet(type(entity), pos, angle, dmg=self.dmg))


submarine_spritesheet = pygame.image.load("Sprites/submarine_spritesheet.png").convert()
spritesheets = {
    "submarine": [clip(submarine_spritesheet, i * 38, 0, 38, 32, (172, 50, 50)) for i in range(4)]
}


class Cosmetics:
    def __init__(self, entity, spritesheet_name):
        self.entity = entity
        self.sprites = spritesheets[spritesheet_name]
        self.img_angles = {0: [[0, 30], [150, 180]], 1: [[30, 60], [120, 150]], 2: [[60, 75], [105, 120]], 3: [[75, 105]]}

    def draw(self, surf, scroll):
        angle = math.degrees(self.entity.angle)

        img = self.sprites[0]
        for img_id in self.img_angles:
            if any(section[0] <= angle % 180 < section[1] for section in self.img_angles[img_id]):
                img = self.sprites[img_id]

        img = pygame.transform.rotate(pygame.transform.flip(img, False, math.cos(self.entity.angle) < 0), -angle)

        surf.blit(img, (self.entity.pos[0] - scroll[0] - int(img.get_width() / 2),
                        self.entity.pos[1] - scroll[0] - int(img.get_height() / 2)))


class Enemy(Entity):
    def __init__(self, pos, hp=8, speed=3, size=12, dmg=4, color=(255, 0, 0)):
        self.color = color
        self.hp = Hp(hp)

        self.weapon = Weapon(dmg, 60, 1)

        self.speed = speed

        self.target_path = []

        super().__init__(pos, size, self.speed)

    def follow_path(self, target, min_target_dist=48):
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

    def update(self, player, dt: int or float = 1):
        self.hp.update(dt)
        self.weapon.update(dt)

        if self.hp.kb <= 0:
            player_dist = math.dist(player.pos, self.pos)
            if player_dist < 128:
                self.weapon.attack(self, player)

            self.movement = [0, 0]
            self.speed_target = 0
            if player_dist > 80:
                self.movement = self.follow_path(player.pos)
                self.speed_target = self.speed
        else:
            self.speed_target = abs(self.speed_target) * 0.99

        self.move(dt, 1)

    def draw(self, surf, scroll):
        super().debug_draw(surf, scroll, self.color)

        self.hp.draw(surf, scroll, self.pos)


class Player(Entity):
    def __init__(self, pos):
        self.hp = Hp(80)

        self.weapon = Weapon(2, 15, 3)

        self.movement_scheme = {
            "forward": pygame.K_UP,
            "left": pygame.K_LEFT,
            "right": pygame.K_RIGHT,
            "attack": pygame.K_x
        }

        self.angular_speed = 0.07
        self.normal_speed = 4

        self.angle = 0

        self.cosmetics = Cosmetics(self, "submarine")

        super().__init__(pos, 12, self.normal_speed)

    def update(self, load_object, dt: int or float = 1):
        keys = pygame.key.get_pressed()

        self.speed_target = 0
        if keys[self.movement_scheme["left"]]:
            self.angle -= self.angular_speed * dt
        if keys[self.movement_scheme["right"]]:
            self.angle += self.angular_speed * dt
        if keys[self.movement_scheme["forward"]]:
            if load_object.attached:
                self.speed_target = load_object.normal_speed
            else:
                self.speed_target = self.normal_speed

            self.movement = [math.cos(self.angle), math.sin(self.angle)]

        if keys[self.movement_scheme["attack"]]:
            if load_object.attached:
                load_object.attached = False
                load_object.attached_timer = 60
            else:
                self.weapon.attack(self)

        self.move(dt, 1)
        self.weapon.update(dt)
        self.hp.update(dt)

    def draw(self, surf, scroll):
        super().debug_draw(surf, scroll, (0, 255, 0))
        self.cosmetics.draw(surf, scroll)

        self.hp.draw(surf, scroll, self.pos)


class LoadObject(Entity):
    def __init__(self, pos, min_dist=80, color=(0, 255, 0)):
        self.attached = True
        self.attached_timer = 0

        self.min_dist = min_dist

        self.normal_speed = 2.75

        self.color = color

        super().__init__(pos, 12, self.normal_speed)

    def update(self, player, dt: int or float = 1):
        self.attached_timer -= 1 * dt
        if self.attached_timer <= 0 and collision_circle(self.pos, self.size, player.pos, player.size):
            self.attached = True

        if math.dist(player.pos, self.pos) <= self.min_dist or not self.attached or player.speed_target == 0:
            self.speed_target = 0
        else:
            self.speed_target = self.normal_speed
            angle = math.atan2(player.pos[1] - self.pos[1], player.pos[0] - self.pos[0])
            self.movement = [math.cos(angle), math.sin(angle)]

        self.move(dt, 1)

    def draw(self, surf, scroll):
        super().debug_draw(surf, scroll, self.color)


class DefenceObject(LoadObject):
    def __init__(self, pos):
        super().__init__(pos, 8)

        self.hp = Hp(60)

    def update(self, player, dt: int or float = 1):
        super().update(player, dt)

        self.hp.update(dt)

    def draw(self, surf, scroll):
        super().draw(surf, scroll)

        self.hp.draw(surf, scroll, self.pos)


game_map = Map()


player = Player([400, 200])

lines = [LoadObject([400, 200], 8, (255, 255, 255)) for _ in range(6)]

defence_object = DefenceObject([400, 200])

bullets = []

enemies = []

enemy_types = [
    {"hp": 6, "speed": 2, "size": 12, "dmg": 4, "color": (255, 0, 0)},
    {"hp": 2, "speed": 3, "size": 6, "dmg": 2, "color": (255, 0, 255)},
    {"hp": 12, "speed": 1.5, "size": 18, "dmg": 8, "color": (255, 0, 0)}
]
enemy_waves = [[0, 0], [1, 1, 1, 1], [2], [2, 0], [2, 1, 1, 1]]

threat_level = 0
waves_stopped = False
upgraded = False


dt = 1

last_time = time.time() - 1


while True:
    dt = time.time() - last_time
    dt *= 60
    last_time = time.time()

    if player.hp.alive and defence_object.hp.alive:
        display.fill((100, 100, 100))

        mx, my = pygame.mouse.get_pos()
        mx /= scale
        my /= scale

        # Draw Map and rope

        game_map.draw(display, scroll)

        if defence_object.attached:
            pygame.draw.line(display, (255, 255, 255),
                             [player.pos[0] - scroll[0], player.pos[1] - scroll[1]],
                             [lines[-1].pos[0] - scroll[0], lines[-1].pos[1] - scroll[1]], 4)

            for i in range(len(lines) - 1):
                pygame.draw.line(display, (255, 255, 255),
                                 [lines[i].pos[0] - scroll[0], lines[i].pos[1] - scroll[1]],
                                 [lines[i + 1].pos[0] - scroll[0], lines[i + 1].pos[1] - scroll[1]], 4)

            pygame.draw.line(display, (255, 255, 255),
                             [lines[0].pos[0] - scroll[0], lines[0].pos[1] - scroll[1]],
                             [defence_object.pos[0] - scroll[0], defence_object.pos[1] - scroll[1]], 4)

        # Update Player

        player.update(defence_object, dt)
        player.draw(display, scroll)

        # Update/draw Defence Object

        if defence_object.attached:
            defence_object.update(lines[0], dt)

            lines[-1].update(player, dt)
            for i, line in enumerate(lines):
                if i >= len(lines) - 1:
                    continue
                line.update(lines[i + 1], dt)
        else:
            defence_object.update(player, dt)
            lines = [LoadObject(player.pos.copy(), 8, (255, 255, 255)) for _ in range(6)]

        defence_object.draw(display, scroll)

        # Update

        for i, bullet in enumerate(bullets):
            bullet.update(enemies, player, defence_object, dt)
            bullet.draw(display, scroll)

            if not bullet.alive:
                bullets.pop(i)

        for i, enemy in enumerate(enemies):
            enemy.update(player, dt)
            enemy.draw(display, scroll)

            if not enemy.hp.alive:
                enemies.pop(i)

        # Wave System

        if not waves_stopped and defence_object.speed_target != 0:
            threat_level += 1 * dt

        # Spawn Enemies

        if int(threat_level % (60 * 40)) == 0:
            waves_stopped = True

        if not waves_stopped and int(threat_level % (240 + threat_level / 300)) == 0 and random.randint(0, 100) < 15 + threat_level / 420:
            for enemy_type in random.choice(enemy_waves):
                stats = enemy_types[enemy_type]

                enemies.append(Enemy([400 + random.randint(400, 450) * random.choice([1, -1]),
                                      225 + random.randint(225, 275) * random.choice([1, -1])],
                                     stats["hp"], stats["speed"], stats["size"], stats["dmg"],
                                     stats["color"]))

        if waves_stopped:
            if upgraded:
                font_size = font.get_font_size(f"PRESS ENTER TO CONTINUE", 2)
                font.render(display, f"PRESS ENTER TO CONTINUE", [400 - font_size[0] / 2, 335], 2)
            else:
                font_size = font.get_font_size(f"PRESS 1 TO UPGRADE MAX HP AND TO HEAL. PRESS 2 TO UPGRADE WEAPON", 2)
                font.render(display, f"PRESS 1 TO UPGRADE MAX HP AND TO HEAL. PRESS 2 TO UPGRADE WEAPON", [400 - font_size[0] / 2, 335], 2)
        else:
            font_size = font.get_font_size(f"TRAVEL WITH THE LOAD FOR {int(40 - (threat_level / 60 % 40))}", 2)
            font.render(display, f"TRAVEL WITH THE LOAD FOR {int(40 - (threat_level / 60 % 40))}", [400 - font_size[0] / 2, 335], 2)
    else:
        font.render(display, "GAME OVER", [332, 150], 3)

    # Inputs

    for event in pygame.event.get():  # event loop
        if event.type == QUIT:  # check for window quit
            pygame.quit()  # stop pygame
            sys.exit()  # stop script
        if event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()
            if waves_stopped and upgraded and event.key == K_RETURN:
                waves_stopped = False
                upgraded = False
                threat_level += 60
            if not upgraded:
                if event.key == K_1:
                    upgraded = True

                    player.hp.max_hp += 10
                    player.hp.hp += player.hp.max_hp * 0.5
                if event.key == K_2:
                    upgraded = True

                    player.weapon.dmg += player.weapon.dmg * 0.33
                    player.weapon.cooldown -= 2
                    if random.randint(0, 100) < 40:
                        player.weapon.bullets_amount += 1

    surf = pygame.transform.scale(display, WINDOW_SIZE)
    screen.blit(surf, (0, 0))
    fps_clock.tick(120)
    pygame.display.update()
