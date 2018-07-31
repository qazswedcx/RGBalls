from sys import exit
from abc import ABC
from bisect import bisect_left

from wrap_text import render_textrect, TextRectException
from directions import position_after_moving, assert_direction, opposite_direction
from images import get_image
from const import *


class Event:
    def __init__(self, x, y, event, times_triggered=1, miscellaneous=None):
        self.times_triggered = times_triggered
        self.x, self.y = x, y
        self.event = event
        self.miscellaneous = miscellaneous

    def trigger(self, game):
        self.event(game, self)
        self.times_triggered -= 1
        if self.times_triggered == 0:
            game.events.pop((self.x, self.y))


class GameObject(ABC):
    def __init__(self, x, y, miscellaneous=None):
        """
        Create object in place (x, y).
        :param x, y: Coordinates.
        """
        self.sprite_path = None
        self.x, self.y = x, y
        # Miscellaneous can be used to keep any additional info that you might use outside of this object.
        self.miscellaneous = miscellaneous
        # Default layer for all objects
        self.layer = DEFAULT_LAYER

    def before_step(self, game, direction):
        """
        Call when object attempts to move from current position.
        :param game: Game instance.
        :param direction: Direction of move.
        """
        pass

    def after_step(self, game):
        """
        Call when object arrives to new position.
        :param game: Game instance.
        """
        pass

    def on_touch(self, game, direction):
        """
        Call when player touches this object from a direction.
        :param game: Game instance.
        :param direction: Direction of touch.
        """
        pass

    def on_hit(self, game, direction):
        """
        Call when hit by another object (probably cannonball, enemy, ...).
        :param game: Game instance.
        :param direction: Direction of hit.
        """
        pass

    def update(self, game):
        """
        This function is called every frame for every object and contains game logic.
        :param game: Game instance.
        """
        pass

    def render(self, game):
        """
        This function is called every frame for every object and
        provides way to render object.
        :param game: Game instance.
        """
        if self.sprite_path is not None:
            x = PLAYER_X + (self.x - game.player.x) * TILE_SIZE - game.player.in_move_delta_x
            y = PLAYER_Y + (self.y - game.player.y) * TILE_SIZE - game.player.in_move_delta_y
            if in_render_range(x, y):
                game.screen.blit(get_image(self.sprite_path), (x, y))


class MockupObject(GameObject):
    """
    This invisible object is created to protect from moving two objects
    to the same place by reserving it. This object should not be created
    on its own (i.e. in levels.py).
    """
    def __init__(self, x, y, game, owner):
        super().__init__(x, y)
        self.owner = owner
        game.objects[self.layer][(x, y)] = self
        self.game = game
        self.time_to_live = 150

    def update(self, _):
        """
        This is a band-aid fix in case some mockup objects don't get cleared.
        """
        self.time_to_live -= 1
        if self.time_to_live == 0:
            self.destroy()

    def destroy(self):
        self.game.objects[self.layer].pop((self.x, self.y))


class MovingObject(GameObject, ABC):
    """
    Base class for moving objects.
    """
    def __init__(self, x, y, speed, miscellaneous=None):
        """
        Create an object. It will move with given speed.
        :param x, y: Coordinates.
        :param speed: Speed in tiles per second.
        """
        super().__init__(x, y, miscellaneous)
        self.step_size = TILE_SIZE * speed / CLOCK_TICK
        self.in_move = False  # Either False or direction of move.
        self.in_move_delta_x = 0
        self.in_move_delta_y = 0

    def modify_speed(self, delta):
        """
        Modify speed of object.
        :param delta: Value added to speed of object.
        """
        self.step_size += TILE_SIZE * delta / CLOCK_TICK

    def update(self, game):
        """
        This function works under assumption that tile object
        is moving to is free (or reserved by MockupObject).
        :param game
        """
        if self.in_move == 'up':
            self.in_move_delta_y -= self.step_size
            if -self.in_move_delta_y >= TILE_SIZE:
                game.objects[self.layer].pop((self.x, self.y))
                self.y -= 1
                self.in_move_delta_y = 0
                game.objects[self.layer][(self.x, self.y)] = self
                self.after_step(game)
        if self.in_move == 'down':
            self.in_move_delta_y += self.step_size
            if self.in_move_delta_y >= TILE_SIZE:
                game.objects[self.layer].pop((self.x, self.y))
                self.y += 1
                self.in_move_delta_y = 0
                game.objects[self.layer][(self.x, self.y)] = self
                self.after_step(game)
        if self.in_move == 'left':
            self.in_move_delta_x -= self.step_size
            if -self.in_move_delta_x >= TILE_SIZE:
                game.objects[self.layer].pop((self.x, self.y))
                self.x -= 1
                self.in_move_delta_x = 0
                game.objects[self.layer][(self.x, self.y)] = self
                self.after_step(game)
        if self.in_move == 'right':
            self.in_move_delta_x += self.step_size
            if self.in_move_delta_x >= TILE_SIZE:
                game.objects[self.layer].pop((self.x, self.y))
                self.x += 1
                self.in_move_delta_x = 0
                game.objects[self.layer][(self.x, self.y)] = self
                self.after_step(game)

    def render(self, game):
        if self.sprite_path is not None:
            x = PLAYER_X + (self.x - game.player.x) * TILE_SIZE - game.player.in_move_delta_x + self.in_move_delta_x
            y = PLAYER_Y + (self.y - game.player.y) * TILE_SIZE - game.player.in_move_delta_y + self.in_move_delta_y
            if in_render_range(x, y):
                game.screen.blit(get_image(self.sprite_path), (x, y))


