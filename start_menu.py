import sys

import khaos_map
from menus import *


class StartMenu(GUIMenu):
    """The start menu object."""
    def __init__(self, app_window):
        super().__init__(app_window)

    def init_menu_objs(self):
        """Initializes and places the elements of the start menu in the start menu Q, so they can be rendered."""
        start_menu_Q = render.RenderQ(self.window.draw_screen, self.window.settings, 'start_menu')
        buttons = []

        # Add elements to the start menu
        # BG image
        bg_img = pygame.image.load('images/gui/StartMenu.png')
        bg_img = pygame.transform.smoothscale(bg_img, self.window.settings.render_size)
        bg = render.RenderBox(pygame.Rect((0, 0), self.window.settings.render_size), img=bg_img)

        # Start button
        start_button = StartButton(self)
        buttons.append(start_button)

        # Load button
        load_button = LoadButton(self)
        buttons.append(load_button)

        # Settings button
        stg_button = SettingsButton(self)
        buttons.append(stg_button)

        # Exit button
        exit_button = ExitButton(self)
        buttons.append(exit_button)

        # Add everything to the Q
        start_menu_Q.add(bg, start_button, load_button, stg_button, exit_button)

        return start_menu_Q, buttons


class StartButton(MenuButton):
    """The button that starts the main map generator."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] / 2, stg.render_size[1] * 0.6), stg.start_menu_button_size,
                         'images/gui/StartMenuButtonStart.png',
                         'images/gui/StartMenuButtonStartHover.png')

    def on_click(self):
        """Opens the map menu. WIP"""
        if self.menu.window.map_menu.map is None:
            self.menu.window.map_menu.init_with_map_data(khaos_map.KhaosMap(self.menu.window.settings))

        self.menu.close()
        self.menu.window.map_menu.open()

class LoadButton(MenuButton):
    """The button that loads maps from file."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] / 2, stg.render_size[1] * 0.7), stg.start_menu_button_size,
                         'images/gui/StartMenuButtonLoad.png',
                         'images/gui/StartMenuButtonLoadHover.png')

    def on_click(self):
        """Opens the load map file dialog. WIP"""
        # TODO Write the load map function so this has something to point to
        pass


class SettingsButton(MenuButton):
    """The button that opens the settings menu."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] / 2, stg.render_size[1] * 0.8), stg.start_menu_button_size,
                         'images/gui/StartMenuButtonSettings.png',
                         'images/gui/StartMenuButtonSettingsHover.png')

    def on_click(self):
        """Opens the settings menu."""
        self.menu.close()
        self.menu.window.settings_menu.open()


class ExitButton(MenuButton):
    """The button that exits the program."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] / 2, stg.render_size[1] * 0.9), stg.start_menu_button_size,
                         'images/gui/StartMenuButtonExit.png',
                         'images/gui/StartMenuButtonExitHover.png')

    def on_click(self):
        """Closes the program"""
        sys.exit()

