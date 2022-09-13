from khaos_map import KhaosMap
from render import RenderQ

import pygame
import sys


class PyGameWindow:
    """The window that renders the map out for visualization"""
    def __init__(self, k_map):
        self.map = k_map
        self.settings = self.map.settings

        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(self.settings.screen_size)
        pygame.display.set_caption("Khaos Map Generator")

        # Create controls and clock
        self.controls = KeyStrokes(self.settings)
        self.clock = pygame.time.Clock()

        # Create the RenderQs
        self.cellQ = RenderQ(self.screen, self.settings, 'cell')
        self.atmosphereQ = RenderQ(self.screen, self.settings, 'atmosphere')
        self.vertexQ = RenderQ(self.screen, self.settings, 'vertex')

        # Add the elements from the map to them
        for each_cell in self.map.cells:
            self.cellQ.add(each_cell)
            self.atmosphereQ.add(each_cell)

        for each_vertex in self.map.vertices:
            self.vertexQ.add(each_vertex)

    def main_loop(self):
        """Main loop that calls all the update functions for the subsidiary objects"""
        while not self.controls.ctrl_bools['exit']:
            # Update controls and tick the clock to cap the framerate
            self.controls.update()
            self.clock.tick(self.settings.framerate)

            # Update wind
            self.map.update_atmosphere()

            # Update the renderQs
            self.cellQ.update()
            self.vertexQ.update()
            self.atmosphereQ.update()

            # Flip the screen
            pygame.display.flip()


class KeyStrokes:
    """Manages input from the keyboard."""
    def __init__(self, settings):
        self.settings = settings

        self.controls = {'exit': [pygame.K_ESCAPE],
                         'confirm': [pygame.K_SPACE, pygame.K_RETURN],
                         }

        self.ctrl_bools = {'exit': False,
                           'confirm': False,
                           }

    def update(self):
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in self.controls['exit']:
                    self.ctrl_bools['exit'] = True
                elif event.key in self.controls['confirm']:
                    self.ctrl_bools['confirm'] = True

            elif event.type == pygame.KEYUP:
                if event.key in self.controls['exit']:
                    self.ctrl_bools['exit'] = False
                elif event.key in self.controls['confirm']:
                    self.ctrl_bools['confirm'] = False


if __name__ == "__main__":
    # Create or load a map
    khaos_map = KhaosMap()

    # Initialize window
    window = PyGameWindow(khaos_map)

    if not khaos_map.settings.do_render_vertices:
        window.vertexQ.disable = True

    if not khaos_map.settings.do_render_atmosphere:
        window.atmosphereQ.disable = True

    # Run the renderer window
    window.main_loop()