class Ball(MovingObject):
    def __init__(self, x, y, color, miscellaneous=None):
        super().__init__(x, y, TILE_SIZE / 2, miscellaneous)
        self.on_pad = False
        self.color = color
        if color == 'red':
            self.sprite_path = join('objects', 'red_ball.png')
        elif color == 'green':
            self.sprite_path = join('objects', 'green_ball.png')
        elif color == 'blue':
            self.sprite_path = join('objects', 'blue_ball.png')
        else:
            exit("Error when initializing Ball object: \"" + color + "\" is not a color.")

    def before_step(self, game, direction):
        if game.tiles_map[self.y][self.x] in ['R', 'G', 'B', 'U']:
            self.in_move = False
            return  # Can't move away from magnetic pads.
        pos = position_after_moving(self.x, self.y, direction)
        if not game.tile_is_free(pos[0], pos[1], self.layer):
            return  # Can't move if there is something in this place.
        if game.tiles_map[pos[1]][pos[0]] == '#':
            return  # Can't move if terrain does not allow to do it.
        if game.tiles_map[self.y][self.x] == self.color[0] and self.on_pad:
            self.on_pad = False
            game.balls_left[color_to_index(self.color)] += 1
        self.in_move_delta_x = 0
        self.in_move_delta_y = 0
        self.in_move = direction
        MockupObject(pos[0], pos[1], game, self)

    def after_step(self, game):
        pos = position_after_moving(self.x, self.y, self.in_move)
        if (not game.tile_is_free(pos[0], pos[1], self.layer)) or game.tiles_map[pos[1]][pos[0]] == '#':
            # Ball can't keep moving if there is an obstacle.
            self.in_move = False
        tile = game.tiles_map[self.y][self.x]
        if tile == '~':
            # Ball stops on sand.
            self.in_move = False
        if not self.in_move and (tile == self.color[0] or tile == 'u'):
            # Count ball towards victory.
            self.on_pad = True
            game.balls_left[color_to_index(self.color)] -= 1
        elif tile == self.color[0].capitalize() or tile == 'U':
            # Magnetic pads stop balls regardless of color.
            self.in_move = False
            self.on_pad = True
            game.balls_left[color_to_index(self.color)] -= 1
        elif self.in_move:
            self.before_step(game, self.in_move)

    def on_touch(self, game, direction):
        self.before_step(game, direction)


