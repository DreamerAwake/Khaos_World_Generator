import pygame

import render
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
        self.controls = KeyStrokes(self.settings)
        self.clock = pygame.time.Clock()

        # Create the master renderQ
        self.masterQ = render.RenderQ(self.draw_screen, self.settings, 'master')

    def init_start_menu(self):
        """Initializes and places the elements of the start menu."""

        start_menu_Q = render.RenderQ(self.draw_screen, self.settings, 'start_menu')
