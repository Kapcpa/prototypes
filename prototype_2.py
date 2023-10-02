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

scale = 1

screen = pygame.display.set_mode(WINDOW_SIZE, 0, 32)
pygame.display.set_caption("Prototype 2 - Idk what even is this")

font = Font('Framework/font.png')

fps_clock = pygame.time.Clock()

display = pygame.Surface((WINDOW_SIZE[0] / scale, WINDOW_SIZE[1] / scale))

scroll = [0, 0]

# TODO:
#   - diverse players attacks
#   - add enemies back
#   - add the 3rd character and its functionality


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


class Bullet(Entity):
    def __init__(self, owner_type, pos, angle, speed=4, size=6, dmg=1, color=(255, 255, 255)):
        self.owner_type = owner_type

        self.lifetime = 720

        self.angle = angle

        self.alive = True

        self.color = color

        self.dmg = dmg

        super().__init__(pos, size, speed, 10)

    def update(self, enemies, players, dt=1.0):
        self.lifetime -= 1 * dt

        self.movement = [math.cos(self.angle), math.sin(self.angle)]

        if self.col or self.lifetime <= 0:
            self.alive = False

        if self.owner_type != Enemy:
            for enemy in enemies:
                self.hit(enemy)

        if self.owner_type != Player:
            for player in players:
                self.hit(player)

        self.move(dt, 1)

    def hit(self, other):
        if collision_circle(self.pos, self.size, other.pos, other.size):
            other.hp.damage(self.dmg)
            self.alive = False

    def draw(self, surf, scroll):
        super().debug_draw(surf, scroll, self.color)


class Weapon:
    def __init__(self, dmg, radius, cooldown, mana_drain, range_weapon=False):
        self.range_weapon = range_weapon

        self.dmg = dmg
        self.radius = radius

        self.cooldown_time = 0
        self.attack_time = 0

        self.cooldown = cooldown
        self.mana_drain = mana_drain

    def update(self, dt=1):
        self.attack_time -= 1 * dt
        self.cooldown_time -= 1 * dt

    def hit(self, entity, other):
        if self.range_weapon:
            return

        if self.attack_time > 0 and collision_circle(entity.pos, entity.weapon.radius, other.pos, other.size):
            other.hp.damage(self.dmg)

    def attack(self, entity):
        if self.cooldown_time > 0:
            return

        entity.hp.drain_mana(self.mana_drain)

        self.cooldown_time = self.cooldown
        if not self.range_weapon:
            self.attack_time = 5
            return

        for i in range(-2, 3):
            angle = math.atan2(entity.movement_dynamics[1].y, entity.movement_dynamics[0].y) + i * math.pi / 8

            pos = entity.pos + pygame.Vector2(math.cos(angle), math.sin(angle)) * entity.size * 2

            bullets.append(Bullet(type(entity), pos, angle, dmg=self.dmg))

    def draw(self, surf, pos, color):
        if self.attack_time > 0:
            pygame.draw.circle(surf, color, pos, self.radius, 4)


class Player(Entity):
    def __init__(self, pos, player_id=0, weapon=Weapon(4, 32, 15, 20)):
        self.hp = Hp(30, 50)

        self.weapon = weapon

        self.movement_scheme = {
            0: {"up": pygame.K_w, "down": pygame.K_s, "left": pygame.K_a, "right": pygame.K_d, "attack": pygame.K_LSHIFT, "switch": pygame.K_LCTRL},
            1: {"up": pygame.K_UP, "down": pygame.K_DOWN, "left": pygame.K_LEFT, "right": pygame.K_RIGHT, "attack": pygame.K_SPACE, "switch": pygame.K_RSHIFT},
            2: {"up": None, "down": None, "left": None, "right": None, "attack": None, "switch": None}
        }

        color_pool = [(0, 255, 0), (75, 180, 0), (0, 180, 75)]
        self.color = color_pool[player_id]
        self.id = player_id

        self.switch_cooldown = 0

        self.target_path = []

        super().__init__(pos, 12)

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

    def update(self, players, dt: int or float = 1):
        self.switch_cooldown -= 1 * dt

        self.hp.update(dt)

        if player.id != len(players) - 1:
            self.target_path = []

            keys = pygame.key.get_pressed()

            if keys[self.movement_scheme[self.id]["left"]]:
                self.movement[0] += -2
            if keys[self.movement_scheme[self.id]["right"]]:
                self.movement[0] += 2
            if keys[self.movement_scheme[self.id]["up"]]:
                self.movement[1] += -2
            if keys[self.movement_scheme[self.id]["down"]]:
                self.movement[1] += 2

            if keys[self.movement_scheme[self.id]["attack"]]:
                self.weapon.attack(self)

            if keys[self.movement_scheme[self.id]["switch"]] and self.switch_cooldown <= 0:
                self.id_switch(sorted(players, key=lambda x: x.id)[-1])
        else:
            self.movement = self.follow_path([400, 225])

            if math.dist(self.pos, [400, 225]) < 48:
                self.hp.hp += 0.1 * dt

        self.move(dt, 1)
        self.weapon.update(dt)

        self.movement = [0, 0]

    def id_switch(self, other):
        self.id, other.id = other.id, self.id
        self.switch_cooldown = 60
        other.switch_cooldown = 60

    def draw(self, surf, scroll):
        self.weapon.draw(surf, [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], self.color)

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


