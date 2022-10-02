from menus import *


class SettingsMenu(GUIMenu):
    """The settings menu, where all the map settings can be adjusted."""
    def __init__(self, app_window):
        super().__init__(app_window)

    def init_menu_objs(self):
        """Initializes and places the elements of the settings menu in the settings menu Q, so they can be rendered."""
        stg_menu_Q = render.RenderQ(self.window.draw_screen, self.window.settings, 'settings_menu')

        # Add elements to the settings menu
        # BG image
        bg_img = pygame.image.load('images/gui/SettingsMenu.png')
        bg_img = pygame.transform.smoothscale(bg_img, self.window.settings.render_size)
        bg = render.RenderBox(pygame.Rect((0, 0), self.window.settings.render_size), img=bg_img)

        # Back button
        back_button = BackButton(self)

        """Water Settings Buttons"""
        # Sea level
        sea_level_button = SettingsButtonSeaLevelSlider(self)

        # Erosion toggle
        erosion_toggle_button = SettingsButtonErosionToggle(self)

        # Erosion speed
        erosion_speed_button = SettingsButtonErosionSpeedIncrement(self)

        """Map Settings Buttons"""
        # Total Cells
        total_cells_button = SettingsButtonTotalCellsIncrement(self)

        # Cell Regularity (Lloyd-Voronoi Relax Passes)
        cell_reg_button = SettingsButtonCellRegularityIncrement(self)

        # Tectonic Plates
        tect_plates_button = SettingsButtonTectonicPlateSlider(self)

        # Tectonic Plate Size
        tect_plate_size_button = SettingsButtonMinPlateSizeSlider(self)

        # Mountain height slider
        tect_final_alt_button = SettingsButtonMiddleAltitudeSlider(self)

        # Peak persistence (mtn reduction factor and inverse weight)
        peak_persist_button = SettingsButtonPeakPersistenceSlider(self)

        # Mountain Fork chance
        mtn_fork_button = SettingsButtonMtnForkSlider(self)

        # Min-Max Mountain Ridge buttons
        min_mtn_ridge_button = SettingsButtonMinMtnRidgesIncrement(self)
        max_mtn_ridge_button = SettingsButtonMaxMtnRidgesIncrement(self)
        min_mtn_ridge_button.pair(max_mtn_ridge_button)

        # Add everything to the Q and compose buttons list
        stg_menu_Q.add(bg, back_button,
                       sea_level_button, erosion_toggle_button, erosion_speed_button,
                       total_cells_button, cell_reg_button,
                       tect_plates_button, tect_plate_size_button, tect_final_alt_button, peak_persist_button,
                       mtn_fork_button, min_mtn_ridge_button, max_mtn_ridge_button
                       )
        buttons = [back_button,
                   sea_level_button, erosion_toggle_button,
                   erosion_speed_button.plus_button, erosion_speed_button.minus_button,
                   total_cells_button.plus_button, total_cells_button.minus_button,
                   cell_reg_button.plus_button, cell_reg_button.minus_button,
                   tect_plates_button, tect_plate_size_button, tect_final_alt_button, peak_persist_button,
                   mtn_fork_button,
                   min_mtn_ridge_button.plus_button, min_mtn_ridge_button.minus_button,
                   max_mtn_ridge_button.plus_button, max_mtn_ridge_button.minus_button,
                   ]

        return stg_menu_Q, buttons


class BackButton(MenuButton):
    """The back button that takes the player to the main menu. Used on the settings page."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.04, stg.render_size[1] * 0.05), stg.medium_square_button_size,
                         'images/gui/SettingsMenuButtonBack.png')

    def on_click(self):
        """Returns the player to the main menu."""
        self.menu.close()
        self.menu.window.start_menu.open()


class SettingsButtonSeaLevelSlider(Slider):
    """A slider that controls sea level."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.15, stg.render_size[1] * 0.14), 'sea level')

        self.set_slider_position(self.menu.window.settings.wtr_sea_level)

    def update(self, renderer):
        super().update(renderer)

        self.menu.window.settings.wtr_sea_level = 1 * self.slider_pos_as_percent


class SettingsButtonErosionToggle(ToggleBox):
    """A toggle button for the erosion calculations."""
    def __init__(self, menu):
        stg = menu.window.settings
        center_pos = (stg.render_size[0] * 0.15, stg.render_size[1] * 0.23)
        super().__init__(menu, center_pos, stg.small_square_button_size, 'erosion toggle')

        self.state = stg.erode_enable

        # Readjust label position for this button
        if self.label_text:
            self.label_text.place_text_box((0, 0), 1, self.img.get_width() * 4)
            self.label_text.rect.center = (center_pos[0], center_pos[1] - self.rect.height)
            self.label_text.write(self.label_text.current_text.title())

    def on_click(self):
        super().on_click()
        self.menu.window.settings.erode_mod = self.state


