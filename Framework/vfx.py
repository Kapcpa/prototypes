import pygame
import math
import random

from pygame import *


from .global_values import colorkey
from .main_framework import animation_database, animation_frames
from .second_order_system import *
from .extra_functions import clamp

from ..sprites import skeleton, blood_stains, debris, game_ui_imgs


def get_gradient(surf_size, start_color, end_color, steps):
    surf = pygame.Surface(surf_size)

    step_sizes = ((end_color[0] - start_color[0]) / steps,
                  (end_color[1] - start_color[1]) / steps,
                  (end_color[2] - start_color[2]) / steps)

    color = start_color
    for y in range(surf.get_height()):
        for x in range(surf.get_width()):
            surf_color = (int(color[0]), int(color[1]), int(color[2]))
            surf.set_at([x, y], surf_color)
        if y % int(surf.get_height() / steps) == 0:
            color[0] += step_sizes[0]
            color[1] += step_sizes[1]
            color[2] += step_sizes[2]

    return surf


class ShockwaveDistortion:
    def __init__(self, pos, force, speed, force_fadeout=0.00075, size=0.0, max_size=3.0):
        self.pos = pos

        self.force = force
        self.force_fadeout = force_fadeout

        self.speed = speed

        self.size = size
        self.max_size = max_size

        self.alive = True

    def update(self, dt):
        self.size += self.speed * dt
        self.force -= self.force_fadeout * dt

        if self.size > self.max_size or self.force <= 0:
            self.alive = False

    def debug_draw(self, surf, scroll):
        pygame.draw.circle(surf, (255, 255, 255), [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], 5)

    def get_shader_data(self, surf, scroll):
        return [(self.pos[0] - scroll[0]) / surf.get_width(), (self.pos[1] - scroll[1]) / surf.get_height(), self.size, self.force]


class ShaderDistortions:
    def __init__(self, engine):
        self.shockwaves = []

        self.engine = engine

    def update(self):
        for i, shockwave in enumerate(self.shockwaves):
            shockwave.update(self.engine.dt)

            if not shockwave.alive:
                self.shockwaves.pop(i)


class ImageIcon:
    def __init__(self, pos, icon_name, speed=0.04):
        self.pos = pos.copy()

        self.icon_name = icon_name

        self.rot_speed = speed

        self.angle = 0

    def draw(self, surf, scroll, dt=1):
        self.angle += self.rot_speed * dt

        img = game_ui_imgs[self.icon_name].copy()
        rot_scale = math.sin(self.angle)
        if rot_scale < 0:
            img = pygame.transform.flip(img, True, False)
        rot_size = [int(img.get_width() * abs(rot_scale)), img.get_height()]
        img = pygame.transform.scale(img, rot_size)

        offset = [int(img.get_width() / 2), int(img.get_height() / 2)]
        surf.blit(img, (self.pos[0] - scroll[0] - offset[0], self.pos[1] - scroll[1] - offset[1]))


class AnimatedIcon:
    def __init__(self, pos, icon_name, animation_versions=5):
        self.pos = pos.copy()

        self.icon_name = icon_name
        self.animation_versions = animation_versions
        self.icon_action = self.icon_name + f"_{random.randint(0, self.animation_versions)}"
        self.icon_frame = 0

    def draw(self, surf, scroll, dt=1):
        self.icon_frame += 1 * dt
        if self.icon_frame >= len(animation_database[self.icon_action]):
            self.icon_action = self.icon_name + f"_{random.randint(0, self.animation_versions)}"
            self.icon_frame = 0

        img = animation_frames[animation_database[self.icon_action][int(self.icon_frame)]]

        offset = [int(img.get_width() / 2), int(img.get_height() / 2)]
        surf.blit(img, (self.pos[0] - scroll[0] - offset[0], self.pos[1] - scroll[1] - offset[1]))


class Icons:
    def __init__(self, engine):
        self.icons = []

        self.engine = engine

    def update(self):
        for i, icon in enumerate(self.icons):
            if self.engine.map.can_draw(icon.pos, self.engine.scroll, 32):
                icon.draw(self.engine.display, self.engine.scroll, self.engine.dt)


