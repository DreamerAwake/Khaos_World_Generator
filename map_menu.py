import khaos_map
import settings_menu
from menus import *


class MapMenu(GUIMenu):
    """The main map menu, where the Khaos map is rendered and updated."""
    def __init__(self, app_window):
        self.map = None
        super().__init__(app_window)

    def init_with_map_data(self, k_map):
        """Reinitializes the object with the given map data"""
        self.map = k_map

        # Create the RenderQs
        cellQ = render.RenderQ(self.window.draw_screen, self.window.settings, 'cell')

        atmosphereQ = render.RenderQ(self.window.draw_screen, self.window.settings, 'atmosphere')
        atmosphereQ.disable = not self.window.settings.do_render_atmosphere

        vertexQ = render.RenderQ(self.window.draw_screen, self.window.settings, 'vertex')

        # Add the elements from the map to the RenderQs
        for each_cell in self.map.cells:
            cellQ.add(each_cell)
            atmosphereQ.add(each_cell)

        for each_vertex in self.map.vertices:
            vertexQ.add(each_vertex)

        self.q.add(cellQ, vertexQ, atmosphereQ, place_on_bottom=True)

    def init_menu_objs(self):
        """Initializes and places the elements of the start menu in the start menu Q, so they can be rendered."""

        # DEBUG Create a back button
        back_button = settings_menu.BackButton(self)

        # Create the dropdowns at the top of the screen
        file_dropdown_button = MapMenuFileDropDown(self)

        map_menu_Q = render.RenderQ(self.window.draw_screen, self.window.settings, 'map_menu')
        map_menu_Q.add(back_button, file_dropdown_button)

        buttons = [back_button, file_dropdown_button]

        return map_menu_Q, buttons

    def unload_map(self):
        """Unloads the current map so a new one can take its place."""
        for each_renderable in self.q.queue:
            if isinstance(each_renderable, render.RenderQ):
                self.q.remove(each_renderable)

    def loop(self):
        while True:
            # Update the window and controls
            self.update_controls()

            # Update wind
            for iteration in range(0, self.window.settings.atmo_iterations_per_frame):
                self.map.update_atmosphere()

            # Run the master update
            self.window.update()


class MapMenuFileDropDown(DropdownBox):
    """The File dropdown on the top bar of the map menu."""
    def __init__(self, menu):
        super().__init__(menu, (menu.window.settings.drop_down_width / 2,
                                menu.window.settings.small_square_button_size[1] / 2),
                         ['New', 'Save', 'Load', 'Close'])

        self.render_value('File')

    def select(self, value):
        """Handles selections from the drop down."""

        if value == 'New':
            self.menu.close()
            self.menu.unload_map()
            self.menu.init_with_map_data(khaos_map.KhaosMap(self.menu.window.settings))
            self.menu.open()

        if value == 'Save':
            self.menu.map.save()

        if value == 'Load':
            filename = input("Please enter the file name of the save you would like to load.")
            new_map = khaos_map.KhaosMap(self.menu.window.settings, f"saves/{filename}.json")
            self.menu.close()
            self.menu.unload_map()
            self.menu.init_with_map_data(new_map)
            self.menu.open()
