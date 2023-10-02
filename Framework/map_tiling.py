import pygame


def load_from_png(file, pixel_size=1):
    pixel_map = file.copy()
    pixel_map = pygame.transform.scale(pixel_map, (pixel_map.get_width() * pixel_size,
                                                   pixel_map.get_height() * pixel_size))

    binary_map = []

    for y in range(pixel_map.get_height()):
        binary_map.append([])
        for x in range(pixel_map.get_width()):
            if pixel_map.get_at((x, y)) == (0, 0, 0):
                binary_map[y].append('1')
            else:
                binary_map[y].append('0')

    return binary_map


# from left to right: 10 - 4 rot, 1 - 2 rot, 3 - 0 rot
def load_tileset(tileset_img, save=False, colorkey=(172, 50, 50)):
    loaded_tileset_img = pygame.Surface((10 * 4 * 16 + 2 * 16 + 3 * 16, 16))
    tileset = []

    offset = 0
    for i in range(14):
        img = pygame.Surface((16, 16))
        img.blit(tileset_img, (-i * 16, 0))
        img.set_colorkey(colorkey)
        if i < 10:
            for x in range(4):
                img_rot = pygame.transform.rotate(img.copy(), x * 90)
                tileset.append(img_rot)

                loaded_tileset_img.blit(img_rot, (offset * 16, 0))
                offset += 1
        elif i == 10:
            for x in range(2):
                img_rot = pygame.transform.rotate(img.copy(), x * 90)
                tileset.append(img_rot)

                loaded_tileset_img.blit(img_rot, (offset * 16, 0))
                offset += 1
        else:
            tileset.append(img)

            loaded_tileset_img.blit(img, (offset * 16, 0))
            offset += 1

    if save:
        pygame.image.save(loaded_tileset_img, 'Sprites/loaded_tileset.png')

    return tileset


directions_list = {
                   '0': ['X0X',
                         '0X1',
                         'X11'],
                   '1': ['X11',
                         '0X1',
                         'X0X'],
                   '2': ['11X',
                         '1X0',
                         'X0X'],
                   '3': ['X0X',
                         '1X0',
                         '11X'],
                   '4': ['X0X',
                         '1X1',
                         'X1X'],
                   '5': ['X1X',
                         '0X1',
                         'X1X'],
                   '6': ['X1X',
                         '1X1',
                         'X0X'],
                   '7': ['X1X',
                         '1X0',
                         'X1X'],
                   '8': ['011',
                         '1X1',
                         '111'],
                   '9': ['111',
                         '1X1',
                         '011'],
                   '10': ['111',
                          '1X1',
                          '110'],
                   '11': ['110',
                          '1X1',
                          '111'],
                   '12': ['X0X',
                          '0X1',
                          'X0X'],
                   '13': ['X1X',
                          '0X0',
                          'X0X'],
                   '14': ['X0X',
                          '1X0',
                          'X0X'],
                   '15': ['X0X',
                          '0X0',
                          'X1X'],
                   '16': ['010',
                          '1X1',
                          'X1X'],
                   '17': ['01X',
                          '1X1',
                          '01X'],
                   '18': ['X1X',
                          '1X1',
                          '010'],
                   '19': ['X10',
                          '1X1',
                          'X10'],
                   '20': ['010',
                          '1X1',
                          '011'],
                   '21': ['011',
                          '1X1',
                          '010'],
                   '22': ['110',
                          '1X1',
                          '010'],
                   '23': ['010',
                          '1X1',
                          '110'],
                   '24': ['00X',
                          '0X1',
                          'X10'],
                   '25': ['X10',
                          '0X1',
                          '00X'],
                   '26': ['01X',
                          '1X0',
                          'X00'],
                   '27': ['X00',
                          '1X0',
                          '01X'],
                   '28': ['010',
                          '1X1',
                          'X0X'],
                   '29': ['01X',
                          '1X0',
                          '01X'],
                   '30': ['X0X',
                          '1X1',
                          '010'],
                   '31': ['X10',
                          '0X1',
                          'X10'],
                   '32': ['110',
                          '1X1',
                          'X0X'],
                   '33': ['01X',
                          '1X0',
                          '11X'],
                   '34': ['X0X',
                          '1X1',
                          '011'],
                   '35': ['X11',
                          '0X1',
                          'X10'],
                   '36': ['011',
                          '1X1',
                          'X0X'],
                   '37': ['11X',
                          '1X0',
                          '01X'],
                   '38': ['X0X',
                          '1X1',
                          '110'],
                   '39': ['X10',
                          '0X1',
                          'X11'],
                   '40': ['X0X',
                          '1X1',
                          'X0X'],
                   '41': ['X1X',
                          '0X0',
                          'X1X'],
                   '42': ['010',
                          '1X1',
                          '010'],
                   '43': ['000',
                          '0X0',
                          '000'],
                   '44': ['111',
                          '1X1',
                          '111']
                   }


def find_tile_dir(map_array, base_x, base_y):
    i = len(directions_list) - 2

    tile_directions = []
    for y in range(3):
        layer_string = ''
        for x in range(3):
            if 0 <= base_y + y - 1 < len(map_array) and 0 <= base_x + x - 1 < len(map_array[0]):
                layer_string += map_array[base_y + y - 1][base_x + x - 1]
            else:
                layer_string += '0'
        tile_directions.append(layer_string)
    for tile_type in directions_list:
        neighbours = directions_list[tile_type]

        compatible = True

        y = 0
        for layer in neighbours:
            for x in range(3):
                if layer[x] != 'X':
                    if layer[x] != tile_directions[y][x]:
                        compatible = False
            y += 1

        if compatible:
            i = int(tile_type)

    return i