class FadeSprite:
    def __init__(self, img, pos, fade_speed=1.0, rotation=random.randint(0, 360)):
        self.img = pygame.transform.rotate(img, rotation)
        self.img_size = self.img.get_size()

        self.pos = (pos[0] - int(self.img.get_width() / 2), pos[1] - int(self.img.get_height() / 2))

        self.alpha = 255
        self.speed = fade_speed

        self.alive = True

    def update(self, dt=1):
        if self.speed != 0:
            self.alpha -= self.speed * dt

            if self.alpha <= 0:
                self.alive = False

    def draw(self, surf, scroll):
        if not self.alive:
            return

        screen_pos = (self.pos[0] - scroll[0], self.pos[1] - scroll[1])
        if -self.img_size[0] < screen_pos[0] < surf.get_width() + self.img_size[0] and \
                -self.img_size[1] < screen_pos[1] < surf.get_height() + self.img_size[1]:
            if self.speed != 0:
                self.img.set_alpha(self.alpha)
            surf.blit(self.img, screen_pos)


class FadingSprites:
    def __init__(self, engine, draw_layers=3):
        self.draw_layers = draw_layers

        self.chunks = {}

        self.engine = engine

    def add_object(self, img, pos, fade_speed=1, rotation=random.randint(0, 360), draw_order=0):
        chunk_system = self.engine.map.chunk_system
        chunk_loc_str = str(int(pos[0] / 16 / chunk_system.size)) + ';' + str(int(pos[1] / 16 / chunk_system.size))
        if chunk_loc_str not in self.chunks:
            self.chunks[chunk_loc_str] = [[] for _ in range(self.draw_layers)]
            self.chunks[chunk_loc_str][draw_order].append(FadeSprite(img, pos, fade_speed, rotation))
        else:
            self.chunks[chunk_loc_str][draw_order].append(FadeSprite(img, pos, fade_speed, rotation))

    def update(self):
        chunk_system = self.engine.map.chunk_system
        for y in range(chunk_system.visible_chunks[1]):
            for x in range(chunk_system.visible_chunks[0]):
                chunk_x = x - 1 + int(round(self.engine.scroll[0] / (16 * chunk_system.size)))
                chunk_y = y - 1 + int(round(self.engine.scroll[1] / (16 * chunk_system.size)))
                target_chunk = str(chunk_x) + ';' + str(chunk_y)

                if target_chunk in self.chunks:
                    for layer in self.chunks[target_chunk]:
                        remove_list = []

                        for fade_sprite in layer:
                            fade_sprite.update(self.engine.dt)
                            fade_sprite.draw(self.engine.display, self.engine.scroll)
                            if not fade_sprite.alive:
                                remove_list.append(fade_sprite)

                        for i in remove_list:
                            layer.remove(i)


class FadingText:
    def __init__(self, font, pos, text='', y_target=-48, scale=2, draw_center=True, reaction_time=1):
        self.font = font

        self.text = text
        self.scale = scale

        self.text_surf = pygame.Surface(self.font.get_font_size(self.text, self.scale))
        self.text_surf.set_colorkey((0, 0, 0))
        self.font.render(self.text_surf, self.text, [0, 0], self.scale)

        self.pos = pos
        if draw_center:
            self.pos[0] -= int(self.text_surf.get_width() / 2)
            self.pos[1] -= int(self.text_surf.get_height() / 2)

        self.y_pos = SecondOrderDynamics(1 * reaction_time, 2, 0, 0)
        self.y_target = y_target
        self.alpha = SecondOrderDynamics(0.25 * reaction_time, 0.25, 0, 255)

        self.alive = True

    def update(self, dt):
        self.y_pos.update(self.y_target, dt / 60)
        self.alpha.update(0, dt / 60)

        if self.alpha.y < 0.1:
            self.alive = False

    def draw(self, surf, scroll):
        self.text_surf.set_alpha(self.alpha.y)

        surf.blit(self.text_surf, (self.pos[0] - scroll[0], self.pos[1] + self.y_pos.y - scroll[1]))


class FadingTexts:
    def __init__(self, engine):
        self.engine = engine

        self.texts = []

    def update(self):
        for i, text in sorted(enumerate(self.texts), reverse=True):
            text.update(self.engine.dt)
            text.draw(self.engine.ui_display, self.engine.scroll)

            if not text.alive:
                self.texts.pop(i)


