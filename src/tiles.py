from os.path import join

from images import get_image


class TilesManager:
    def __init__(self):
        self.__tiles_map = {
            '#': get_image(join('tiles', 'wall.png')),
            '.': get_image(join('tiles', 'grass.png')),
            '_': get_image(join('tiles', 'water.png')),
            '~': get_image(join('tiles', 'sand.png')),
            'l': get_image(join('tiles', 'lily.png')),
            'r': get_image(join('tiles', 'red_pad.png')),
            'g': get_image(join('tiles', 'green_pad.png')),
            'b': get_image(join('tiles', 'blue_pad.png')),
            'u': get_image(join('tiles', 'universal_pad.png')),
            'R': get_image(join('tiles', 'red_pad_mag.png')),
            'G': get_image(join('tiles', 'green_pad_mag.png')),
            'B': get_image(join('tiles', 'blue_pad_mag.png')),
            'U': get_image(join('tiles', 'universal_pad_mag.png')),
        }

    def get_tile(self, sign):
        return self.__tiles_map[sign]
