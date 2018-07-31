import pygame
from os.path import join


__image_library = {}


def get_image(image_png):
    global __image_library
    path = join('..', 'images', image_png)
    image = __image_library.get(path)
    if image is None:
        image = pygame.image.load(path)
        __image_library[path] = image
    return image
