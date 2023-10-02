import pygame
import math
import json

from pygame import Vector2

pygame.init()

pygame.mixer.pre_init(frequency=44100, size=-16, channels=8, buffer=512)

channel_num = 32

pygame.mixer.set_num_channels(channel_num)


def load_map(path):
    f = open(path + '.txt', 'r')
    data = f.read()
    f.close()
    data = data.split('\n')
    game_map = []
    for row in data:
        game_map.append(list(row))
    return game_map


def clip(surf, x, y, x_size, y_size, colorkey=(0, 0, 0)):
    handle_surf = surf.copy()
    clipR = pygame.Rect(x, y, x_size, y_size)
    handle_surf.set_clip(clipR)
    image = surf.subsurface(handle_surf.get_clip())
    image.set_colorkey(colorkey)
    return image


def animation_crop(surf, frame_w, frames_count=-1, colorkey=(0, 0, 0)):
    if frames_count == -1:
        frames_count = surf.get_width() / frame_w

    anim_frames = []
    for i in range(int(frames_count)):
        anim_frames.append(clip(surf, 0 + i * frame_w, 0, frame_w, surf.get_height(), colorkey))

    return anim_frames


class Font:
    def __init__(self, path):
        self.spacing = 1
        self.character_order = [
            'A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T',
            'U', 'V', 'W', 'X', 'Y', 'Z', '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '/', ':', '+', '-',
            '%', '.', '[', ']', '_', ',', '?'
        ]
        font_img = pygame.image.load(path).convert()
        current_char_width = 0
        self.characters = []
        character_count = 0
        for x in range(font_img.get_width()):
            c = font_img.get_at((x, 0))
            if c[0] == 217:
                char_img = clip(font_img, x - current_char_width, 0, current_char_width, font_img.get_height())
                self.characters.append(0)
                self.characters[character_count] = char_img.copy()
                character_count += 1
                current_char_width = 0
            else:
                current_char_width += 1
        self.space_width = self.characters[0].get_width()

    def get_font_size(self, text, scale):
        height = self.characters[0].get_height() * scale
        width = 0

        for char in text:
            if char != ' ':
                ix = self.character_order.index(char)
                width += self.characters[ix].get_width() * scale + self.spacing
            else:
                width += self.space_width + self.spacing * scale

        return [width, height]

    def render(self, surf, text, loc, scale):
        x_offset = 0
        for char in text:
            if char != ' ':
                ix = self.character_order.index(char)
                blit_img = pygame.transform.scale(self.characters[ix], (self.characters[ix].get_width() * scale,
                                                                        self.characters[ix].get_height() * scale))
                surf.blit(blit_img, (loc[0] + x_offset, loc[1]))
                x_offset += self.characters[ix].get_width() * scale + self.spacing
            else:
                x_offset += self.space_width + self.spacing * scale


def palette_swap(surf, old_color, new_color):
    img_copy = pygame.Surface(surf.get_size())
    img_copy.fill(new_color)
    surf.set_colorkey(old_color)
    img_copy.blit(surf, (0, 0))
    img_copy.set_colorkey((172, 50, 50))
    return img_copy


def write_new_data(file_path, new_data):
    file = open(file_path, 'r')
    data = file.read()
    file = open(file_path, 'w')
    file.write(new_data + '\n' + data)
    file.close()


def data_update(new_data, path):
    with open(path, "w") as data_file:
        json.dump(new_data, data_file)


def connect_points(surf, i, j, point_list):
    pygame.draw.line(surf, (255, 255, 255), point_list[i], point_list[j])


def outline(surf, outline_color=(255, 255, 255)):
    mask = pygame.mask.from_surface(surf)
    surf_mask = mask.to_surface()
    surf_mask.set_colorkey((0, 0, 0))
    outline_surf = pygame.Surface((surf.get_width() + 2, surf.get_height() + 2))

    outline_surf.fill((100, 100, 100))
    outline_surf.blit(surf_mask, (0, 1))
    outline_surf.blit(surf_mask, (2, 1))
    outline_surf.blit(surf_mask, (1, 2))
    outline_surf.blit(surf_mask, (1, 0))

    outline_surf = palette_swap(outline_surf, (255, 255, 255), outline_color)
    outline_surf.set_colorkey((100, 100, 100))

    return outline_surf


# ik_obj.solve_ik(0, ik_boj.points[-1], target) <= thats how you start solving the ik for some target

