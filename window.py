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
        self.guiQ = RenderQ(self.screen, self.settings, 'gui')

        # Add the elements from the map to them
        for each_cell in self.map.cells:
            self.cellQ.add(each_cell)
            self.atmosphereQ.add(each_cell)

        for each_vertex in self.map.vertices:
            self.vertexQ.add(each_vertex)

        # Add text box to the guiQ
        self.guiQ.add(k_map.display_text)


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
            self.guiQ.update()

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


class TextBox:
    def __init__(self, settings):
        """This class draws a text box with updateable text."""
        self.settings = settings

        self.number_of_lines = 0
        self.width = 0
        self.letter_size = self.settings.font_body.size('M')
        self.line_spacing = 0
        self.rect = None

        self.font = self.settings.font_body
        self.color = (0, 0, 0)

        self.current_text = ''
        self.current_text_list = []

    def set_font(self, font_type):
        if font_type == 'body':
            self.font = self.settings.font_body
        elif font_type == 'title':
            self.font = self.settings.font_title

    def place_text_box(self, location, number_of_lines, width, line_spacing=0):
        """Places the text box at the specified location."""
        self.number_of_lines = number_of_lines
        self.width = width
        self.rect = pygame.Rect(location, (self.width, self.letter_size[1] * number_of_lines))
        self.line_spacing = line_spacing

    def write_also(self, text, no_new_line=False):
        """Writes additional text after the current message, starting on a new line."""
        if no_new_line:
            self.write(f"{self.current_text} {text}")
        elif self.current_text == '':
            self.write(text)
        else:
            self.write(f"{self.current_text} N {text}")

    def write(self, text):
        self.current_text = text
        words = text.split()
        lines = []
        lines_complete = 0

        while len(words) > 0 and lines_complete < self.number_of_lines:
            this_line = []
            while len(words) > 0 and lines_complete < self.number_of_lines:
                this_line.append(words.pop(0))
                size = self.font.size(f'{" ".join(this_line + words[:1])}')
                if len(words) > 0 and words[0] == 'N':
                    del words[0]
                    lines_complete += 1
                    break
                elif size[0] > self.width:
                    lines_complete += 1
                    break

            line = ' '.join(this_line)
            lines.append(line)

        self.current_text_list = lines

    def update(self, renderer):
        line_offset = 0
        for line in self.current_text_list:

            font_surface = self.font.render(line, False, self.color)
            renderer.screen.blit(font_surface, (self.rect.left, self.rect.top + line_offset))
            line_offset += self.letter_size[1] + self.line_spacing


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
