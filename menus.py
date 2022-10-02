import pygame

import my_pygame_functions
import render


class GUIMenu:
    """Parent for most menu screens."""
    def __init__(self, app_window):
        self.window = app_window
        self.q, self.buttons = self.init_menu_objs()

    def init_menu_objs(self):
        """Initializes and places the elements of the settings menu in the menu Q, so they can be rendered."""
        q = render.RenderQ(self.window.draw_screen, self.window.settings, 'dummy_menu')
        buttons = []

        return q, buttons

    def open(self):
        """Opens this menu for rendering and interaction."""
        self.q.disable = False
        self.loop()

    def close(self):
        """Prepares the current window to close."""
        self.q.disable = True

    def loop(self):
        """Runs until a selection is made."""
        while True:
            # Update the window and controls
            self.update_controls()
            self.window.update()

    def update_controls(self):
        """Updates the controls by a single tick."""
        # Check mouse clicks against buttons
        for each_button in self.buttons:
            if each_button.is_point_in(self.window.controls.mouse_last_down) \
                    and each_button.is_point_in(self.window.controls.mouse_last_up):
                self.window.controls.mouse_last_down = (0, 0)
                each_button.on_click()
            if each_button.is_point_in(self.window.controls.mouse_pos):
                each_button.on_hover()


class MenuButton(render.RenderBox):
    """The parent for all simple single click buttons."""

    def __init__(self, menu, center_pos, size, img_string, img_hover_string=None, label=None):
        self.menu = menu
        settings_button_rect = pygame.Rect((0, 0), size)
        settings_button_rect.center = center_pos

        settings_button_img = pygame.image.load(img_string)
        settings_button_img = pygame.transform.smoothscale(settings_button_img, size)

        if img_hover_string:
            self.img_hover = pygame.image.load(img_hover_string)
            self.img_hover = pygame.transform.smoothscale(self.img_hover, size)
        else:
            self.img_hover = None

        super().__init__(settings_button_rect, img=settings_button_img)

        if label:
            self.label_text = my_pygame_functions.TextBox(menu.window.settings)
            self.label_text.enable_bg((200, 150, 100))
            self.label_text.place_text_box((0, 0), 1, self.img.get_width())
            self.label_text.rect.center = (center_pos[0], center_pos[1] - (size[1]))
            self.label_text.do_center_text = True
            self.label_text.write(label.title())
        else:
            self.label_text = None

        self.is_hover = False

    def on_hover(self):
        """Shows the highlighted version of the button."""
        self.is_hover = True

    def update(self, renderer):
        if self.is_hover and self.img_hover:
            renderer.screen.blit(self.img_hover, self.rect)
        else:
            renderer.screen.blit(self.img, self.rect)

        # Render the label if it exists
        if self.label_text:
            self.label_text.update(renderer)

        # Reset the hover bool
        self.is_hover = False


class Slider(MenuButton):
    """A parent for sliders, used to control bounded variables in the menus."""
    def __init__(self, menu, center_pos, label=None):
        self.slider_img = pygame.image.load('images/gui/SliderStatic.png')
        self.slider_img = pygame.transform.smoothscale(self.slider_img,
                                                       (menu.window.settings.slider_width,
                                                        menu.window.settings.small_square_button_size[1] * 0.5))
        self.slider_rect = pygame.Rect((0, 0), (menu.window.settings.slider_width,
                                                menu.window.settings.small_square_button_size[1] * 0.5))
        self.slider_rect.center = center_pos
        self.slider_pos_as_percent = 0.5    # The slider's position as a percent.

        super().__init__(menu, center_pos, (menu.window.settings.small_square_button_size[0] * 0.566,
                                      menu.window.settings.small_square_button_size[1]),
                         'images/gui/SliderButton.png', 'images/gui/PlusButton.png', label)

        # Readjust label position for this button
        if self.label_text:
            self.label_text.place_text_box((0, 0), 1, self.slider_img.get_width())
            self.label_text.rect.center = (center_pos[0], center_pos[1] - self.rect.height)
            self.label_text.write(self.label_text.current_text.title())

    def update(self, renderer):
        # Move slider object to the position of the mouse
        if self.is_hover and self.menu.window.controls.mouse_is_clicked:
            # Move slider to mouse and collide with the edges of the slider
            self.rect.centerx = self.menu.window.controls.mouse_pos[0]
            if self.rect.centerx < self.slider_rect.left:
                self.rect.centerx = self.slider_rect.left
            elif self.rect.centerx > self.slider_rect.right:
                self.rect.centerx = self.slider_rect.right

            # Update the slider_pos_as_%
            self.slider_pos_as_percent = (self.rect.centerx - self.slider_rect.left) \
                                         / (self.slider_rect.right - self.slider_rect.left)

        # Render as normal
        renderer.screen.blit(self.slider_img, self.slider_rect)
        renderer.screen.blit(self.img, self.rect)

        # Render the Label
        if self.label_text:
            self.label_text.update(renderer)

        self.is_hover = False

    def set_slider_position(self, value):
        """Sets the slider position. Given number must be between 0.0 - 1.0, where 0.0 is the leftmost position."""
        self.slider_pos_as_percent = value
        self.rect.centerx = self.slider_rect.left + ((self.slider_rect.right - self.slider_rect.left) * self.slider_pos_as_percent)