class IK:
    def __init__(self, point_list, target, max_range):
        self.points = list(map(Vector2, point_list))
        self.max_range = max_range
        self.target = target

        self.rel_points = []
        self.angles = []

        for i in range(1, len(self.points)):
            self.rel_points.append(self.points[i] - self.points[i - 1])
            self.angles.append(0)

    def solve_ik(self, i, endpoint, target):
        if i < len(self.points) - 2:
            endpoint = self.solve_ik(i + 1, endpoint, target)
        current_point = self.points[i]

        angle = (endpoint - current_point).angle_to(target - current_point)
        self.angles[i] += angle

        return current_point + (endpoint - current_point).rotate(angle)

    def render(self, surf, line_color):
        angle = 0
        for i in range(1, len(self.points)):
            angle += self.angles[i - 1]
            self.points[i] = self.points[i - 1] + self.rel_points[i - 1].rotate(angle)

        for i in range(1, len(self.points)):
            prev = self.points[i - 1]
            cur = self.points[i]

            pygame.draw.line(surf, line_color, prev, cur, 3)


def load_animation(path, frame_duration, name, start_id=0, color_key=True):
    global animation_frames
    animation_name = name
    animation_frame_data = []
    n = 0
    for frame in frame_duration:
        animation_frame_id = animation_name + "_" + str(n + start_id)
        img_loc = path + "/" + animation_frame_id + ".png"
        if color_key:
            animation_image = pygame.image.load(img_loc).convert()
            animation_image.set_colorkey((172, 50, 50))
        else:
            animation_image = pygame.image.load(img_loc)
        animation_frames[animation_frame_id] = animation_image.copy()
        for i in range(frame):
            animation_frame_data.append(animation_frame_id)
        n += 1
    return animation_frame_data


def load_animation_from_list(frames, frame_duration, name, start_id=0, color_key=True):
    global animation_frames
    animation_name = name
    animation_frame_data = []
    n = 0
    for frame in frame_duration:
        animation_frame_id = animation_name + "_" + str(n + start_id)
        animation_image = frames[n + start_id]
        if color_key:
            animation_image.set_colorkey((172, 50, 50))
        animation_frames[animation_frame_id] = animation_image
        for i in range(frame):
            animation_frame_data.append(animation_frame_id)
        n += 1
    return animation_frame_data


def change_action(action_var, frame, new_value):
    if action_var != new_value:
        action_var = new_value
        frame = 0
    return action_var, frame


global animation_frames
animation_frames = {}

animation_database = {}


def palette_from_img(file_name):
    img = pygame.image.load(file_name)
    palette = []
    for x in range(img.get_width()):
        palette.append(img.get_at((x, 0)))

    return palette


def dda(x1, y1, x2, y2, tiles):
    x, y = x1, y1
    length = math.dist([x1, y1], [x2, y2])
    try:
        dx = (x2 - x1) / int(length)
        dy = (y2 - y1) / int(length)

        intersection = None
        steps = 0
        max_steps = int(length * 1.2)
        while steps < max_steps and intersection is None:
            steps += 1
            x += dx
            y += dy
            try:
                if tiles[int(y / 16)][int(x / 16)] == '1':
                    intersection = [x, y]
                    return intersection
            except IndexError:
                pass

        return [x2, y2]
    except ZeroDivisionError:
        return None


# about 4.3 times faster but also less accurate
# points are the points on tile map so x1 = int(point_x / 16) and so on
def tiled_dda(x1, y1, x2, y2, tiles):
    x, y = x1, y1
    dx = x2 - x1
    dy = y2 - y1

    inverted = False

    step = int(math.copysign(1, dx))
    gradient_step = int(math.copysign(1, dy))

    longest = abs(dx)
    shortest = abs(dy)

    if longest < shortest:
        inverted = True

        longest, shortest = shortest, longest
        step, gradient_step = gradient_step, step

    gA = int(longest / 2)

    intersection = None

    for i in range(0, longest + 1):
        if inverted:
            y += step
        else:
            x += step

        gA += shortest
        if gA >= longest:
            if inverted:
                x += gradient_step
            else:
                y += gradient_step
            gA -= longest

        if 0 <= x < len(tiles[0]) and 0 <= y < len(tiles):
            if tiles[y][x] != '0':
                intersection = [x, y]
                return intersection

    return intersection


def scale_by(surf, x):
    return pygame.transform.scale(surf, (int(surf.get_width() * x), int(surf.get_height() * x)))


def crop_sprite(source, sprite_height, colorkey=(172, 50, 50), list_reverse=False):
    crop_sprites = []
    for i in range(int(source.get_height() / sprite_height)):
        img = clip(source, 0, i * sprite_height, source.get_width(), sprite_height, colorkey)
        crop_sprites.append(img)
    if list_reverse:
        crop_sprites.reverse()
    return crop_sprites


def sprite_chunk(source, side_chunks, colorkey=(0, 0, 0)):
    chunk_size = source.get_width() / side_chunks

    chunk_img_list = []
    for y in range(side_chunks):
        chunk_img_list.append([])
        for x in range(side_chunks):
            img = clip(source, x * chunk_size, y * chunk_size, chunk_size, chunk_size, colorkey)
            chunk_img_list[y].append(img)

    return chunk_img_list
