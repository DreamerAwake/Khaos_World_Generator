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

        # DEBUG Create a back button
        back_button = settings_menu.BackButton(self)

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

        self.q.add(cellQ, vertexQ, atmosphereQ, back_button)
        self.buttons.append(back_button)

    def init_menu_objs(self):
        """Initializes and places the elements of the start menu in the start menu Q, so they can be rendered."""

        map_menu_Q = render.RenderQ(self.window.draw_screen, self.window.settings, 'map_menu')
        buttons = []

        return map_menu_Q, buttons

    def loop(self):
        while True:
            # Update the window and controls
            self.update_controls()

            # Update wind
            for iteration in range(0, self.window.settings.atmo_iterations_per_frame):
                self.map.update_atmosphere()

            # Run the master update
            self.window.update()