class SettingsButtonErosionSpeedIncrement(NumberIncrementButton):
    """A settings button that sets erosion speed."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.15, stg.render_size[1] * 0.32), 0.1, 0.0, 2.0, 'erosion speed')

        self.value = stg.erode_mod
        self.display_text.write(str(self.value))

    def increment(self, multi):
        super().increment(multi)

        self.menu.window.settings.erode_mod = self.value


class SettingsButtonTotalCellsIncrement(NumberIncrementButton):
    """A settings button that sets the total cells."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.14), 500, 1000, 7500, 'total cells')

        self.value = stg.total_cells
        self.display_text.write(str(self.value))

    def increment(self, multi):
        super().increment(multi)

        self.menu.window.settings.total_cells = self.value


class SettingsButtonCellRegularityIncrement(NumberIncrementButton):
    """A settings button that sets number of lloyd relaxes done to the voronoi diagram."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.23), 1, 0, 9, 'Cell Regularity')

        self.value = stg.relax_passes
        self.display_text.write(str(self.value))

    def increment(self, multi):
        super().increment(multi)

        self.menu.window.settings.relax_passes = self.value


class SettingsButtonTectonicPlateSlider(Slider):
    """A slider that controls the target number of tectonic plates."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.32), 'tectonic plates')

        self.set_slider_position(self.menu.window.settings.tect_plates_min / 20)

    def update(self, renderer):
        super().update(renderer)

        self.menu.window.settings.tect_plates_min = round(20 * self.slider_pos_as_percent)
        self.menu.window.settings.tect_plates_max = 4 * self.menu.window.settings.tect_plates_min


class SettingsButtonMinPlateSizeSlider(Slider):
    """A slider that controls the minimum tectonic plate size."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.41), 'plate size')

        self.set_slider_position(self.menu.window.settings.tect_min_dist * 10)

    def update(self, renderer):
        super().update(renderer)

        self.menu.window.settings.tect_min_dist = self.slider_pos_as_percent / 10


class SettingsButtonMiddleAltitudeSlider(Slider):
    """A slider that controls the middle altitude of the tectonic plates, functionally controls overall height."""

    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.50), 'overall altitude')

        self.set_slider_position(self.menu.window.settings.tect_final_alt_mod)

    def update(self, renderer):
        super().update(renderer)

        self.menu.window.settings.tect_final_alt_mod = self.slider_pos_as_percent


class SettingsButtonPeakPersistenceSlider(Slider):
    """A slider that controls both the peak reduction factor and the peak weight."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.59), 'peak persistence')

        self.set_slider_position(10 * (self.menu.window.settings.mtn_peak_weight - 0.9))

    def update(self, renderer):
        super().update(renderer)

        self.menu.window.settings.mtn_peak_weight = 0.9 + (self.slider_pos_as_percent * 0.1)
        self.menu.window.settings.mtn_peak_reduction_factor = 1 - self.menu.window.settings.mtn_peak_weight


class SettingsButtonMtnForkSlider(Slider):
    """A slider that controls both the peak reduction factor and the peak weight."""
    def __init__(self, menu):
        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.68), 'mountain forks')

        self.set_slider_position(self.menu.window.settings.mtn_fork_chance * 2)

    def update(self, renderer):
        super().update(renderer)

        self.menu.window.settings.mtn_fork_chance = self.slider_pos_as_percent / 2


class SettingsButtonMaxMtnRidgesIncrement(NumberIncrementButton):
    """An increment button for the maximum mountain ridges."""
    def __init__(self, menu):
        self.paired_button = None

        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.77), 1, 0, 50, 'Max Mountain Ridges')

        self.value = stg.mtn_ridges_max
        self.display_text.write(str(self.value))

    def pair(self, button):
        """Pairs this button with a button that shares some feature."""
        self.paired_button = button
        button.paired_button = self

    def increment(self, multi):
        super().increment(multi)

        if multi != 0:
            self.menu.window.settings.mtn_ridges_max = self.value
            if self.paired_button.value > self.value:
                self.paired_button.value = self.value
            self.paired_button.increment(0)


class SettingsButtonMinMtnRidgesIncrement(NumberIncrementButton):
    """An increment button for the minimum mountain ridges."""

    def __init__(self, menu):
        self.paired_button = None

        stg = menu.window.settings
        super().__init__(menu, (stg.render_size[0] * 0.3, stg.render_size[1] * 0.86), 1, 0, 25, 'Min Mountain Ridges')

        self.value = stg.mtn_ridges_min
        self.display_text.write(str(self.value))

    def pair(self, button):
        """Pairs this button with a button that shares some feature."""
        self.paired_button = button
        button.paired_button = self

    def increment(self, multi):
        super().increment(multi)

        if multi != 0:
            self.menu.window.settings.mtn_ridges_min = self.value
            if self.paired_button.value < self.value:
                self.paired_button.value = self.value
            self.paired_button.increment(0)

