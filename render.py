import pygame.draw

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

    def update(self):
        """Calls update on each element in the queue as long as this Q is enabled."""
        if not self.disable:
            for each_renderable in self.queue:
                try:
                    each_renderable.update(self)
                except TypeError:
                    each_renderable.update()

            # Apply AA
            if self.AA:
                aa = pygame.transform.smoothscale(self.screen, self.settings.window_size)
                self.aa_screen.blit(aa, (0, 0))

    def enable_AA(self, aa_screen):
        """Enable antialiasing for this renderQ. The given screen becomes the final rendering target.."""
        self.AA = True
        self.aa_screen = aa_screen

    def move_to_top(self, renderable):
        """Finds the given object in the Q and moves it to the end of the list, causing it to render on top.
        Returns True if the object was moved successfully, and False if it was not found in the list."""
        if self.remove(renderable):
            self.add(renderable)
            return True
        else:
            return False

    def add(self, *renderables, place_on_bottom=False, place_at=0):
        """Adds each renderable object passed to the RenderQ"""
        for renderable in renderables:
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
    """Given a rect, and a color or an image, renders a box of the color or an image in that rect at that location when
    added to a RenderQ. Used as a parent for all Button type objects."""
    def __init__(self, rect, color=None, img=None):
        super().__init__()

        self.rect = rect
        self.color = color
        self.img = img
        self.outline_width = 0

    def update(self, renderer):
        if self.img:
            renderer.screen.blit(self.img, self.rect)
        elif self.color:
            pygame.draw.rect(renderer.screen, self.color, self.rect, self.outline_width)

    def is_point_in(self, point):
        """An alias for this object's rect's .collidepoint to determine if the given point is in the rect."""
        return self.rect.collidepoint(point)

    def on_click(self):
        """The code that runs when this is clicked, used for button functionality."""
        pass

    def on_hover(self):
        """The code that runs when this is hovered over with the mouse. Runs once each frame that the mouse remains over
         the button."""
        pass


