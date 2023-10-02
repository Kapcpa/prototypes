import math
import pygame
import string


from .main_framework import scale_by, palette_swap
from .extra_functions import clamp
from ..sprites import ui_imgs


class Text:
    def __init__(self, pos, font, text="", text_scale=1, text_color=(255, 255, 255), draw_center=True):
        self.text_pos = pos
        self.offset = [0, 0]

        text = text.upper()

        self.text_img = pygame.Surface(font.get_font_size(text, text_scale))
        self.text_img.fill((0, 0, 0))

        font.render(self.text_img, text, [0, 0], text_scale)
        self.text_img = palette_swap(self.text_img, (255, 255, 255), text_color)

        self.text_img.set_colorkey((0, 0, 0))

        if draw_center:
            self.offset[0] = int(self.text_img.get_width() / 2)
            self.offset[1] = int(self.text_img.get_height() / 2)

    def draw(self, surf, text_alpha=255, offset=[0, 0]):
        text_img = self.text_img.copy()
        if text_alpha != 255:
            text_img.set_alpha(text_alpha)

        surf.blit(text_img, [self.text_pos[0] - self.offset[0] - offset[0], self.text_pos[1] - self.offset[1] - offset[1]])


class Button:
    def __init__(self, pos, font, name, neighbour_buttons={}, button_scale=1, text_scale=2, draw_center=True):
        self.pos = pos

        self.neighbour_buttons = neighbour_buttons
        self.name = name

        self.text_normal = Text(pos, font, name, text_scale, (51, 52, 67))
        self.text_selected = Text(pos, font, name, text_scale)

        self.img = scale_by(ui_imgs["button"], button_scale)
        self.img_selected = scale_by(ui_imgs["button_selected"], button_scale)
        self.img_offset = [0, 0]
        if draw_center:
            self.img_offset[0] = int(self.img.get_width() / 2)
            self.img_offset[1] = int(self.img.get_height() / 2)

    def update(self, engine, selected_button=""):
        pass

    def draw(self, surf, selected_button=""):
        if self.name == selected_button:
            self.text_selected.draw(surf)

            surf.blit(self.img_selected, (self.pos[0] - self.img_offset[0], self.pos[1] - self.img_offset[1]))
        else:
            self.text_normal.draw(surf)

            surf.blit(self.img, (self.pos[0] - self.img_offset[0], self.pos[1] - self.img_offset[1]))


class TextField:
    def __init__(self, pos, font, enabling_button, text_scale=1, start_text="text_field", draw_center=False):
        self.pos = pos
        self.font = font
        self.scale = text_scale
        self.draw_center = draw_center

        self.enabling_button = enabling_button

        self.start_text = Text(pos, font, start_text, text_scale, (51, 52, 67), draw_center)
        self.text_field = Text(pos, font, "", text_scale, (255, 255, 255), draw_center)

        self.text = ""

        self.blink_timer = 0
        self.blink_text = Text(pos, font, "", text_scale, (51, 52, 67), draw_center)

    def update_text(self, key):
        if key == 'backspace':
            self.text = self.text[:-1]
        if key == "space":
            self.text += " "

        if key not in list(string.ascii_lowercase) + [str(i) for i in range(0, 10)]:
            return

        self.text += key

    def update(self, engine, selected_button=""):
        if self.enabling_button != selected_button:
            self.text_field = Text(self.pos, self.font, "", self.scale, (255, 255, 255), self.draw_center)
            return

        self.text_field = Text(self.pos, self.font, self.text, self.scale, (255, 255, 255), self.draw_center)

        self.blink_timer += 1 * engine.dt

        if int(self.blink_timer % 120) < 60:
            self.blink_text = Text(self.pos, self.font, self.text + "_", self.scale, (255, 255, 255), self.draw_center)

            return

        self.blink_text = Text(self.pos, self.font, self.text, self.scale, (255, 255, 255), self.draw_center)

    def draw(self, surf, selected_button=""):
        if self.enabling_button != selected_button:
            return

        if not self.text:
            self.start_text.draw(surf)

            return

        self.blink_text.draw(surf)

        self.text_field.draw(surf)