class SquareParticle:
    def __init__(self, pos, velo, size, size_velo, width, color, alpha_velo=-1, alpha=255):
        self.pos = pos.copy()
        self.velo = velo

        self.size = size
        self.size_velo = size_velo
        self.width = width

        self.color = color

        self.alpha = alpha
        self.alpha_velo = alpha_velo

        self.alive = True

    def update(self, engine):
        self.pos[0] += self.velo[0] * engine.dt
        self.pos[1] += self.velo[1] * engine.dt

        self.alpha += self.alpha_velo * engine.dt
        self.size += self.size_velo * engine.dt

        if self.alpha <= 0:
            self.alive = False

        self.alpha = clamp(self.alpha, 0, 255)

    def draw(self, surf, scroll):
        square_points = []
        for pos in [[-1, 1], [1, 1], [1, -1], [-1, -1]]:
            square_points.append([self.pos[0] + pos[0] * self.size - scroll[0],
                                  self.pos[1] + pos[1] * self.size - scroll[1]])

        color = [self.color[0], self.color[1], self.color[2], self.alpha]
        # pygame.draw.aalines(surf, color, True, square_points, 3)
        pygame.draw.lines(surf, color, True, square_points, self.width)


class BaseParticle:
    def __init__(self, pos, velo, speed, color, size, width=0):
        self.pos = pos
        self.velo = velo
        self.speed = speed

        self.color = color
        self.size = size
        self.width = width

        self.alive = True

    def draw(self, surf, scroll):
        pygame.draw.circle(surf, self.color, [self.pos[0] - scroll[0], self.pos[1] - scroll[1]], self.size, self.width)


class NormalParticle(BaseParticle):
    def __init__(self, pos, velo, speed, color, size, shrink_speed, width=0):
        self.shrink_speed = shrink_speed

        super().__init__(pos, velo, speed, color, size, width)

    def update(self, engine):
        self.size -= self.shrink_speed * engine.dt

        self.pos[0] += self.velo[0] * self.speed * engine.dt
        self.pos[1] += self.velo[1] * self.speed * engine.dt

        if self.size <= 0:
            self.alive = False


class PhysicsParticle(BaseParticle):
    def __init__(self, pos, velo, speed, color, size, shrink_speed, speed_loss=0.9, width=0):
        self.shrink_speed = shrink_speed

        self.speed_loss = speed_loss

        super().__init__(pos, velo, speed, color, size, width)

    def update(self, engine):
        game_map = engine.map
        self.size -= self.shrink_speed * engine.dt

        # X movement with tile check

        self.pos[0] += self.velo[0] * self.speed * engine.dt

        tile_pos = [int(self.pos[0] / game_map.tile_size),
                    int(self.pos[1] / game_map.tile_size)]
        if 0 < tile_pos[0] < len(game_map.binary_map[0]) and 0 < tile_pos[1] < len(game_map.binary_map):
            if game_map.binary_map[tile_pos[1]][tile_pos[0]] == '1':
                self.velo[0] *= -self.speed_loss
                self.pos[0] += self.velo[0] * self.speed * engine.dt

        # Y movement with tile check

        self.pos[1] += self.velo[1] * self.speed * engine.dt

        tile_pos = [int(self.pos[0] / game_map.tile_size),
                    int(self.pos[1] / game_map.tile_size)]
        if 0 < tile_pos[0] < len(game_map.binary_map[0]) and 0 < tile_pos[1] < len(game_map.binary_map):
            if game_map.binary_map[tile_pos[1]][tile_pos[0]] == '1':
                self.velo[1] *= -self.speed_loss
                self.pos[1] += self.velo[1] * self.speed * engine.dt

        if self.size <= 0:
            self.alive = False