class Enemy(Entity):
    def __init__(self, pos, hp=3, speed=2, flying=False, size=12, dmg=0.5, color=(255, 0, 0)):
        self.color = color
        self.hp = Hp(hp)

        self.weapon = Weapon(dmg, size + 4, 60, 0)

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

    def update(self, players, dt: int or float = 1):
        self.hp.update(dt)
        self.weapon.update(dt)

        for player in players:
            player.weapon.hit(player, self)

        for player in sorted(players, key=lambda x: math.dist(x.pos, self.pos)):
            if player.id == len(players) - 1:
                continue

            if self.hp.kb > 0:
                break

            player_dist = math.dist(player.pos, self.pos)
            if player_dist < self.weapon.radius:
                self.weapon.attack(self)

            self.movement = self.follow_path(player.pos)
            self.speed_target = self.speed

            self.weapon.hit(self, player)

            break

        if self.hp.kb > 0:
            self.speed_target = abs(self.speed_target) * -0.99

        self.move_func(dt, 1)

    def draw(self, surf, scroll):
        super().debug_draw(surf, scroll, self.color)

        self.hp.draw(surf, scroll, self.pos)


game_map = Map()

defence_point = DefencePoint([400, 225])

players = [Player([400, 200], player_id=0), Player([400, 200], player_id=1, weapon=Weapon(8, 64, 60, 40)),
           Player([400, 200], player_id=2, weapon=Weapon(8, 24, 10, 10, True))]

enemies = []
enemy_types = [
    {"hp": 6, "speed": 2, "flying": False, "size": 12, "dmg": 0.1, "color": (255, 0, 0)},
    {"hp": 2, "speed": 3, "flying": False, "size": 6, "dmg": 0.5, "color": (255, 0, 255)},
    {"hp": 12, "speed": 1, "flying": False, "size": 18, "dmg": 1.5, "color": (255, 0, 0)},
    {"hp": 3, "speed": 2, "flying": True, "size": 6, "dmg": 0.75, "color": (255, 150, 0)},
]
enemy_waves = [[0, 0, 0], [3, 3, 3, 3], [1, 1, 1, 1, 1], [2], [2, 0, 0], [2, 1, 1, 1, 1], [2, 3], [3, 3, 1, 1, 1]]

bullets = []

threat_level = 0
waves_stopped = False
upgraded = False


dt = 1

last_time = time.time() - 1


while True:
    if all(player.hp.alive for player in players):
        dt = time.time() - last_time
        dt *= 60
        last_time = time.time()

        display.fill((100, 100, 100))

        mx, my = pygame.mouse.get_pos()
        mx /= scale
        my /= scale

        # Update

        game_map.draw(display, scroll)

        pygame.draw.circle(display, (225, 225, 0), [400, 225], 48, 4)

        for i, enemy in enumerate(enemies):
            enemy.update(players, dt)
            enemy.draw(display, scroll)

            if not enemy.hp.alive:
                enemies.pop(i)

        for player in players:
            player.update(players, dt)
            player.draw(display, scroll)

        for i, bullet in enumerate(bullets):
            bullet.update(enemies, players, dt)
            bullet.draw(display, scroll)

            if not bullet.alive:
                bullets.pop(i)

        # Wave System

        if not waves_stopped:
            threat_level += 1 * dt

        # Spawn Enemies

        if int(threat_level % (60 * 100)) == 0:
            waves_stopped = True

        if not waves_stopped and int(threat_level % (120 + threat_level / 300)) == 0 and random.randint(0, 100) < 15 + threat_level / 420:
            for enemy_type in random.choice(enemy_waves):
                stats = enemy_types[enemy_type]

                enemies.append(Enemy([400 + random.randint(400, 450) * random.choice([1, -1]), 225 + random.randint(225, 275) * random.choice([1, -1])],
                                     stats["hp"], stats["speed"], stats["flying"], stats["size"], stats["dmg"], stats["color"]))

        if waves_stopped:
            if upgraded:
                font_size = font.get_font_size(f"PRESS ENTER TO CONTINUE", 2)
                font.render(display, f"PRESS ENTER TO CONTINUE", [400 - font_size[0] / 2, 335], 2)
            else:
                font_size = font.get_font_size(f"PRESS 1 TO UPGRADE MAX HP AND TO HEAL. PRESS 2 TO BOOST DMG", 2)
                font.render(display, f"PRESS 1 TO UPGRADE MAX HP AND TO HEAL. PRESS 2 TO BOOST DMG", [400 - font_size[0] / 2, 335], 2)
        else:
            font_size = font.get_font_size(f"SURVIVE FOR {int(100 - (threat_level / 60 % 100))}", 2)
            font.render(display, f"SURVIVE FOR {int(100 - (threat_level / 60 % 100))}", [400 - font_size[0] / 2, 335], 2)

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

                    for player in players:
                        player.hp.max_hp += 5
                        player.hp.hp += player.hp.max_hp * 0.5
                if event.key == K_2:
                    upgraded = True

                    for player in players:
                        player.weapon.dmg += player.weapon.dmg * 0.25

    surf = pygame.transform.scale(display, WINDOW_SIZE)
    screen.blit(surf, (0, 0))
    fps_clock.tick(120)
    pygame.display.update()