class Switch:
    def __init__(self, pos, font, changing_bool, name, neighbour_buttons={}, button_scale=1, text_scale=2, draw_center=True):
        self.pos = pos

        self.changing_bool = changing_bool
        self.neighbour_buttons = neighbour_buttons
        self.name = name

        self.img = scale_by(ui_imgs["switch"], button_scale)
        self.img_selected = scale_by(ui_imgs["switch_selected"], button_scale)
        self.img_offset = [0, 0]
        if draw_center:
            self.img_offset[0] = int(self.img.get_width() / 2)
            self.img_offset[1] = int(self.img.get_height() / 2)

        text_pos = [pos[0] + self.img_offset[0] + 2, pos[1] - int(font.get_font_size("0", text_scale)[1] / 2)]

        self.text_normal = Text(text_pos.copy(), font, name, text_scale, (51, 52, 67), draw_center=False)
        self.text_selected = Text(text_pos.copy(), font, name, text_scale, draw_center=False)

        self.flash = 0

    def update(self, engine, selected_button=""):
        if self.name == selected_button:
            self.flash += 0.08 * engine.dt
        else:
            self.flash = 0

    def draw(self, surf, selected_button=""):
        surf.blit(self.img, (self.pos[0] - self.img_offset[0], self.pos[1] - self.img_offset[1]))
        self.text_normal.draw(surf)

        if self.name == selected_button:
            text_alpha = int(255 * (math.sin(self.flash) * 0.6 + 0.2 + 0.6 * int(self.changing_bool)))

            self.text_selected.draw(surf, text_alpha)

            flash_img = self.img_selected.copy()
            flash_img.set_alpha(text_alpha)

            surf.blit(flash_img, (self.pos[0] - self.img_offset[0], self.pos[1] - self.img_offset[1]))
            return

        if self.changing_bool:
            self.text_selected.draw(surf)

            surf.blit(self.img_selected, (self.pos[0] - self.img_offset[0], self.pos[1] - self.img_offset[1]))
            return


class InputSwitch:
    def __init__(self, pos, font, changing_bool, name, neighbour_buttons={}, button_scale=1, text_scale=2, draw_center=True):
        self.pos = pos

        self.changing_bool = changing_bool
        self.neighbour_buttons = neighbour_buttons
        self.name = name

        self.img = scale_by(ui_imgs["input_switch"], button_scale)
        self.img_selected = scale_by(ui_imgs["input_switch_selected"], button_scale)
        self.img_offset = [0, 0]
        if draw_center:
            self.img_offset[0] = int(self.img.get_width() / 2)
            self.img_offset[1] = int(self.img.get_height() / 2)

        text_pos = [pos[0] + self.img_offset[0] + 2, pos[1] - int(font.get_font_size("0", text_scale)[1] / 2)]

        self.text_normal = Text(text_pos.copy(), font, name, text_scale, (51, 52, 67), draw_center=False)
        self.text_selected = Text(text_pos.copy(), font, name, text_scale, draw_center=False)

        self.flash = 0

    def update(self, engine, selected_button=""):
        if self.name == selected_button:
            self.flash += 0.08 * engine.dt
        else:
            self.flash = 0

    def draw(self, surf, selected_button=""):
        surf.blit(self.img, (self.pos[0] - self.img_offset[0], self.pos[1] - self.img_offset[1]))
        self.text_normal.draw(surf)

        if self.name == selected_button:
            text_alpha = int(255 * (math.sin(self.flash) * 0.6 + 0.2 + 0.6 * int(self.changing_bool)))

            self.text_selected.draw(surf, text_alpha)

            flash_img = self.img_selected.copy()
            flash_img.set_alpha(text_alpha)

            surf.blit(flash_img, (self.pos[0] - self.img_offset[0], self.pos[1] - self.img_offset[1]))
            return

        if self.changing_bool:
            self.text_selected.draw(surf)

            surf.blit(self.img_selected, (self.pos[0] - self.img_offset[0], self.pos[1] - self.img_offset[1]))
            return


class Slider:
    def __init__(self, pos, font, name, neighbour_buttons={}, start_value=0, button_scale=1, text_scale=2, slider_color=(51, 52, 67)):
        self.pos = pos

        self.neighbour_buttons = neighbour_buttons
        self.name = name

        self.value = start_value  # 0 <= value <= 1
        self.slider_size = 100 * button_scale

        self.slider_color = slider_color
        self.slider_scale = 4 * button_scale

        self.slider_img = scale_by(ui_imgs["slider"], button_scale)
        self.slider_img_selected = scale_by(ui_imgs["slider_selected"], button_scale)
        self.slider_img_offset = [int(self.slider_img.get_width() / 2), int(self.slider_img.get_height() / 2)]

        text_pos = [pos[0] + self.slider_size + self.slider_img_offset[0] + 2,
                    pos[1] - int(font.get_font_size("0", text_scale)[1] / 2)]

        self.text_normal = Text(text_pos.copy(), font, name, text_scale, (51, 52, 67), draw_center=False)
        self.text_selected = Text(text_pos.copy(), font, name, text_scale, draw_center=False)

    def update(self, engine, selected_button=""):
        if self.name != selected_button:
            return

        if pygame.key.get_pressed()[pygame.K_LEFT]:
            self.value -= 0.04 * engine.dt
        if pygame.key.get_pressed()[pygame.K_RIGHT]:
            self.value += 0.04 * engine.dt

        self.value = clamp(self.value, 0, 1)

    def draw(self, surf, selected_button=""):
        pygame.draw.line(surf, self.slider_color, (self.pos[0], self.pos[1]), (self.pos[0] + self.slider_size, self.pos[1]), self.slider_scale)

        pos = (self.pos[0] + self.slider_size * self.value - self.slider_img_offset[0], self.pos[1] - self.slider_img_offset[1])
        if self.name == selected_button:
            self.text_selected.draw(surf)

            surf.blit(self.slider_img_selected, pos)
        else:
            self.text_normal.draw(surf)

            surf.blit(self.slider_img, pos)