class AnimParticle:
    def __init__(self, pos, velo, speed, anim_name, rot=None):
        self.pos = pos

        self.velo = velo
        self.speed = speed

        self.rot = random.randint(0, 360)
        if rot:
            self.rot = rot

        self.frame = 0
        self.name = anim_name

        self.alive = True

    def update(self, engine):
        self.pos[0] += self.velo[0] * self.speed * engine.dt
        self.pos[1] += self.velo[1] * self.speed * engine.dt

        self.frame += 1 * engine.dt

        if self.frame >= len(animation_database[self.name]):
            self.alive = False

    def draw(self, surf, scroll):
        if not self.alive:
            return

        img_id = animation_database[self.name][int(self.frame)]
        img = pygame.transform.rotate(animation_frames[img_id], self.rot)

        surf.blit(img, (self.pos[0] - int(img.get_width() / 2) - scroll[0],
                        self.pos[1] - int(img.get_height() / 2) - scroll[1]))


class Explosion(BaseParticle):
    def __init__(self, pos, velo, speed, start_color, end_color, size, shrink_speed, speed_loss=0.9, width=0):
        self.shrink_speed = shrink_speed

        self.end_color = end_color

        self.speed_loss = speed_loss

        super().__init__(pos, velo, speed, start_color, size, width)

    def update(self, game_map, dt, speed_mult):
        self.size -= self.shrink_speed * dt

        # X movement with tile check

        self.pos[0] += self.velo[0] * self.speed * speed_mult * dt

        tile_pos = [int(self.pos[0] / game_map.tile_size),
                    int(self.pos[1] / game_map.tile_size)]
        if 0 < tile_pos[0] < len(game_map.binary_map[0]) and 0 < tile_pos[1] < len(game_map.binary_map):
            if game_map.binary_map[tile_pos[1]][tile_pos[0]] == '1':
                self.velo[0] *= -self.speed_loss
                self.pos[0] += self.velo[0] * self.speed * dt

        # Y movement with tile check

        self.pos[1] += self.velo[1] * self.speed * speed_mult * dt

        tile_pos = [int(self.pos[0] / game_map.tile_size),
                    int(self.pos[1] / game_map.tile_size)]
        if 0 < tile_pos[0] < len(game_map.binary_map[0]) and 0 < tile_pos[1] < len(game_map.binary_map):
            if game_map.binary_map[tile_pos[1]][tile_pos[0]] == '1':
                self.velo[1] *= -self.speed_loss
                self.pos[1] += self.velo[1] * self.speed * dt

        if speed_mult >= -0.1:
            self.color = self.end_color

        if self.size <= 0:
            self.alive = False


class Debris(BaseParticle):
    def __init__(self, pos, velo, speed, color, size, shrink_speed, speed_loss=0.9, width=0):
        self.shrink_speed = shrink_speed

        self.speed_loss = speed_loss

        super().__init__(pos, velo, speed, color, size, width)

    def update(self, engine):
        game_map = engine.map

        self.size -= self.shrink_speed * engine.dt

        try:
            # X movement with tile check

            self.pos[0] += self.velo[0] * self.speed * engine.dt

            tile_pos = [int(self.pos[0] / game_map.tile_size),
                        int(self.pos[1] / game_map.tile_size)]
            if game_map.binary_map[tile_pos[1]][tile_pos[0]] == '1':
                self.velo[0] *= -self.speed_loss
                self.pos[0] += self.velo[0] * self.speed * engine.dt

            # Y movement with tile check

            self.pos[1] += self.velo[1] * self.speed * engine.dt

            tile_pos = [int(self.pos[0] / game_map.tile_size),
                        int(self.pos[1] / game_map.tile_size)]
            if game_map.binary_map[tile_pos[1]][tile_pos[0]] == '1':
                self.velo[1] *= -self.speed_loss
                self.pos[1] += self.velo[1] * self.speed * engine.dt
        except IndexError:
            self.alive = False

        # Spawning blood stains

        debris_pos = [int(self.pos[0]), int(self.pos[1])]

        if not random.randint(0, 5):
            img = debris[random.randint(0, len(debris) - 1)].copy()
            img = pygame.transform.rotate(img, random.randint(0, 360))
            engine.fading_sprites.add_object(img, debris_pos, 0)

        if self.size <= 0:
            img = debris[random.randint(0, len(debris) - 1)].copy()
            img = pygame.transform.rotate(img, random.randint(0, 360))
            engine.fading_sprites.add_object(img, debris_pos, 0)

            self.alive = False