class NumberIncrementSubButton(MenuButton):
    """Used by the NumberIncrementButton to alter its values."""
    def __init__(self, menu, parent_button, center_pos, size, is_plus_button):
        self.parent_button = parent_button
        self.is_plus_button = is_plus_button

        if is_plus_button:
            super().__init__(menu, center_pos, size, 'images/gui/PlusButton.png', 'images/gui/PlusButtonHover.png')
        else:
            super().__init__(menu, center_pos, size, 'images/gui/MinusButton.png', 'images/gui/MinusButtonHover.png')

    def on_click(self):
        """Tell the parent to increment itself."""
        if self.is_plus_button:
            self.parent_button.increment(1)
        else:
            self.parent_button.increment(-1)


class NumberIncrementButton:
    """A parent for buttons in which a number is incremented by clicking + and - buttons on either side.
    IMPORTANT: The subbuttons must be added to the menu's button lists individually in order to properly function."""
    def __init__(self, menu, center_pos, increment_step, limit_min, limit_max, label=None, round_to=1):
        self.menu = menu
        self.value = 0  # The internal value of the button, may not necessarily be needed by children objects
        self.limit_min = limit_min  # The min limit for the value before the - button stop working
        self.limit_max = limit_max  # The max limit for the value before the + button stop working
        self.increment_step = increment_step  # The change in value caused by incrementing with the buttons
        self.round_to = round_to
        size = self.menu.window.settings.small_square_button_size

        # Create the display text box
        self.display_text = my_pygame_functions.TextBox(self.menu.window.settings)
        self.display_text.place_text_box((0, 0), 1, size[0] * 4)
        self.display_text.do_center_text = True
        self.display_text.rect.center = center_pos
        self.display_text.enable_bg((200, 150, 100))
        self.display_text.write(str(self.value))

        # Create the label text box
        if label:
            self.label_text = my_pygame_functions.TextBox(menu.window.settings)
            self.label_text.enable_bg((200, 150, 100))
            self.label_text.place_text_box((0, 0), 1, self.display_text.rect.width)
            self.label_text.rect.center = (center_pos[0], center_pos[1] - (size[1]))
            self.label_text.do_center_text = True
            self.label_text.write(label.title())
        else:
            self.label_text = None

        # Create the subbuttons
        self.plus_button = NumberIncrementSubButton(menu, self, (center_pos[0] + (size[0] * 2), center_pos[1]), size, True)
        self.minus_button = NumberIncrementSubButton(menu, self, (center_pos[0] - (size[0] * 2), center_pos[1]), size, False)

    def increment(self, multi):
        """Called when the subbuttons are clicked, causes the target to be incremented. Must be written per extension"""
        self.value += self.increment_step * multi

        if self.value > self.limit_max:
            self.value = self.limit_max
        elif self.value < self.limit_min:
            self.value = self.limit_min

        self.value = round(self.value, self.round_to)

        self.display_text.write(str(self.value))

    def update(self, renderer):
        self.display_text.update(renderer)
        self.plus_button.update(renderer)
        self.minus_button.update(renderer)

        if self.label_text:
            self.label_text.update(renderer)


