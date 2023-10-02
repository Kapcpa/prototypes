import pygame
import random

from .second_order_system import *
from .extra_functions import clamp


def scale_map(surf, scale_factor):
    return pygame.transform.scale(surf.copy(), (surf.get_width() * scale_factor, surf.get_height() * scale_factor))


class Camera:
    def __init__(self, surf_size, scroll_speed, start_scroll=[0, 0], cam_bound=[[-math.inf, math.inf], [-math.inf, math.inf]]):
        self.surf_size = surf_size

        self.shake_value = 0
        self.shake_time = 0
        self.flash_time = 0

        # Scroll Stuff

        self.scroll = start_scroll
        self.cam_bound = cam_bound

        self.cam_speed = scroll_speed

        self.scroll_target = [0, 0]

        # Shader Parameters

        self.vignette_strength = SecondOrderDynamics(0.2, 1, 0, 1)

        self.blood_indicator_time = 0
        self.blood_visibility = SecondOrderDynamics(1, 1, 0, 0)

        self.rgb_split = SecondOrderDynamics(0.5, 1, 0, 0)

    def scroll_target_update(self, targets, max_dist=320):
        old_scroll = self.scroll_target.copy()
        self.scroll_target = [0, 0]
        scroll_weight = 0

        for target in targets:
            if scroll_weight > targets[0]["weight"] * 2:
                break

            if target is not targets[0]:
                target_dist = math.dist(targets[0]["pos"], target["pos"])
                if target_dist > max_dist:
                    target["weight"] = 0
                else:
                    target["weight"] *= (max_dist / target_dist)

            self.scroll_target[0] += target["pos"][0] * target["weight"]
            self.scroll_target[1] += target["pos"][1] * target["weight"]
            scroll_weight += target["weight"]

        self.scroll_target[0] /= scroll_weight
        self.scroll_target[1] /= scroll_weight

        self.scroll_target[0] = (self.scroll_target[0] + old_scroll[0]) / 2
        self.scroll_target[1] = (self.scroll_target[1] + old_scroll[1]) / 2

    def scroll_update(self, col_scale=1, dt=1):
        self.scroll[0] += (self.scroll_target[0] / col_scale - self.scroll[0] - int(self.surf_size[0] / 2)) / self.cam_speed * dt
        self.scroll[1] += (self.scroll_target[1] / col_scale - self.scroll[1] - int(self.surf_size[1] / 2)) / self.cam_speed * dt

        self.scroll[0] = clamp(self.scroll[0], self.cam_bound[0][0], self.cam_bound[0][1])
        self.scroll[1] = clamp(self.scroll[1], self.cam_bound[1][0], self.cam_bound[1][1])

    def get_scroll(self):
        scroll = self.scroll.copy()

        scroll[0] += random.randint(0, self.shake_value) - int(self.shake_value / 2)
        scroll[1] += random.randint(0, self.shake_value) - int(self.shake_value / 2)

        return scroll

    def value_update(self, player, dt=1):
        self.blood_indicator_time += 0.1 * dt

        heart_beat_func = abs(math.floor(math.sin(self.blood_indicator_time * 0.75)) * math.sin(1.5 * self.blood_indicator_time))

        self.blood_visibility.update(1 - player.hp / player.start_hp, dt / 60)
        if player.hp == 1:
            self.blood_visibility.update(1 - player.hp / player.start_hp + heart_beat_func ** 2 * 3, dt / 20)

        self.rgb_split.update(0, dt / 60)
        self.vignette_strength.update(0.75, dt / 60)

        self.flash_time -= 1 * dt
        if self.shake_time > 0:
            self.shake_time -= 1 * dt
        else:
            self.shake_value = 0

    def set_cam_flash(self, time):
        self.flash_time = time

    def set_cam_shake(self, time, value):
        self.shake_time = time
        self.shake_value = value

    def debug_draw(self, surf):
        pygame.draw.circle(surf, (255, 0, 0), [self.scroll_target[0] - self.scroll[0],
                                               self.scroll_target[1] - self.scroll[1]], 5)
