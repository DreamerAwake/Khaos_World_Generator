import pygame.draw
from scipy import ndimage

class RenderQ:
    """This class contains and manages a list of Renderable objects, including their calls to .update(),
    simplifying the rendering pipline."""
    def __init__(self, surface, settings, label):
        self.screen = surface
        self.settings = settings

        self.label = label
        self.queue = []
        self.disable = False
        self.AA = False
        self.aa_screen = None

    def update(self, blit_to=None):
        """Calls update on each element in the queue as long as this Q is enabled."""
        if not self.disable:
            for each_renderable in self.queue:
                if type(each_renderable).__bases__[0] == Renderable:
                    each_renderable.update(self)
                else:
                    each_renderable.update()

            if blit_to:
                blit_to.blit(self.screen, (0, 0))

        # Apply AA
        if self.AA:
            aa = pygame.transform.smoothscale(self.screen, self.settings.window_size)
            self.aa_screen.blit(aa, (0, 0))

    def enable_AA(self, aa_screen):
        """Enable antialiasing for this renderQ. The given screen becomes the final rendering target.."""
        self.AA = True
        self.aa_screen = aa_screen

    def add(self, renderable, place_on_bottom=False, place_at=0):
        """Adds a renderable object to the RenderQ"""
        renderable: Renderable
        if renderable not in self.queue:
            if place_on_bottom:
                self.queue.insert(0, renderable)
            elif place_at != 0:
                self.queue.insert(place_at, renderable)
            else:
                self.queue.append(renderable)

    def remove(self, renderable):
        """Removes the given object from the queue. Will return True or False depending on whether the object was
        found in the first place."""
        if renderable in self.queue:
            self.queue.remove(renderable)
            return True
        else:
            return False


class Renderable:
    """The Superclass for my renderable objects, which allows me to call TypeErrors if I try to add the wrong
    object to a RenderQ. All Renderable sub-classes will have individually defined .update() functions."""
    def __init__(self):
        pass

    def update(self, renderer):
        """Renderable objects call update to write themselves to the screen."""
        pass


class RenderBox(Renderable):
    """Given a rect and a color, renders a box at that location when added to a RenderQ."""
    def __init__(self, rect, color):
        super().__init__()

        self.rect = rect
        self.color = color
        self.outline_width = 0

    def update(self, renderer):
        pygame.draw.rect(renderer.screen, self.color, self.rect, self.outline_width)

    def is_point_in(self, point):
        """An alias for this object's rect's .collidepoint to determine if the given point is in the rect."""
        return self.rect.collidepoint(point)
