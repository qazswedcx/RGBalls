import pygame
from os.path import join

from images import get_image
from levels import unpack_level
from const import TILE_SIZE, CLOCK_TICK, color_to_index, PLAYER_X, PLAYER_Y, in_render_range
from objects import Player, Ball, Diamond, Event
from tiles import TilesManager


class Game:
    def __init__(self, level_number):
        try:
            self.level = unpack_level(level_number)
        except FileNotFoundError:
            self.win_stars = ['level not found']
            return
        self.map_x_size = self.level.width + 2
        self.map_y_size = self.level.height + 2
        self.tiles_map = [self.map_x_size * '#']
        for row in self.level.tiles:
            self.tiles_map.append('#' + row + '#')
        self.tiles_map.append(self.map_x_size * '#')
        self.screen = pygame.display.get_surface()
        self.tiles_manager = TilesManager()
        self.background_path = join('tiles', 'background.png')
        self.player = None
        self.holding_arrows = {
            pygame.K_UP: False,
            pygame.K_DOWN: False,
            pygame.K_LEFT: False,
            pygame.K_RIGHT: False
        }
        # Objects' world has three layers. Most important layer is
        # layer 1 - almost all objects are there.
        self.objects = [{}, {}, {}]
        self.events = {}
        self.balls_left = [0, 0, 0]
        self.diamonds_left = 0
        self.foreground = []
        # Register objects
        for obj in self.level.objects:
            self.register_object(obj)
        action = self.game_loop()
        self.win_stars = ['_', '_', '_']
        if action == 'win':
            self.win_stars[0] = '*'  # First star is for winning game
            if self.diamonds_left == 0:  # Second is for collecting all diamonds
                self.win_stars[1] = '*'
            if self.player.steps <= self.level.steps:  # Third is for finishing in enough steps
                self.win_stars[2] = '*'
        elif action == 'retry':
            self.win_stars = ['retry']
        elif action == 'lose':
            self.win_stars = ['lose']

    def register_object(self, obj):
        if isinstance(obj, Player):
            self.player = obj
        elif isinstance(obj, Event):
            self.events[(obj.x, obj.y)] = obj
        else:
            if isinstance(obj, Ball):
                if obj.color[0] == self.tiles_map[obj.y][obj.x].lower():
                    obj.on_pad = True
                else:
                    self.balls_left[color_to_index(obj.color)] += 1
            elif isinstance(obj, Diamond):
                self.diamonds_left += 1
            self.objects[obj.layer][(obj.x, obj.y)] = obj

    def render_tiles(self):
        for i in range(self.map_x_size):
            for j in range(self.map_y_size):
                x = PLAYER_X + (i - self.player.x) * TILE_SIZE - self.player.in_move_delta_x
                y = PLAYER_Y + (j - self.player.y) * TILE_SIZE - self.player.in_move_delta_y
                if in_render_range(x, y):
                    self.screen.blit(self.tiles_manager.get_tile(self.tiles_map[j][i]), (x, y))

    def render_objects(self):
        for layer in self.objects:
            for obj in list(layer.values()):
                obj.render(self)

    def render_foreground(self):
        """
        Foreground sprites are need to be created by other objects and
        added to self.foreground every frame as triple:
         * x-coordinate on screen,
         * y-coordinate on screen,
         * sprite path.
        """
        for obj_x, obj_y, obj_sprite_path in self.foreground:
            self.screen.blit(get_image(obj_sprite_path), (obj_x, obj_y))
        self.foreground.clear()

    def tile_is_free(self, x, y, layer):
        """
        Check whether any object (including Player) is in coordinates.
        :param x, y: Coordinates.
        :param layer: Layer (0, 1 or 2).
        :return: True or False.
        """
        if (x, y) in self.objects[layer] or (self.player.x, self.player.y) == (x, y):
            return False
        return True

    def reset_arrow_keys(self):
        for key in self.holding_arrows.keys():
            self.holding_arrows[key] = False

    def game_loop(self):
        self.player.init_function(self)
        clock = pygame.time.Clock()
        while True:
            # Events
            events = pygame.event.get()
            pressed = pygame.key.get_pressed()
            for event in events:
                if event.type == pygame.QUIT:
                    quit(0)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        return None
                    if event.key == pygame.K_h:
                        self.player.switch_hud()
                    if event.key == pygame.K_z:
                        self.player.select_previous_item()
                    if event.key == pygame.K_x:
                        self.player.select_next_item()
                    if event.key == pygame.K_SPACE:
                        self.player.use_item(self)
                    if event.key == pygame.K_r:
                        return 'retry'
                    if event.key in self.holding_arrows.keys():
                        self.holding_arrows[event.key] = True
                if event.type == pygame.KEYUP:
                    if event.key in self.holding_arrows.keys():
                        self.holding_arrows[event.key] = False
            if not self.player.in_move:
                direction = False
                if self.holding_arrows[pygame.K_UP]:
                    direction = 'up'
                elif self.holding_arrows[pygame.K_DOWN]:
                    direction = 'down'
                elif self.holding_arrows[pygame.K_LEFT]:
                    direction = 'left'
                elif self.holding_arrows[pygame.K_RIGHT]:
                    direction = 'right'
                if direction:
                    self.player.before_step(self, direction)

            self.player.update(self)
            for layer in self.objects:
                for obj in list(layer.values()):
                    obj.update(self)

            if self.balls_left == [0, 0, 0]:
                return 'win'
            if self.player.dead:
                return 'lose'

            # Render
            self.screen.fill((0, 0, 0))
            self.render_tiles()
            self.render_objects()
            self.player.render(self)
            self.render_foreground()
            pygame.display.flip()
            clock.tick(CLOCK_TICK)
