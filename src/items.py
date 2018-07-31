from abc import ABC, abstractmethod
from os.path import join

from const import DEFAULT_LAYER
from directions import position_after_moving, opposite_direction
from objects import MockupObject, Cannonball


class Item(ABC):
    """
    Base class for items.
    """
    @abstractmethod
    def __str__(self):
        """
        Displayed name.
        :return: string
        """
        pass

    @property
    @abstractmethod
    def path(self):
        """
        Path to image of this item.
        """
        raise NotImplementedError

    @abstractmethod
    def on_use(self, game):
        """
        Use an item.
        :param game: Game instance.
        :return: True or False, depending on whether that item was used successfully.
        """
        pass

    # Necessary to keep order in player's inventory.
    def __lt__(self, other):
        return str(self) < str(other)


class Gun(Item):
    path = join('objects', 'cannonball.png')

    def __str__(self):
        return "Gun"

    def on_use(self, game):
        direction = game.player.direction_facing
        pos = position_after_moving(game.player.x, game.player.y, direction)
        if game.tiles_map[pos[1]][pos[0]] == '#':
            return False
        collide = game.objects[DEFAULT_LAYER].get(pos)
        if collide is not None and isinstance(collide, MockupObject):
            collide = collide.owner
        if collide is not None:
            collide.on_hit(game, opposite_direction(direction))
        else:
            game.register_object(Cannonball(pos[0], pos[1], direction, 8))
        return True


class SpeedPill(Item):
    path = join('objects', 'speed_pill.png')

    def __str__(self):
        return "Speed Pill"

    def on_use(self, game):
        game.player.modify_speed(2)
        return True


class LilyPlant(Item):
    path = join('tiles', 'lily.png')

    def __str__(self):
        return "Lily Plant"

    def on_use(self, game):
        direction = game.player.direction_facing
        pos = position_after_moving(game.player.x, game.player.y, direction)
        if game.tiles_map[pos[1]][pos[0]] == '_':
            row = game.tiles_map[pos[1]]
            game.tiles_map[pos[1]] = row[:pos[0]] + 'l' + row[pos[0] + 1:]
            return True
        return False
