# - libraries -
import pygame
from pytmx.util_pygame import load_pygame  # allows use of tiled tile map files for pygame use
# - general -
from game_data import tile_size, controller_map, fonts
from support import *
from boids import Flock
# - systems -
from camera import Camera
from text import Font


class Level:
    def __init__(self, level_data, screen_surface, screen_rect, controllers, starting_spawn):
        # TODO testing, remove
        self.dev_debug = False

        # level setup
        self.screen_surface = screen_surface  # main screen surface
        self.screen_rect = screen_rect
        self.screen_width = screen_surface.get_width()
        self.screen_height = screen_surface.get_height()

        self.controllers = controllers

        self.starting_spawn = starting_spawn
        self.player_spawn = None  # begins as no spawn as filled when player is initialised

        self.pause = False
        self.pause_pressed = False

        dt = 1  # dt starts as 1 because on the first frame we can assume it is 60fps. dt = 1/60 * 60 = 1

        # - text setup -
        self.small_font = Font(resource_path(fonts['small_font']), 'white')
        self.large_font = Font(resource_path(fonts['large_font']), 'white')

        # flock
        flock_size = 100
        flocks = 3
        self.flocks = [Flock(self.screen_surface, flock_size) for i in range(flocks)]

# -- check methods --

    def get_input(self):
        keys = pygame.key.get_pressed()

        # pause pressed prevents holding key and rapidly switching between T and F
        if keys[pygame.K_p]:
            if not self.pause_pressed:
                self.pause = not self.pause
            self.pause_pressed = True
        # if not pressed
        else:
            self.pause_pressed = False


        # TODO testing, remove
        if keys[pygame.K_z] and keys[pygame.K_LSHIFT]:
            self.dev_debug = False
        elif keys[pygame.K_z]:
            self.dev_debug = True

# -- menus --

    def pause_menu(self):
        pause_surf = pygame.Surface((self.screen_surface.get_width(), self.screen_surface.get_height()))
        pause_surf.fill((40, 40, 40))
        self.screen_surface.blit(pause_surf, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
        width = self.large_font.width('PAUSED')
        self.large_font.render('PAUSED', self.screen_surface, (center_object_x(width, self.screen_surface), 20))

# -------------------------------------------------------------------------------- #

    # updates the level allowing tile scroll and displaying tiles to screen
    # order is equivalent of layers
    def update(self, dt):
        # #### INPUT > GAME(checks THEN UPDATE) > RENDER ####
        # checks deal with previous frames interactions. Update creates interactions for this frame which is then diplayed
        '''player = self.player.sprite'''

        # -- INPUT --
        self.get_input()

        # -- CHECKS (For the previous frame)  --
        if not self.pause:

        # -- UPDATES -- player needs to be before tiles for scroll to function properly
            for f in self.flocks:
                f.update()

        # -- RENDER --
        # Draw
        for f in self.flocks:
            f.draw()

        # must be after other renders to ensure menu is drawn last
        if self.pause:
            self.pause_menu()

        # Dev Tools
        if self.dev_debug:
            '''put debug tools here'''
            pygame.draw.line(self.screen_surface, 'red', (0, 0), (15, 15), 1)