class Box(MovingObject):
    drowning_speed = 6  # Frames for one image of drowning box

    def __init__(self, x, y, miscellaneous=None):
        super().__init__(x, y, TILE_SIZE / 6, miscellaneous)
        self.sprite_path = join('objects', 'box.png')
        self.drowning = 0

    def before_step(self, game, direction):
        if self.drowning > 0:
            return
        pos = position_after_moving(self.x, self.y, direction)
        if not game.tile_is_free(pos[0], pos[1], self.layer):
            return  # Can't move if there is something in this place.
        pos = position_after_moving(self.x, self.y, direction)
        if game.tiles_map[pos[1]][pos[0]] == '#':
            return  # Can't move if terrain does not allow to do it.
        self.in_move = direction
        MockupObject(pos[0], pos[1], game, self)

    def after_step(self, game):
        self.in_move = False
        if game.tiles_map[self.y][self.x] == '_':
            # Box drowns.
            self.drowning = 1
        if game.tiles_map[self.y][self.x] == 'l':
            # Box and lily drown.
            self.drowning = 1
            row = game.tiles_map[self.y]
            game.tiles_map[self.y] = row[:self.x] + '_' + row[self.x + 1:]

    def on_touch(self, game, direction):
        self.before_step(game, direction)

    def update(self, game):
        if self.drowning == 0:
            super().update(game)
        else:
            sprite_number = str(self.drowning // self.drowning_speed + 1)
            self.sprite_path = join('objects', 'box_drowning_' + sprite_number + '.png')
            self.drowning += 1
        if self.drowning == 6 * self.drowning_speed:
            game.objects[self.layer].pop((self.x, self.y))


class Player(MovingObject):
    def __init__(self, x, y, init_function=lwr(None), miscellaneous=None):
        super().__init__(x, y, TILE_SIZE / 4, miscellaneous)
        self.steps = 0
        self.sprites_paths = {
            'left': join('objects', 'player_left.png'),
            'right': join('objects', 'player_right.png'),
            'up': join('objects', 'player_up.png'),
            'down': join('objects', 'player_down.png'),
        }
        self.hud_path = join('hud', 'stats.png')
        self.inventory_path = join('hud', 'inventory.png')
        self.no_item_path = join('hud', 'no_item.png')
        # List of HUDs:
        # 0 - don't display anything
        # 1 - display balls and diamonds left and steps taken
        # 2 - display items
        self.selected_hud = 1
        self.total_huds = 3
        self.dead = False
        self.direction_facing = 'down'
        # Inventory keeps two lists of same length. First list contains names of items.
        # Second has amount of that item in inventory.
        self.inventory = [[], []]
        self.selected_item_index = 0
        self.init_function = init_function

    def before_step(self, game, direction):
        self.direction_facing = direction
        pos = position_after_moving(self.x, self.y, direction)
        game_object = game.objects[self.layer].get(pos)
        if game_object is None:
            if game.tiles_map[pos[1]][pos[0]] in ['#', '_']:
                return  # Can't move if terrain does not allow to do it.
            self.in_move = direction
            MockupObject(pos[0], pos[1], game, self)
        else:
            game_object.on_touch(game, direction)

    def after_step(self, game):
        self.in_move_delta_x = 0
        self.in_move_delta_y = 0
        self.steps += 1
        self.in_move = False
        event = game.events.get((self.x, self.y))
        if event is not None:
            event.trigger(game)

    def on_hit(self, _, __):
        self.dead = True

    def update(self, game):
        if self.in_move == 'up':
            self.in_move_delta_y -= self.step_size
            if -self.in_move_delta_y >= TILE_SIZE:
                self.y -= 1
                game.objects[self.layer].pop((self.x, self.y))
                self.after_step(game)
        if self.in_move == 'down':
            self.in_move_delta_y += self.step_size
            if self.in_move_delta_y >= TILE_SIZE:
                self.y += 1
                game.objects[self.layer].pop((self.x, self.y))
                self.after_step(game)
        if self.in_move == 'left':
            self.in_move_delta_x -= self.step_size
            if -self.in_move_delta_x >= TILE_SIZE:
                self.x -= 1
                game.objects[self.layer].pop((self.x, self.y))
                self.after_step(game)
        if self.in_move == 'right':
            self.in_move_delta_x += self.step_size
            if self.in_move_delta_x >= TILE_SIZE:
                self.x += 1
                game.objects[self.layer].pop((self.x, self.y))
                self.after_step(game)

    def select_previous_item(self):
        if len(self.inventory[0]) != 0:
            self.selected_item_index = (self.selected_item_index + 1) % len(self.inventory[0])

    def select_next_item(self):
        if len(self.inventory[0]) != 0:
            self.selected_item_index = (self.selected_item_index - 1) % len(self.inventory[0])

    def use_item(self, game):
        if not self.in_move and len(self.inventory[0]) != 0:
            result = self.inventory[0][self.selected_item_index].on_use(game)
            if result is True:
                self.inventory[1][self.selected_item_index] -= 1
                if self.inventory[1][self.selected_item_index] == 0:
                    self.inventory[0].pop(self.selected_item_index)
                    self.inventory[1].pop(self.selected_item_index)
                    if self.selected_item_index > 0:
                        self.selected_item_index -= 1

    def add_item(self, item, amount=1):
        if len(self.inventory[0]) != 0:
            index = bisect_left(self.inventory[0], item)
            if index < len(self.inventory[0]) and str(self.inventory[0][index]) == str(item):
                self.inventory[1][index] += amount
            else:
                self.inventory[0].insert(index, item)
                self.inventory[1].insert(index, amount)
                if index <= self.selected_item_index:
                    self.selected_item_index += 1
        else:
            self.inventory[0].append(item)
            self.inventory[1].append(amount)

    def switch_hud(self):
        self.selected_hud = (self.selected_hud + 1) % self.total_huds

    def render(self, game):
        game.screen.blit(get_image(self.sprites_paths[self.direction_facing]), (PLAYER_X, PLAYER_Y))
        white = colors['white']
        if self.selected_hud == 1:
            game.screen.blit(get_image(self.hud_path), (HUD_X_POSITION, HUD_Y_POSITION))
            center_x = HUD_X_POSITION + HUD_BORDER_SIZE + HUD_BOX_SIZE / 2
            center_y = HUD_Y_POSITION + 2 * HUD_BORDER_SIZE + 3 * HUD_BOX_SIZE / 2
            for i in range(3):
                text = SMALL_FONT.render(str(game.balls_left[i]), True, white)
                rect = text.get_rect(center=(center_x, center_y))
                game.screen.blit(text, rect)
                center_x += HUD_BOX_SIZE + HUD_BORDER_SIZE
            text = SMALL_FONT.render(str(game.diamonds_left), True, white)
            rect = text.get_rect(center=(center_x, center_y))
            game.screen.blit(text, rect)
            center_x = HUD_X_POSITION + 5 * HUD_BORDER_SIZE / 2 + 2 * HUD_BOX_SIZE
            center_y += HUD_BOX_SIZE + HUD_BORDER_SIZE
            text = SMALL_FONT.render("Steps: " + str(self.steps) + "/"
                                     + str(game.level.steps), True, white)
            rect = text.get_rect(center=(center_x, center_y))
            game.screen.blit(text, rect)
        elif self.selected_hud == 2:
            game.screen.blit(get_image(self.inventory_path), (HUD_X_POSITION, HUD_Y_POSITION))
            center_x = HUD_X_POSITION + 5 * HUD_BORDER_SIZE / 2 + 2 * HUD_BOX_SIZE
            center_y = HUD_Y_POSITION + HUD_BORDER_SIZE + HUD_BOX_SIZE / 2
            if len(self.inventory[0]) != 0:
                text = SMALL_FONT.render(str(self.inventory[0][self.selected_item_index]), True, white)
            else:
                text = SMALL_FONT.render("Empty inventory", True, white)
            rect = text.get_rect(center=(center_x, center_y))
            game.screen.blit(text, rect)
            center_x = HUD_X_POSITION + HUD_BORDER_SIZE + HUD_BOX_SIZE / 2
            center_y = HUD_Y_POSITION + 2 * HUD_BORDER_SIZE + 3 * HUD_BOX_SIZE / 2
            text = SMALL_FONT.render("Z", True, white)
            rect = text.get_rect(center=(center_x, center_y))
            game.screen.blit(text, rect)
            center_x += (HUD_BOX_SIZE + HUD_BORDER_SIZE) * 3
            text = SMALL_FONT.render("X", True, white)
            rect = text.get_rect(center=(center_x, center_y))
            game.screen.blit(text, rect)
            corner_x = center_x - TILE_SIZE / 2 - 2 * (HUD_BOX_SIZE + HUD_BORDER_SIZE)
            corner_y = center_y - TILE_SIZE / 2
            if len(self.inventory[0]) != 0:
                game.screen.blit(get_image(self.inventory[0][self.selected_item_index].path), (corner_x, corner_y))
            else:
                game.screen.blit(get_image(self.no_item_path), (corner_x, corner_y))
            if len(self.inventory[0]) != 0:
                center_x -= HUD_BOX_SIZE + HUD_BORDER_SIZE
                text = SMALL_FONT.render(str(self.inventory[1][self.selected_item_index]), True, white)
                rect = text.get_rect(center=(center_x, center_y))
                game.screen.blit(text, rect)
            else:
                corner_x += HUD_BOX_SIZE + HUD_BORDER_SIZE
                game.screen.blit(get_image(self.no_item_path), (corner_x, corner_y))
            center_x = HUD_X_POSITION + 5 * HUD_BORDER_SIZE / 2 + 2 * HUD_BOX_SIZE
            center_y += HUD_BOX_SIZE + HUD_BORDER_SIZE
            text = SMALL_FONT.render("Space: use item", True, white)
            rect = text.get_rect(center=(center_x, center_y))
            game.screen.blit(text, rect)


class Diamond(GameObject):
    def __init__(self, x, y, miscellaneous=None):
        super().__init__(x, y, miscellaneous)
        self.sprite_paths_list = [
            join('objects', 'diamond_1.png'),
            join('objects', 'diamond_2.png'),
            join('objects', 'diamond_3.png'),
        ]
        self.sprite_number = 0
        self.animation_time = 0
        self.max_animation_time = 60

    def on_touch(self, game, _):
        game.diamonds_left -= 1
        game.objects[self.layer].pop((self.x, self.y))

    def update(self, game):
        self.sprite_path = self.sprite_paths_list[self.sprite_number]
        self.animation_time += 1
        if self.animation_time == self.max_animation_time:
            self.animation_time = 0
            self.sprite_number += 1
            if self.sprite_number == len(self.sprite_paths_list):
                self.sprite_number = 0


class Envelope(GameObject):
    def __init__(self, x, y, message, miscellaneous=None):
        super().__init__(x, y, miscellaneous)
        self.sprite_path = join('objects', 'envelope.png')
        self.message = message

    def on_touch(self, game, _):
        game.objects[self.layer].pop((self.x, self.y))
        clock = pygame.time.Clock()
        message_loop = True
        rect = pygame.Rect(100, 100, SCREEN_X_SIZE - 200, SCREEN_Y_SIZE - 200)
        game.reset_arrow_keys()
        try:
            text = render_textrect(self.message, MID_FONT, rect, colors['white'], colors['orange'], 0)
        except TextRectException:
            try:
                text = render_textrect(self.message, SMALL_FONT, rect, colors['white'], colors['orange'], 0)
            except TextRectException:
                text = render_textrect("Message is too long to be displayed.",
                                       MID_FONT, rect, colors['white'], colors['orange'], 0)
        while message_loop:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    quit(0)
                if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                    message_loop = False
            game.screen.blit(text, rect.topleft)
            pygame.display.flip()
            clock.tick(CLOCK_TICK)


class Portal(GameObject):
    def __init__(self, x, y, destination_x, destination_y, miscellaneous=None):
        super().__init__(x, y, miscellaneous)
        self.destination_x = destination_x
        self.destination_y = destination_y
        self.sprite_paths_list = [
            join('objects', 'portal_1.png'),
            join('objects', 'portal_2.png'),
        ]
        self.portal_blocked_sprite_path = join('objects', 'portal_blocked.png')
        self.alert_sprite_path = join('objects', 'alert.png')
        self.sprite_number = 0
        self.animation_time = 0
        self.max_animation_time = 60
        self.display_alert = 0

    def on_touch(self, game, _):
        if (game.tile_is_free(self.destination_x, self.destination_y, self.layer) and
                game.tiles_map[self.destination_y][self.destination_x] != '#'):
            game.player.x = self.destination_x
            game.player.y = self.destination_y
            game.player.after_step(game)
            game.reset_arrow_keys()
        else:
            self.display_alert = 1

    def update(self, game):
        if self.display_alert == 0:
            self.sprite_path = self.sprite_paths_list[self.sprite_number]
            self.animation_time += 1
            if self.animation_time == self.max_animation_time:
                self.animation_time = 0
                self.sprite_number += 1
                if self.sprite_number == len(self.sprite_paths_list):
                    self.sprite_number = 0
        else:
            self.sprite_path = self.portal_blocked_sprite_path

    def render(self, game):
        super().render(game)
        if self.display_alert == self.max_animation_time:
            self.display_alert = 0
        if self.display_alert > 0:
            self.display_alert += 1
            x = PLAYER_X + (self.destination_x - game.player.x) * TILE_SIZE - game.player.in_move_delta_x
            y = PLAYER_Y + (self.destination_y - game.player.y) * TILE_SIZE - game.player.in_move_delta_y
            if in_render_range(x, y):
                game.foreground.append((x, y, self.alert_sprite_path))


class Cannonball(MovingObject):
    def __init__(self, x, y, direction, speed, miscellaneous=None):
        super().__init__(x, y, speed, miscellaneous)
        self.in_move = direction
        self.sprite_path = join('objects', 'cannonball.png')

    def update(self, game):
        if self.in_move == 'up':
            self.in_move_delta_y -= self.step_size
            if -self.in_move_delta_y >= TILE_SIZE:
                game.objects[self.layer].pop((self.x, self.y))
                self.y -= 1
                self.in_move_delta_y = 0
                self.after_step(game)
        if self.in_move == 'down':
            self.in_move_delta_y += self.step_size
            if self.in_move_delta_y >= TILE_SIZE:
                game.objects[self.layer].pop((self.x, self.y))
                self.y += 1
                self.in_move_delta_y = 0
                self.after_step(game)
        if self.in_move == 'left':
            self.in_move_delta_x -= self.step_size
            if -self.in_move_delta_x >= TILE_SIZE:
                game.objects[self.layer].pop((self.x, self.y))
                self.x -= 1
                self.in_move_delta_x = 0
                self.after_step(game)
        if self.in_move == 'right':
            self.in_move_delta_x += self.step_size
            if self.in_move_delta_x >= TILE_SIZE:
                game.objects[self.layer].pop((self.x, self.y))
                self.x += 1
                self.in_move_delta_x = 0
                self.after_step(game)

    def after_step(self, game):
        if (game.player.x, game.player.y) == (self.x, self.y):
            game.player.on_hit(game, opposite_direction(self.in_move))
        collide = game.objects[self.layer].get((self.x, self.y))
        if collide is not None and isinstance(collide, MockupObject):
            collide = collide.owner
        if collide is not None:
            collide.on_hit(game, opposite_direction(self.in_move))
            return
        if game.tiles_map[self.y][self.x] == '#':
            return
        game.objects[self.layer][(self.x, self.y)] = self


class Cannon(GameObject):
    def __init__(self, x, y, direction, shooting_delay_function, bullet_speed_function, miscellaneous=None):
        super().__init__(x, y, miscellaneous)
        assert_direction(direction)
        self.shooting_direction = direction
        self.sprite_path = join('objects', 'cannon_' + direction + '.png')
        self.get_shooting_delay = shooting_delay_function
        self.get_bullet_speed = bullet_speed_function
        self.cannon_counter = 0
        self.delay = self.get_shooting_delay(0)

    def update(self, game):
        if self.delay == 0:
            pos = position_after_moving(self.x, self.y, self.shooting_direction)
            if (game.player.x, game.player.y) == pos:
                game.player.on_hit(game, opposite_direction(self.shooting_direction))
                return
            if game.tiles_map[pos[1]][pos[0]] != '#':
                collide = game.objects[self.layer].get(pos)
                if collide is not None and isinstance(collide, MockupObject):
                    collide = collide.owner
                if collide is not None:
                    collide.on_hit(game, opposite_direction(self.shooting_direction))
                else:
                    game.register_object(Cannonball(pos[0], pos[1], self.shooting_direction,
                                                    self.get_bullet_speed(self.cannon_counter)))
            self.cannon_counter += 1
            self.delay = self.get_shooting_delay(self.cannon_counter)
        else:
            self.delay -= 1


class Door(GameObject):
    def __init__(self, x, y, container, miscellaneous=None):
        super().__init__(x, y, miscellaneous)
        self.container = container
        self.condition_on_update = self.container.get('condition_on_update')
        self.condition_on_touch = self.container.get('condition_on_touch')
        self.sprite_path = join('objects', 'door_locked.png')

    def update(self, game):
        if self.condition_on_update is not None and self.condition_on_update(game, self.container):
            game.objects[self.layer].pop((self.x, self.y))

    def on_touch(self, game, direction):
        if self.condition_on_touch is not None and self.condition_on_update(game, direction, self.container):
            game.objects[self.layer].pop((self.x, self.y))


class LittleDevil(MovingObject):
    def __init__(self, x, y, speed, health=0, miscellaneous=None):
        super().__init__(x, y, speed, miscellaneous)
        self.sprite_path = join('objects', 'little_devil.png')
        self.health = health
        self.mockup = None

    def __verify_direction(self, game, direction):
        if direction is False:
            return
        pos = position_after_moving(self.x, self.y, direction)
        if game.tiles_map[pos[1]][pos[0]] == '#':
            direction = False
        elif pos in game.objects[self.layer]:
                direction = False
        if direction is not False:
            self.in_move = direction
            self.mockup = MockupObject(pos[0], pos[1], game, self)

    def update(self, game):
        if not self.in_move:
            distance_x = game.player.x - self.x
            distance_y = game.player.y - self.y
            if distance_y < 0:
                in_move_y = 'up'
            elif distance_y > 0:
                in_move_y = 'down'
            else:
                in_move_y = False
            if distance_x < 0:
                in_move_x = 'left'
            elif distance_x > 0:
                in_move_x = 'right'
            else:
                in_move_x = False
            # Cover larger distance first
            if abs(distance_x) < abs(distance_y):
                in_move_first_direction = in_move_y
                in_move_second_direction = in_move_x
            else:
                in_move_first_direction = in_move_x
                in_move_second_direction = in_move_y
            # Little devil has chosen potential directions of move, but we still need to check whether he can move there
            self.__verify_direction(game, in_move_first_direction)
            if not self.in_move:
                self.__verify_direction(game, in_move_second_direction)
        # Now little devil has chosen direction of move (could be False) and will move
        super().update(game)

    def after_step(self, game):
        self.mockup = None
        if (game.player.x, game.player.y) == (self.x, self.y):
            game.player.on_hit(game, opposite_direction(self.in_move))
        else:
            self.in_move = False

    def on_hit(self, game, _):
        if self.health > 0:
            self.health -= 1
            if self.health <= 0:
                game.objects[self.layer].pop((self.x, self.y))
                if self.mockup is not None:
                    self.mockup.destroy()
                    self.mockup = None


class Ghost(MovingObject):
    def __init__(self, x, y, speed, path, miscellaneous=None):
        super().__init__(x, y, speed, miscellaneous)
        self.moving_path = path
        self.moving_path.insert(0, (x, y))
        self.sprite_path = join('objects', 'ghost.png')
        self.target_place_index = 0
        self.layer = 2  # This is ghost.

    def update(self, game):
        if not self.in_move:
            self.target_place_index = (self.target_place_index + 1) % len(self.moving_path)
            if self.x > self.moving_path[self.target_place_index][0]:
                self.in_move = 'left'
            elif self.x < self.moving_path[self.target_place_index][0]:
                self.in_move = 'right'
            if self.y > self.moving_path[self.target_place_index][1]:
                self.in_move = 'up'
            elif self.y < self.moving_path[self.target_place_index][1]:
                self.in_move = 'down'
        super().update(game)

    def after_step(self, game):
        collide = game.objects[DEFAULT_LAYER].get((self.x, self.y))  # Player layer
        if collide is not None and isinstance(collide, MockupObject):
            collide = collide.owner
        if (game.player.x, game.player.y) == (self.x, self.y) or isinstance(collide, Player):
            game.player.on_hit(game, opposite_direction(self.in_move))
        else:
            if (self.x, self.y) == self.moving_path[self.target_place_index]:
                self.in_move = False


class HellEntrance(GameObject):
    def __init__(self, x, y, frequency, speed, health=1, miscellaneous=None):
        super().__init__(x, y, miscellaneous)
        self.sprite_path = join('objects', 'hell_entrance.png')
        self.frequency = frequency
        self.speed = speed
        self.health = health
        self.frame_counter = 0
        self.layer = 0

    def update(self, game):
        if self.frame_counter > 0:
            self.frame_counter -= 1
        if self.frame_counter == 0:
            if (game.player.x, game.player.y) == (self.x, self.y):
                game.player.on_hit(game, game.player.direction_facing)
                return
            collide = game.objects[DEFAULT_LAYER].get((self.x, self.y))
            if collide is not None and isinstance(collide, MockupObject):
                collide = collide.owner
            if collide is not None:
                if isinstance(collide, Player):
                    game.player.on_hit(game, self, game.player.direction_facing)
                return
            game.register_object(LittleDevil(self.x, self.y, self.speed, self.health))
            self.frame_counter = self.frequency