class ExplosionSystem:
    def __init__(self, center, density, size, start_color, end_color):
        self.explosion_particles = []
        self.debris_particles = []

        self.speed_mult_system = SecondOrderDynamics(0.5, 0.7, 1.5, -1)

        self.end_color = end_color

        self.alive = True

        debris_angles = 6

        for x in range(debris_angles):
            angle = x * 360 / debris_angles
            p_pos = center.copy()
            p_movement = [math.cos(angle), math.sin(angle)]

            p_size = random.randint(2, 6)
            self.debris_particles.append(Debris(p_pos, p_movement, random.randint(10, 20) / 5, (16, 20, 31), p_size, 0.2))

        for x in range(density):
            p_pos = center.copy()
            angle = math.radians(random.randint(0, 360))
            p_movement = [math.cos(angle), math.sin(angle)]

            center_dist = random.randint(0, 16)

            p_pos[0] -= p_movement[0] * center_dist
            p_pos[1] -= p_movement[1] * center_dist

            p_size = random.randint(size[0], size[1])
            self.explosion_particles.append(Explosion(p_pos, p_movement * 3, random.randint(0, 30) / 5,
                                                      start_color, end_color, p_size, 0.2))

    def update(self, engine):
        self.speed_mult_system.update(0, engine.dt / 60)

        for i, p in enumerate(self.explosion_particles):
            p.update(engine.map, engine.dt, self.speed_mult_system.y)
            p.draw(engine.gblur_display, engine.scroll)
            if not p.alive:
                self.explosion_particles.pop(i)

        for i, p in enumerate(self.debris_particles):
            p.update(engine)
            p.draw(engine.display, engine.scroll)
            if not p.alive:
                self.debris_particles.pop(i)

        if len(self.explosion_particles) == 0 and len(self.debris_particles) == 0:
            self.alive = False


class SmokeSystem:
    def __init__(self, center, density, size, start_color, end_color):
        self.explosion_particles = []

        self.speed_mult_system = SecondOrderDynamics(0.25, 0.7, 1, -1)

        self.end_color = end_color

        self.alive = True

        for x in range(density):
            p_pos = center.copy()
            angle = math.radians(random.randint(0, 360))
            p_movement = [math.cos(angle), math.sin(angle)]

            center_dist = random.randint(0, 32)

            p_pos[0] -= p_movement[0] * center_dist
            p_pos[1] -= p_movement[1] * center_dist

            p_size = random.randint(size[0], size[1])
            self.explosion_particles.append(Explosion(p_pos, p_movement, random.randint(0, 20) / 5,
                                                      start_color, end_color, p_size, 0.12))

    def update(self, engine):
        self.speed_mult_system.update(0, engine.dt / 60)

        for i, p in enumerate(self.explosion_particles):
            p.update(engine.map, engine.dt, self.speed_mult_system.y)
            p.draw(engine.gblur_display, engine.scroll)
            if not p.alive:
                self.explosion_particles.pop(i)

        if len(self.explosion_particles) == 0:
            self.alive = False


class BloodParticle(BaseParticle):
    def __init__(self, pos, velo, speed, color, size, shrink_speed, speed_loss=0.9, width=0, fading_speed=0.25):
        self.shrink_speed = shrink_speed
        self.fading_speed = fading_speed

        self.speed_loss = speed_loss

        super().__init__(pos, velo, speed, color, size, width)

    def update(self, engine):
        game_map = engine.map

        self.size -= self.shrink_speed * engine.dt

        # X movement with tile check

        self.pos[0] += self.velo[0] * self.speed * engine.dt

        tile_pos = [int(self.pos[0] / game_map.tile_size),
                    int(self.pos[1] / game_map.tile_size)]
        if game_map.binary_map[tile_pos[1]][tile_pos[0]] == '1':
            self.velo[0] *= -self.speed_loss
            self.pos[0] += self.velo[0] * self.speed * engine.dt

        # Y movement with tile check

        self.pos[1] += self.velo[1] * self.speed * engine.dt

        tile_pos = [int(self.pos[0] / game_map.tile_size),
                    int(self.pos[1] / game_map.tile_size)]
        if game_map.binary_map[tile_pos[1]][tile_pos[0]] == '1':
            self.velo[1] *= -self.speed_loss
            self.pos[1] += self.velo[1] * self.speed * engine.dt

        # Spawning blood stains

        stain_pos = [int(self.pos[0]), int(self.pos[1])]

        if not random.randint(0, 10):
            img = blood_stains[random.randint(0, len(blood_stains) - 1)].copy()
            img = pygame.transform.rotate(img, random.randint(0, 360))
            engine.fading_sprites.add_object(img, stain_pos, self.fading_speed)

        if self.size <= 0:
            img = blood_stains[random.randint(0, len(blood_stains) - 1)].copy()
            img = pygame.transform.rotate(img, random.randint(0, 360))
            engine.fading_sprites.add_object(img, stain_pos, self.fading_speed)
            self.alive = False


