import pygame
import math
from render import Renderable


class TextBox(Renderable):
    def __init__(self, settings):
        """This class draws a text box with updateable text."""
        super().__init__()
        self.settings = settings
        self.do_center_text = False

        self.number_of_lines = 0
        self.width = 0
        self.letter_size = self.settings.font_body.size('M')
        self.line_spacing = 0
        self.rect = None

        self.font = self.settings.font_body
        self.color = (0, 0, 0)
        self.bg_color = None

        self.current_text = ''
        self.current_text_list = []

    def enable_bg(self, color):
        """Causes the texbox to render a background box in the chosen color."""
        self.bg_color = color

    def set_font(self, font_type):
        """Sets the font by appealing to the settings file."""
        if font_type == 'body':
            self.font = self.settings.font_body
        elif font_type == 'title':
            self.font = self.settings.font_title

    def place_text_box(self, location, number_of_lines, width, line_spacing=0):
        """Places the text box at the specified location. The text box cannot be rendered until
        this has been run at least once."""
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
            self.write(f"{self.current_text} * {text}")

    def write(self, text):
        """Used to write text to the text box. The * escape character is used as a line break."""
        self.current_text = text
        words = text.split()
        lines = []
        lines_complete = 0
        this_line = []

        # Start looping through each word in the complete list of words
        while len(words) > 0 and lines_complete < self.number_of_lines:

            # If the next word is the line break character make the linebreak
            if words[0] == '*':
                # Delete the character
                del words[0]
                # Increment your lines, add this_line to lines
                lines_complete += 1
                this_line.append(' ')
                line = ' '.join(this_line)
                lines.append(line)
                this_line = []
                continue
            else:

                this_line.append(words.pop(0))

                # If the size would overrun the allowed width when adding the next word, end the line and go to the next
                size = self.font.size(f'{" ".join(this_line + words[:1])}')
                if size[0] > self.width:
                    lines_complete += 1
                    line = ' '.join(this_line)
                    lines.append(line)
                    this_line = []

        lines_complete += 1
        line = ' '.join(this_line)
        lines.append(line)
        self.current_text_list = lines

    def update(self, renderer):
        # Draw background
        if self.bg_color is not None:
            pygame.draw.rect(renderer.screen, self.bg_color, self.rect, self.rect.width)

        # Draw text
        line_offset = 0
        for line in self.current_text_list:

            font_surface = self.font.render(line, False, self.color)
            if self.do_center_text:
                renderer.screen.blit(font_surface, (self.rect.left + (self.rect.width / 2) -
                                                    (self.font.size(line)[0] / 2), self.rect.top + line_offset))
            else:
                renderer.screen.blit(font_surface, (self.rect.left, self.rect.top + line_offset))
            line_offset += self.letter_size[1] + self.line_spacing


def load_scaled_img(game, filespace_string):
    """This function bypasses the need to use the lengthy pygame call pygame.transform.scale(pygame.image.load(X)).
    Given a string representing a key in the game.settings.filespace, this function loads the associated image scaled
    to the correct render size for the current window.
    Returns the default image if the image cannot be found in the filespace. Otherwise returns the scaled image."""
    if filespace_string not in game.settings.filespace.keys():
        print(f"Failed to load img from filespace '{filespace_string}'")
        img = pygame.image.load(game.settings.filespace['DEFAULT'])
    else:
        img = pygame.image.load(game.settings.filespace[filespace_string])
    img_size = img.get_size()
    img_scaled = pygame.transform.scale(img, (img_size[0] * game.settings.render_scale,
                                              img_size[1] * game.settings.render_scale))
    print(f"loaded '{filespace_string}' from filespace")
    return img_scaled


def load_each_from_sheet(game, sheet_filespace, tile_size, last_index, is_alpha=False):
    img_list = []
    if sheet_filespace not in game.settings.filespace.keys():
        print(f"Failed to load sprite sheet from filespace '{sheet_filespace}.'")
        img = pygame.image.load(game.settings.filespace['DEFAULT'])
        img_size = img.get_size()
        img_scaled = pygame.transform.scale(img, (img_size[0] * game.settings.render_scale,
                                                  img_size[1] * game.settings.render_scale))
        img_list.append(img_scaled)
    else:
        tile_rect = pygame.Rect((0, 0), tile_size)
        img_size = tile_rect.size
        sheet = pygame.image.load(game.settings.filespace[sheet_filespace])
        img = pygame.Surface(tile_size).convert()
        indices_per_row = math.floor(sheet.get_width() / tile_rect.width)
        for sprite_index in range(0, last_index+1):
            if sprite_index % indices_per_row == 0 and sprite_index != 0:
                tile_rect.left = 0
                tile_rect.top = tile_size[1] * (sprite_index / indices_per_row)
            else:
                tile_rect.left = tile_size[0] * (sprite_index % indices_per_row)
            cropped_img = img.copy()
            cropped_img.blit(sheet, (0, 0), tile_rect)

            img_scaled = pygame.transform.scale(cropped_img, (img_size[0] * game.settings.render_scale,
                                                              img_size[1] * game.settings.render_scale))
            if is_alpha:
                img_scaled.set_colorkey(game.settings.colorspace['alpha'], pygame.RLEACCEL)
            img_list.append(img_scaled)

    return img_list


def is_point_in_polygon(point, polygon):
    """Given a point (a tuple of int, int) and a polygon (an iterable of (int, int)s), determines if the point falls
    within the polygon. Returns True if the point is in the polygon, False otherwise."""
    collides = False

    for iteration in range(0, len(polygon)):
        poly_edge_1 = polygon[iteration - 1]
        poly_edge_2 = polygon[iteration]

        # Check if the point is placed between the poly_edge points vertically
        edge_bool_1 = poly_edge_1[1] > point[1]
        edge_bool_2 = poly_edge_2[1] > point[1]
        if edge_bool_1 != edge_bool_2:
            # Check if at least one of the poly_edges is to the left of the point
            if poly_edge_1[0] < point[0] or poly_edge_2[0] < point[0]:
                # if so invert collides
                collides = not collides

    # If collides has toggled an odd number of times it is True now,
    # It has crossed an odd number of poly_edges, meaning it is inside the shape
    return collides
