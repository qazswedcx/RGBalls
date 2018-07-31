import pygame
from os.path import join

pygame.font.init()
SMALL_FONT = pygame.font.Font(join('..', 'fonts', 'open-sans.ttf'), 14)
MID_FONT = pygame.font.Font(join('..', 'fonts', 'open-sans.ttf'), 36)
BIG_FONT = pygame.font.Font(join('..', 'fonts', 'open-sans.ttf'), 144)
TILE_SIZE = 32
CLOCK_TICK = 60
# Preferred at least 20x15 in proportion 4:3
SCREEN_X_TILES_LENGTH = 20
SCREEN_Y_TILES_LENGTH = 15
SCREEN_X_SIZE = TILE_SIZE * SCREEN_X_TILES_LENGTH
SCREEN_Y_SIZE = TILE_SIZE * SCREEN_Y_TILES_LENGTH
PLAYER_X = (SCREEN_X_SIZE - TILE_SIZE) / 2
PLAYER_Y = (SCREEN_Y_SIZE - TILE_SIZE) / 2
DEFAULT_LAYER = 1
HUD_X_POSITION = 15
HUD_Y_POSITION = 15
HUD_BORDER_SIZE = 2
HUD_BOX_SIZE = 34
STAR_SIZE = 41
GAME_TITLE = "RGBalls"

colors = {
    'orange': (238, 154, 0),
    'blue': (0, 0, 139),
    'white': (255, 255, 255),
    'purple': (145, 44, 238),
    'black': (0, 0, 0),
}


def lwr(x):
    """
    Lambda wrapper.
    """
    return lambda *args, **kwargs: x


def color_to_index(color):
    """
    Match color with its array index.
    :param color: 'red', 'green' or 'blue'.
    :return: 0, 1 or 2.
    """
    if color == 'red':
        return 0
    elif color == 'green':
        return 1
    elif color == 'blue':
        return 2
    else:
        exit("Error in color_to_index function: \"" + color + "\" is not a color.")


def in_render_range(x, y):
    """
    Check whether coordinates are in window range
    :param x, y: Coordinates.
    :return: True or False.
    """
    return -TILE_SIZE < x < SCREEN_X_SIZE + TILE_SIZE and -TILE_SIZE < y < SCREEN_Y_SIZE + TILE_SIZE
