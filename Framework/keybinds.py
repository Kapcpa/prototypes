import pygame

from .main_framework import data_update
from .extra_functions import load_bonus_property
from .global_values import game_data


class Key:
    def __init__(self, keycode: str, mod: str):
        self.key = pygame.key.key_code(keycode)
        self.key_code = keycode

        self.mod = self.get_mode(mod)

    @staticmethod
    def mode_name(mod: int) -> str:
        mods = {
            pygame.KMOD_SHIFT: 'shift',
            pygame.KMOD_LSHIFT: 'lshift',
            pygame.KMOD_RSHIFT: 'rshift',
            pygame.KMOD_CTRL: 'ctrl',
            pygame.KMOD_LCTRL: 'lctrl',
            pygame.KMOD_RCTRL: 'rctrl',
            pygame.KMOD_ALT: 'alt',
            pygame.KMOD_LALT: 'lalt',
            pygame.KMOD_RALT: 'ralt',
            pygame.KMOD_CAPS: 'caps',
            pygame.KMOD_NUM: 'num',
            pygame.KMOD_GUI: 'gui',
            pygame.KMOD_LGUI: 'lgui',
            pygame.KMOD_RGUI: 'rgui',
            pygame.KMOD_NONE: 'NO MODE'
        }
        return mods[mod] if mod in mods else 'MODE UNKNOWN'

    @staticmethod
    def get_mode(mod: str) -> int:
        mods = {
            'shift': pygame.KMOD_SHIFT,
            'lshift': pygame.KMOD_LSHIFT,
            'rshift': pygame.KMOD_RSHIFT,
            'ctrl': pygame.KMOD_CTRL,
            'lctrl': pygame.KMOD_LCTRL,
            'rctrl': pygame.KMOD_RCTRL,
            'alt': pygame.KMOD_ALT,
            'lalt': pygame.KMOD_LALT,
            'ralt': pygame.KMOD_RALT,
            'caps': pygame.KMOD_CAPS,
            'num': pygame.KMOD_NUM,
        }
        return mods[mod] if mod in mods else pygame.KMOD_NONE

    def __eq__(self, other):
        return other.key == self.key and ((other.mod & self.mod) if self.mod != pygame.KMOD_NONE else True)


class InputManager:
    def __init__(self, input_data):
        self.keys = {}

        for input_name in input_data:
            mod = load_bonus_property("mod", input_data[input_name], None)

            self.keys[input_name] = Key(input_data[input_name]["key"], mod)

    def change_keybinds(self, input_name, key, mod=None):
        game_data_updated = game_data
        game_data_updated["keybinds"][input_name] = {"key": key, "mod": mod}
        data_update(game_data_updated, "Data/Levels/game_data.json")

        self.keys = InputManager(game_data_updated["keybinds"]).keys