class Spark:
    def __init__(self, loc, angle, speed, color, scale=1 or 1.0, rotate=True):
        self.loc = loc
        self.angle = angle
        self.speed = speed
        self.scale = scale
        self.color = color
        self.alive = True

        self.rotate = rotate

    def point_towards(self, angle, rate):
        rotate_direction = ((angle - self.angle + math.pi * 3) % (math.pi * 2)) - math.pi
        try:
            rotate_sign = abs(rotate_direction) / rotate_direction
        except ZeroDivisionError:
            rotate_sing = 1
        if abs(rotate_direction) < rate:
            self.angle = angle
        else:
            self.angle += rate * rotate_sign

    def calculate_movement(self, dt):
        return [math.cos(self.angle) * self.speed * dt, math.sin(self.angle) * self.speed * dt]

    def velocity_adjust(self, friction, force, terminal_velocity, dt):  # gravity and friction
        movement = self.calculate_movement(dt)
        movement[1] = min(terminal_velocity, movement[1] + force * dt)
        movement[0] *= friction
        self.angle = math.atan2(movement[1], movement[0])
        # if you want to get more realistic, the speed should be adjusted here

    def update(self, dt):
        movement = self.calculate_movement(dt)
        self.loc[0] += movement[0]
        self.loc[1] += movement[1]

        # a bunch of options to mess around with relating to angles...
        if self.rotate:
            self.point_towards(math.pi / 2, 0.02)
        # self.velocity_adjust(0.975, 0.2, 8, dt)
        # self.angle += 0.1

        self.speed -= 0.2 * dt

        if self.speed <= 0:
            self.alive = False

    def draw(self, surf, offset=[0, 0]):
        if self.alive:
            points = [
                [self.loc[0] + math.cos(self.angle) * self.speed * self.scale - offset[0],
                 self.loc[1] + math.sin(self.angle) * self.speed * self.scale - offset[1]],
                [self.loc[0] + math.cos(self.angle + math.pi / 2) * self.speed * self.scale * 0.3 - offset[0],
                 self.loc[1] + math.sin(self.angle + math.pi / 2) * self.speed * self.scale * 0.3 - offset[1]],
                [self.loc[0] - math.cos(self.angle) * self.speed * self.scale * 3.5 - offset[0],
                 self.loc[1] - math.sin(self.angle) * self.speed * self.scale * 3.5 - offset[1]],
                [self.loc[0] + math.cos(self.angle - math.pi / 2) * self.speed * self.scale * 0.3 - offset[0],
                 self.loc[1] - math.sin(self.angle + math.pi / 2) * self.speed * self.scale * 0.3 - offset[1]],
            ]
            pygame.draw.polygon(surf, self.color, points)


class Sparks:
    def __init__(self, engine):
        self.sparks = []

        self.engine = engine

    def update(self):
        for i, spark in enumerate(self.sparks):
            spark.update(self.engine.dt)
            spark.draw(self.engine.gblur_display, self.engine.scroll)
            self.engine.gblur_render = True
            if not spark.alive:
                self.sparks.pop(i)


