import json

# initialize frameworks
import pygame.transform

from pygame.locals import *

pygame.init()

scale = 1
colorkey = (172, 50, 50)

MONITOR_SIZE = pygame.display.get_desktop_sizes()[0]
WINDOW_SIZE = (768, 432)  # monitor size (1366, 768), game old resolution (800, 450)

game_data = json.load(open("Data/Levels/game_data.json", ))

global screen

if game_data["game_data"]["fullscreen"]:
    screen = pygame.display.set_mode(MONITOR_SIZE, DOUBLEBUF | OPENGL | FULLSCREEN | SCALED)
else:
    screen = pygame.display.set_mode(WINDOW_SIZE, DOUBLEBUF | OPENGL)

pygame.display.set_caption("Gaem")