class ToggleBox(MenuButton):
    """A parent for all toggle box buttons."""
    def __init__(self, menu, center_pos, size, label=None):
        super().__init__(menu, center_pos, size, 'images/gui/ToggleButtonOn.png', 'images/gui/ToggleButtonOnHover.png', label)
        self.menu = menu

        self.state = False
        self.still_hover = False
        self.hover_delay = 0

        self.img_alt = pygame.image.load('images/gui/ToggleButtonOff.png')
        self.img_alt = pygame.transform.smoothscale(self.img_alt, size)
        self.img_alt_hover = pygame.image.load('images/gui/ToggleButtonOffHover.png')
        self.img_alt_hover = pygame.transform.smoothscale(self.img_alt_hover, size)

    def on_click(self):
        """Children objects should super.on_click for the image toggling feature."""
        self.state = not self.state
        self.still_hover = True

    def update(self, renderer):
        # Adjust for the hover delay
        if self.is_hover:
            self.hover_delay += 1
        # Determine if mouse focus has shifted away from the element since last activation
        else:
            if self.still_hover:
                self.still_hover = False
            self.hover_delay = 0

        # Update based on state, is_hover and the delay
        if self.state:
            if self.is_hover and not self.still_hover and self.hover_delay > self.menu.window.settings.button_hover_delay:
                renderer.screen.blit(self.img_hover, self.rect)
            else:
                renderer.screen.blit(self.img, self.rect)
        else:
            if self.is_hover and not self.still_hover and self.hover_delay > self.menu.window.settings.button_hover_delay:
                renderer.screen.blit(self.img_alt_hover, self.rect)
            else:
                renderer.screen.blit(self.img_alt, self.rect)

        # Render the label box
        if self.label_text:
            self.label_text.update(renderer)

        # Reset the hover bool
        self.is_hover = False


class DropdownBoxOption(MenuButton):
    """A subbutton to DropdownBox, used for the options in the drop down."""
    def __init__(self, parent_dropdown, center_pos, value):
        self.parent = parent_dropdown
        self.value = value
        stg = self.parent.menu.window.settings
        super().__init__(self.parent.menu, center_pos, (stg.drop_down_width, stg.small_square_button_size[1]),
                         'images/gui/DropDownOption.png')

        self.img.blit(stg.font_body.render(self.value, True, stg.clr['black']),
                      (stg.small_square_button_size[0] * 0.25, stg.small_square_button_size[1] * 0.04))

    def on_click(self):
        """Sends a signal to the parent box to update the value and closes the options drop down."""
        self.parent.select(self.value)
        self.parent.close()


class DropdownBox(MenuButton):
    """A parent for drop down box menu buttons."""
    def __init__(self, menu, center_pos, list_of_options, label=None):
        self.stg = menu.window.settings
        super().__init__(menu, center_pos, (self.stg.drop_down_width, self.stg.small_square_button_size[1]),
                         'images/gui/DropDownBox.png', label=label)

        self.opened = False
        self.options = self.make_buttons(list_of_options)
        self.current_value = self.options[0].value
        self.img_clean = self.img.copy()
        self.render_value()

    def render_value(self):
        """Rerenders the self.img to reflect the current value."""
        self.img = self.img_clean.copy()
        self.img.blit(self.stg.font_body.render(self.current_value, True, self.stg.clr['black']),
                      (self.stg.small_square_button_size[0] * 0.7, self.stg.small_square_button_size[1] * 0.04))

    def make_buttons(self, list_of_options):
        """Given a list of strings, produces a list of button objects in the same order."""
        buttons = []
        iteration_offset_multi = 1
        for each_option in list_of_options:
            buttons.append(DropdownBoxOption(self, (self.rect.centerx,
                                                    self.rect.centery +
                                                    (self.stg.small_square_button_size[1] * iteration_offset_multi)),
                                             each_option))
            iteration_offset_multi += 1

        return buttons

    def select(self, value):
        """Changes the current_value to the given value.
        In children will have further functionality for each selection made."""
        self.current_value = value
        self.render_value()

    def on_click(self):
        """Open or close the drop down menu."""
        if self.opened:
            self.close()
        else:
            self.open()

    def open(self):
        """Open the dropdown menu and set the necessary flags for everything to function."""
        for each_option in self.options:
            self.menu.buttons.append(each_option)

        self.opened = True

    def close(self):
        """Close the dropdown menu and clean up after yourself."""
        for each_option in self.options:
            self.menu.buttons.remove(each_option)

        self.opened = False

    def update(self, renderer):
        # If you are open
        if self.opened:
            # Render the buttons
            for each_option in self.options:
                each_option.update(renderer)

            # If the mouse is clicked, close
            if self.menu.window.controls.mouse_is_clicked:
                should_close = True
                if not self.is_hover:
                    for each_option in self.options:
                        if each_option.is_point_in(self.menu.window.controls.mouse_pos):
                            should_close = False
                            break
                if should_close:
                    self.close()

        # Render self as normal
        super().update(renderer)




