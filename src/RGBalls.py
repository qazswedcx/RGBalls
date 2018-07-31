import pickle
import pygame
import re
from os.path import join
from os import listdir

from game import Game
from const import SCREEN_Y_SIZE, SCREEN_X_SIZE, GAME_TITLE, CLOCK_TICK,\
    BIG_FONT, MID_FONT, STAR_SIZE, SMALL_FONT, colors
from images import get_image
from levels import generate_levels


class GameMenu:
    def __init__(self):
        generate_levels()
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_X_SIZE, SCREEN_Y_SIZE))
        pygame.display.set_caption(GAME_TITLE)
        self.icon = get_image(join('menu', 'logo-small.png'))
        pygame.display.set_icon(self.icon)
        self.clock = pygame.time.Clock()
        path = join('..', 'save')
        try:
            with open(path, 'rb') as file:
                self.level_results = pickle.load(file)
        except IOError:
            self.level_results = []
        self.level_selected = self.level_unlocked = len(self.level_results)
        pattern = re.compile('^\d{4}\.level$')  # '4 digits'.level
        self.total_levels = len([f for f in listdir(join('..', 'levels')) if pattern.match(f)])
        if self.total_levels == self.level_selected:  # All levels beaten
            self.level_selected -= 1
        self.entrance()
        self.main_loop()

    def entrance(self):
        self.screen.fill(colors['orange'])
        white = colors['white']
        x = SCREEN_X_SIZE / 2
        logo = get_image(join('menu', 'logo-big.png'))
        logo.convert_alpha()
        rect = logo.get_rect()
        rect.center = (x, 210)
        self.screen.blit(logo, rect)
        text = MID_FONT.render("Press Enter to continue", True, white)
        rect = text.get_rect(center=(x, SCREEN_Y_SIZE - 50))
        self.screen.blit(text, rect)
        pygame.display.flip()
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        quit()
                    if event.key == pygame.K_RETURN:
                        return
            self.clock.tick(CLOCK_TICK)

    def save(self):
        path = join('..', 'save')
        with open(path, 'wb') as file:
            pickle.dump(self.level_results, file)

    def play_game(self):
        game = Game(self.level_selected)  # Play level and get result
        result = game.win_stars
        if result[0] == '*':
            if len(self.level_results) > self.level_selected:
                # This wasn't the first time player has won this level
                if self.level_results[self.level_selected] == ['*', '_', '_'] or result == ['*', '*', '*']:
                    # If player collected two stars already, he can improve his score
                    # only by collecting all three stars.
                    self.level_results[self.level_selected] = result
                    self.save()
            else:
                self.level_unlocked += 1
                self.level_results.append(result)
                self.save()
            return self.summary(result[1], result[2], game.level.steps)
        elif result[0] == 'retry':
            return 'retry'
        elif result[0] == 'lose':
            return self.lose()
        else:
            if result[0] == 'level not found':  # This should happen only when player chooses option
                self.level_selected -= 1        # 'Next level' after winning last level
            return 'menu'

    def summary(self, diamonds_star, steps_star, steps_amount):
        star_image = get_image(join('menu', 'star.png'))
        no_star_image = get_image(join('menu', 'no-star.png'))
        self.screen.fill(colors['blue'])
        x = SCREEN_X_SIZE / 2
        white = colors['white']
        text = MID_FONT.render("Congratulations!", True, white)
        rect = text.get_rect(center=(x, 30))
        self.screen.blit(text, rect)
        y = SCREEN_Y_SIZE / 5
        stars_x = 40
        text_x = 90
        text_y_delta = -5
        font_y_size = 45
        self.screen.blit(star_image, (stars_x, y))
        text = MID_FONT.render("Push all balls into pads", True, white)
        self.screen.blit(text, (text_x, y + text_y_delta))
        y += font_y_size
        if diamonds_star == '*':
            self.screen.blit(star_image, (stars_x, y))
        else:
            self.screen.blit(no_star_image, (stars_x, y))
        text = MID_FONT.render("Collect all diamonds", True, white)
        self.screen.blit(text, (text_x, y + text_y_delta))
        y += font_y_size
        if steps_star == '*':
            self.screen.blit(star_image, (stars_x, y))
        else:
            self.screen.blit(no_star_image, (stars_x, y))
        text = MID_FONT.render("Finish in " + str(steps_amount) + " steps", True, white)
        self.screen.blit(text, (text_x, y + text_y_delta))
        x = SCREEN_X_SIZE / 4
        y = 3 * SCREEN_Y_SIZE / 4
        text = SMALL_FONT.render("Q: go to main menu", True, white)
        rect = text.get_rect(center=(x, y))
        self.screen.blit(text, rect)
        button = get_image(join('menu', 'go_to_menu.png'))
        rect = button.get_rect()
        rect.centerx, rect.centery = x, y + font_y_size
        self.screen.blit(button, rect)
        x += SCREEN_X_SIZE / 4
        text = SMALL_FONT.render("R: retry level", True, white)
        rect = text.get_rect(center=(x, y))
        self.screen.blit(text, rect)
        button = get_image(join('menu', 'retry_level.png'))
        rect = button.get_rect()
        rect.centerx, rect.centery = x, y + font_y_size
        self.screen.blit(button, rect)
        x += SCREEN_X_SIZE / 4
        text = SMALL_FONT.render("Enter: play next level", True, white)
        rect = text.get_rect(center=(x, y))
        self.screen.blit(text, rect)
        button = get_image(join('menu', 'next_level.png'))
        rect = button.get_rect()
        rect.centerx, rect.centery = x, y + font_y_size
        self.screen.blit(button, rect)

        pygame.display.flip()
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        return 'menu'
                    if event.key == pygame.K_r:
                        return 'retry'
                    if event.key == pygame.K_RETURN:
                        return 'next'
            self.clock.tick(CLOCK_TICK)

    def lose(self):
        font_y_size = 45
        self.screen.fill(colors['purple'])
        x = SCREEN_X_SIZE / 2
        white = colors['white']
        text = MID_FONT.render("You died!", True, white)
        rect = text.get_rect(center=(x, 30))
        self.screen.blit(text, rect)
        x = SCREEN_X_SIZE / 3
        y = 3 * SCREEN_Y_SIZE / 4
        text = SMALL_FONT.render("Q: go to main menu", True, white)
        rect = text.get_rect(center=(x, y))
        self.screen.blit(text, rect)
        button = get_image(join('menu', 'go_to_menu.png'))
        rect = button.get_rect()
        rect.centerx, rect.centery = x, y + font_y_size
        self.screen.blit(button, rect)
        x += SCREEN_X_SIZE / 3
        text = SMALL_FONT.render("R: retry level", True, white)
        rect = text.get_rect(center=(x, y))
        self.screen.blit(text, rect)
        button = get_image(join('menu', 'retry_level.png'))
        rect = button.get_rect()
        rect.centerx, rect.centery = x, y + font_y_size
        self.screen.blit(button, rect)
        pygame.display.flip()
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        return 'menu'
                    if event.key == pygame.K_r:
                        return 'retry'
            self.clock.tick(CLOCK_TICK)

    def main_loop(self):
        background = get_image(join('menu', 'landscape.png'))
        background = pygame.transform.scale(background, (SCREEN_X_SIZE, SCREEN_Y_SIZE))
        # Unlocked levels are 0, 1, ..., level_unlocked
        # Last level has number total_levels - 1
        while True:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    quit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                        quit()
                    if event.key == pygame.K_LEFT or event.key == pygame.K_DOWN:
                        if self.level_selected > 0:
                            self.level_selected -= 1
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_UP:
                        if self.level_selected < self.level_unlocked and self.level_selected < self.total_levels - 1:
                            self.level_selected += 1
                    if event.key == pygame.K_PAGEUP:
                        self.level_selected = min(self.level_selected + 5, self.level_unlocked, self.total_levels - 1)
                    if event.key == pygame.K_PAGEDOWN:
                        self.level_selected = max(self.level_selected - 5, 0)
                    if event.key == pygame.K_RETURN:
                        while True:
                            # This loop is here only to prevent RuntimeError: maximum recursion depth exceeded,
                            # since Python doesn't support tail recursion optimization.
                            action = self.play_game()
                            if action == 'menu':
                                break
                            elif action == 'next':
                                self.level_selected += 1
            self.screen.blit(background, (0, 0))
            text = BIG_FONT.render(str(self.level_selected + 1), True, colors['black'])
            rect = text.get_rect(center=(SCREEN_X_SIZE / 2, SCREEN_Y_SIZE / 4))
            self.screen.blit(text, rect)
            try:
                level_stars = self.level_results[self.level_selected]
            except IndexError:
                level_stars = ['_', '_', '_']
            star_image = get_image(join('menu', 'star.png'))
            no_star_image = get_image(join('menu', 'no-star.png'))
            for i in range(3):
                if level_stars[i] == '*':
                    self.screen.blit(star_image, (SCREEN_X_SIZE / 2 + (i - 3 / 2) * STAR_SIZE, SCREEN_Y_SIZE / 2))
                else:
                    self.screen.blit(no_star_image, (SCREEN_X_SIZE / 2 + (i - 3 / 2) * STAR_SIZE, SCREEN_Y_SIZE / 2))
            pygame.display.flip()
            self.clock.tick(CLOCK_TICK)


if __name__ == "__main__":
    GameMenu()
