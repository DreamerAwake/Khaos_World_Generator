from khaos_map import KhaosMap
import render
from my_pygame_functions import is_point_in_polygon, TextBox

import pygame
import sys


class PyGameWindow:
    """The window that renders the map out for visualization"""
    def __init__(self, k_map):
        self.map = k_map
        self.settings = self.map.settings

        # Initialize Pygame
        pygame.init()
        self.screen = pygame.display.set_mode(self.settings.window_size)
        pygame.display.set_caption("Khaos Map Generator")

        # Create controls and clock
        self.controls = KeyStrokes(self.settings)
        self.clock = pygame.time.Clock()

        # Create the RenderQs
        self.cellQ = render.RenderQ(self.screen, self.settings, 'cell')
        self.atmosphereQ = render.RenderQ(self.screen, self.settings, 'atmosphere')
        self.vertexQ = render.RenderQ(self.screen, self.settings, 'vertex')

        # Add the elements from the map to the RenderQs
        for each_cell in self.map.cells:
            self.cellQ.add(each_cell)
            self.atmosphereQ.add(each_cell)

        for each_vertex in self.map.vertices:
            self.vertexQ.add(each_vertex)

        # Create the gui, including the GUI RenderQ
        self.guiQ, self.controls.buttons = self.build_gui()

    def main_loop(self):
        """Main loop that calls all the update functions for the subsidiary objects"""
        while not self.controls.ctrl_bools['exit']:

            # Update controls and tick the clock to cap the framerate
            self.controls.update()
            self.controls.update_mouse(self.map, self.guiQ)
            self.clock.tick(self.settings.framerate)

            # Update bools set by buttons
            if khaos_map.settings.do_render_vertices:
                window.vertexQ.disable = False
            else:
                window.vertexQ.disable = True

            if khaos_map.settings.do_render_atmosphere:
                window.atmosphereQ.disable = False
            else:
                window.atmosphereQ.disable = True

            # Update wind
            for iteration in range(0, self.settings.atmo_iterations_per_frame):
                self.map.update_atmosphere()

            # Update the map's text box
            self.map.update_textbox()

            # Update the renderQs
            self.cellQ.update()
            self.vertexQ.update()
            self.atmosphereQ.update()
            self.guiQ.update()

            # Flip the screen
            pygame.display.flip()

    def build_gui(self):
        """Creates all the gui objects and puts them in a shared RenderQ."""
        guiQ = render.RenderQ(self.screen, self.settings, 'gui')
        buttons = {}

        # Create the text box on the side of the screen
        display_text = TextBox(self.settings)
        display_text.place_text_box((self.settings.screen_size[0], 0), 50, self.settings.text_box_width, 12)
        display_text.enable_bg((255, 255, 200))
        display_text.do_center_text = True
        self.map.display_text = display_text
        guiQ.add(display_text)

        # Add text above the toggles at the bottom of the screen
        atmo_textbox = TextBox(self.settings)
        atmo_textbox.place_text_box((self.settings.screen_size[0],
                                     self.settings.screen_size[1] - 200), 1, self.settings.text_box_width / 2)
        atmo_textbox.enable_bg((200, 200, 162))
        atmo_textbox.do_center_text = True
        atmo_textbox.write('Toggle Wind')
        guiQ.add(atmo_textbox)

        vertex_textbox = TextBox(self.settings)
        vertex_textbox.place_text_box((self.settings.screen_size[0] + (self.settings.text_box_width / 2),
                                       self.settings.screen_size[1] - 200), 1, self.settings.text_box_width / 2)
        vertex_textbox.enable_bg((200, 200, 162))
        vertex_textbox.do_center_text = True
        vertex_textbox.write('Toggle Altitudes')
        guiQ.add(vertex_textbox)

        # Add the season readout
        season_textbox = TextBox(self.settings)
        season_textbox.place_text_box((0, 0), 1, 200)
        season_textbox.enable_bg((200, 200, 162))
        season_textbox.write('Season')
        self.map.season_text = season_textbox
        guiQ.add(season_textbox)

        # Add the toggles at the bottom of the screen
        atmo_togglebox = render.RenderBox(pygame.Rect((0, 0), (50, 50)), (255, 200, 200))
        atmo_togglebox.rect.center = (self.settings.screen_size[0] + self.settings.text_box_width / 4,
                                      self.settings.screen_size[1] - 100)
        guiQ.add(atmo_togglebox)
        buttons[atmo_togglebox] = 'atmo_tb'

        vertex_togglebox = render.RenderBox(pygame.Rect((0, 0), (50, 50)), (255, 200, 200))
        vertex_togglebox.rect.center = (self.settings.screen_size[0] + self.settings.text_box_width * 3 / 4,
                                        self.settings.screen_size[1] - 100)
        guiQ.add(vertex_togglebox)
        buttons[vertex_togglebox] = 'vertex_tb'

        return guiQ, buttons


class KeyStrokes:
    """Manages input from the keyboard and mouse."""
    def __init__(self, settings):
        self.settings = settings

        self.controls = {'exit': [pygame.K_ESCAPE],
                         'confirm': [pygame.K_SPACE, pygame.K_RETURN],
                         }

        self.ctrl_bools = {'exit': False,
                           'confirm': False,
                           }

        self.last_click = None
        self.buttons = None

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

            elif event.type == pygame.MOUSEBUTTONUP:
                self.last_click = event.pos

    def update_mouse(self, k_map, guiQ):
        # Change the map's focus cell based on the .last_click in controls
        if self.last_click is not None:

            # If the click is on the gui, find if the click was on a button
            if self.last_click[0] > k_map.settings.screen_size[0]:
                for button in self.buttons.keys():
                    if button.is_point_in(self.last_click):
                        # Determine which button was clicked
                        if self.buttons[button] == 'atmo_tb':
                            khaos_map.settings.do_render_atmosphere = not khaos_map.settings.do_render_atmosphere
                            # Set the new button color
                            if khaos_map.settings.do_render_atmosphere:
                                button.color = (200, 255, 200)
                            else:
                                button.color = (255, 200, 200)
                        elif self.buttons[button] == 'vertex_tb':
                            khaos_map.settings.do_render_vertices = not khaos_map.settings.do_render_vertices
                            # Set the new button color
                            if khaos_map.settings.do_render_vertices:
                                button.color = (200, 255, 200)
                            else:
                                button.color = (255, 200, 200)

                # Set last click to None again
                self.last_click = None

            # If the click is not on the gui, look for a cell
            else:
                for each_cell in k_map.cells:
                    if is_point_in_polygon(self.last_click, each_cell.polygon):
                        # When you find the polygon, empty out the last_click and set the focus cell
                        self.last_click = None
                        # Remove the old focus cell
                        if k_map.focus_cell:
                            guiQ.remove(k_map.focus_cell)
                            k_map.focus_cell.is_focus = False
                        # Add the new focus cell
                        k_map.focus_cell = each_cell
                        guiQ.add(each_cell, True)
                        k_map.focus_cell.is_focus = True
                        break


if __name__ == "__main__":
    # Create or load a map
    khaos_map = KhaosMap()

    # Initialize window
    window = PyGameWindow(khaos_map)

    # Run the renderer window
    window.main_loop()
