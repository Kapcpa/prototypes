import random

import pygame.mixer

from .global_values import *
from .extra_functions import load_bonus_property


pygame.mixer.pre_init()


sound_data = json.load(open("Data/Levels/sound_data.json", ))


class SoundManager:
    def __init__(self, channel_num=32, base_volume=1):
        self.volume = base_volume
        self.channel_num = channel_num

        self.sound_queue = {}

        self.sounds = {}

        for sound in sound_data:
            sound_format = load_bonus_property("format", sound_data[sound], ".wav")
            file_name = load_bonus_property("file_name", sound_data[sound], None)
            self.add_sound(sound, sound_data[sound]["variations"], sound_format, file_name)

        pygame.mixer.set_num_channels(self.channel_num)

    def add_sound(self, sound_name, sound_variations, sound_format=".wav", file_name=None):
        if sound_name in self.sounds:
            return

        if file_name is None:
            file_name = sound_name

        self.sounds[sound_name] = [pygame.mixer.Sound(f"Data/Sounds/{file_name}_{i}{sound_format}") for i in range(sound_variations)]

    def update_sounds(self, dt):
        for sound in list(self.sound_queue.keys()):
            self.sound_queue[sound] -= 1 * dt
            if self.sound_queue[sound] <= 0:
                del self.sound_queue[sound]

    def stop_sound(self, name, fade_time=360):
        if name not in self.sounds:
            return

        sound_variations = self.sounds[name]

        for i in range(self.channel_num):
            if pygame.mixer.Channel(i).get_busy():
                if pygame.mixer.Channel(i).get_sound() in sound_variations:
                    pygame.mixer.Channel(i).fadeout(fade_time)

                    return

    def is_played(self, name):
        if name not in self.sounds:
            return False

        for i in range(self.channel_num):
            if pygame.mixer.Channel(i).get_busy():
                if pygame.mixer.Channel(i).get_sound() in self.sounds[name]:
                    return True

        return False

    def play_sound(self, name, volume=1, loops=0, variation=-1, sound_cooldown=0, angle=0, distance=0):
        if name not in self.sounds or name in self.sound_queue:
            return

        for i in range(self.channel_num):
            if not pygame.mixer.Channel(i).get_busy():
                sound_variation = random.randint(0, len(self.sounds[name]) - 1)
                if variation >= 0:
                    sound_variation = variation
                sound = self.sounds[name][sound_variation]
                sound.set_volume(volume * self.volume)

                pygame.mixer.Channel(i).set_source_location(angle, distance * 255)
                pygame.mixer.Channel(i).play(sound, loops)

                self.sound_queue[name] = sound_cooldown

                return