class Particles:
    def __init__(self, engine):
        self.engine = engine

        self.particles = []
        self.blood = []
        self.particle_systems = []
        self.fire_sources = []

        self.light_particles = []

    def create_explosion(self, center, density, size, start_color=(232, 193, 112), end_color=(207, 87, 60), flash=True, shake=True, particle_system="explosion"):
        if shake:
            self.engine.cam.set_cam_shake(35, 10)

        if flash:
            self.engine.cam.set_cam_flash(10)

        if particle_system == "explosion":
            self.particle_systems.append(ExplosionSystem(center.copy(), density, size, start_color, end_color))
        elif particle_system == "smoke":
            self.particle_systems.append(SmokeSystem(center.copy(), density, size, start_color, end_color))

    def update(self):
        # Normal / Physics particles / Animated particles update
        for i, p in enumerate(self.particles):
            p.update(self.engine)
            p.draw(self.engine.display, self.engine.scroll)
            if not p.alive:
                self.particles.pop(i)

        # Light particles update / Animated particles update
        for i, p in enumerate(self.light_particles):
            p.update(self.engine)
            p.draw(self.engine.gblur_display, self.engine.scroll)
            self.engine.gblur_render = True
            if not p.alive:
                self.light_particles.pop(i)

        # Blood particles update
        for i, p in enumerate(self.blood):
            p.update(self.engine)
            p.draw(self.engine.display, self.engine.scroll)
            if not p.alive:
                self.blood.pop(i)

        # Explosions

        for i, particle_system in enumerate(self.particle_systems):
            self.engine.gblur_render = True

            particle_system.update(self.engine)
            if not particle_system.alive:
                self.particle_systems.pop(i)


# BLOOD SPARK COLOR - (205, 36, 36)
# DUST COLOR - (33, 33, 44)
# BLOOD PARTICLE COLOR - (158, 23, 23)

def entity_hit(entity, sparks, particle_system, dmg=1):
    entity.animator.flash = 10
    entity.animator.scale.y -= 0.25 * dmg

    if dmg > 1:
        particle_system.light_particles.append(AnimParticle(entity.pos.copy(), [0, 0], 0, "explosion", 1))

    start_angle = random.randint(0, 90)
    for x in range(4):
        angle = math.radians(start_angle + 90 * x)
        sparks.append(Spark(entity.pos.copy(), angle, 4, (255, 255, 255), 2.5, False))

    for x in range(int(7 * dmg)):
        angle = -math.atan2(entity.movement[1], entity.movement[0]) + math.radians(random.randint(0, 120) - 60)
        sparks.append(Spark(entity.pos.copy(), angle, 6, (205, 36, 36), 3))
    for x in range(int(5 * dmg)):
        p_angle = -math.atan2(entity.movement[1], entity.movement[0]) + math.radians(random.randint(0, 120) - 60)
        p_movement = [math.cos(p_angle), math.sin(p_angle)]
        particle_system.particles.append(NormalParticle(entity.pos.copy(), p_movement, 1.5, (33, 33, 44), random.randint(10, 14), 0.15))

        particle_system.blood.append(BloodParticle(entity.pos.copy(), p_movement, 4, (158, 23, 23), 1, 0.1, fading_speed=0))


def entity_dead(entity, engine, corpse_img=skeleton):
    engine.cam.rgb_split.y = 0.006
    engine.shader_distortions.shockwaves.append(ShockwaveDistortion(entity.pos.copy(), 0.03, 0.01))

    engine.fading_sprites.add_object(corpse_img, entity.pos.copy(), 0, random.randint(0, 360), draw_order=1)

    engine.particles.light_particles.append(AnimParticle(entity.pos.copy(), [0, 0], 0, "explosion", 1))

    for x in range(20):
        spark_pos = entity.pos.copy()
        engine.sparks.sparks.append(Spark(spark_pos, math.radians(random.randint(0, 360)), 6, (205, 36, 36), 3))
    for x in range(12):
        p_angle = math.radians(random.randint(0, 360))
        p_movement = [math.cos(p_angle), math.sin(p_angle)]
        engine.particles.particles.append(NormalParticle(entity.pos.copy(), p_movement, 1.5, (33, 33, 44), random.randint(10, 14), 0.15))

        engine.particles.blood.append(BloodParticle(entity.pos.copy(), p_movement, 4, (158, 23, 23), 1, 0.1, fading_speed=0))
    for x in range(8):
        p_angle = math.radians(x * 360 / 8)
        p_movement = [math.cos(p_angle), math.sin(p_angle)]

        engine.particles.particles.append(NormalParticle(entity.pos.copy(), p_movement, 1.5, (33, 33, 44), random.randint(12, 16), 0.15))
