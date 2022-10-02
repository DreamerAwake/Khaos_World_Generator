import sys

import pygame

import map_menu
import menus
import render
import settings_menu
import start_menu
from settings import Settings


class ApplicationWindow:
    """The wind in which the application is rendered and interacted with. Contains all of the user level interfaces."""
    def __init__(self):
        # Create the settings object
        self.settings = Settings()

        # Initialize Pygame
        pygame.init()
        self.display_screen = pygame.display.set_mode(self.settings.window_size)
        self.draw_screen = pygame.Surface(self.settings.render_size)
        pygame.display.set_caption("Khaos Map Generator")

        # Initialize controls and clock
        self.controls = Controls(self.settings)
        self.clock = pygame.time.Clock()

        # Create the master renderQ
        self.masterQ = render.RenderQ(self.draw_screen, self.settings, 'master')
        self.masterQ.enable_AA(self.display_screen)

        # Load the gui menus, add them to the master Q
        self.start_menu = start_menu.StartMenu(self)
        self.masterQ.add()

        self.settings_menu = settings_menu.SettingsMenu(self)
        self.settings_menu.q.disable = True

        self.map_menu = map_menu.MapMenu(self)
        self.map_menu.q.disable = True

        self.masterQ.add(self.settings_menu.q, self.start_menu.q, self.map_menu.q)

        # Start the start menu
        self.start_menu.loop()

    def update(self):
        """Main update loop for the window, makes the highest level rendering calls.
        Call this to end a frame."""
        self.controls.update()
        self.masterQ.update()
        pygame.display.flip()
        self.clock.tick()
        # print(self.clock.get_fps())


class Controls:
    """Controls all input from the keyboard and mouse."""
    def __init__(self, settings):
        self.settings = settings
        self.ctrls = {'exit': [pygame.K_ESCAPE],
                      'confirm': [pygame.K_SPACE, pygame.K_RETURN],
                      }

        self.ctrl_bools = {'exit': False,
                           'confirm': False,
                           }

        self.mouse_is_clicked = False
        self.mouse_pos = (0, 0)
        self.mouse_last_down = (0, 0)
        self.mouse_last_up = (0, 0)

    def get_input(self):
        """Fetches input from pygame"""
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                for control_key in self.ctrls.keys():
                    if event.key in self.ctrls[control_key]:
                        self.ctrl_bools[control_key] = True

            elif event.type == pygame.KEYUP:
                for control_key in self.ctrls.keys():
                    if event.key in self.ctrls[control_key]:
                        self.ctrl_bools[control_key] = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                # Adjust mouse position to the antialias render surface
                if self.settings.enableAA:
                    self.mouse_last_down = (event.pos[0] * 2, event.pos[1] * 2)
                else:
                    self.mouse_last_down = event.pos
                self.mouse_is_clicked = True

            elif event.type == pygame.MOUSEBUTTONUP:
                # Adjust mouse position to the antialias render surface
                if self.settings.enableAA:
                    self.mouse_last_up = (event.pos[0] * 2, event.pos[1] * 2)
                else:
                    self.mouse_last_up = event.pos
                self.mouse_is_clicked = False

            # Find the current mouse position
            self.get_mouse_position()

    def get_mouse_position(self):
        """Fetches the current mouse position."""
        if self.settings.enableAA:
            mouse_pos = pygame.mouse.get_pos()
            self.mouse_pos = (mouse_pos[0] * 2, mouse_pos[1] * 2)
        else:
            self.mouse_pos = pygame.mouse.get_pos()

    def update(self):
        self.get_input()
        self.get_mouse_position()


if __name__ == "__main__":
    app = ApplicationWindow()
