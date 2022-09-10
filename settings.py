import numpy.random
import random


class Settings:
    """Contains the settings for the KhaosMap."""
    def __init__(self):
        self.map = None

        # Set the random seed
        self.seed = 36
        numpy.random.seed(self.seed)
        random.seed(self.seed)

        # Program settings
        self.debug_console = True
        self.debug_detail = 2       # All debug console calls with a LESSER debug detail will show. Range of (1-5)

        # Pygame settings
        self.screen_size = (1200, 900)
        self.do_render_vertices = False

        # Voronoi generation settings
        self.total_cells = 3000
        self.relax_passes = 5

        # Terrain generation settings
        self.tect_plates_min = 10    # The minimum number of tectonic plates used in altitude generation
        self.tect_plates_max = 20    # The maximum number of tectonic plates
        self.tect_min_dist = 0.04       # The minimum distance between two plate centers
        self.tect_attempt_to_place = 30     # Number of times the generator will try to place a single tectonic plate
        self.tect_smoothing_resolution = 4  # Depth of samples when smoothing by average altitude
        self.tect_smoothing_repetitions = 2  # Number of times to perform altitude smoothing
        self.tect_final_alt_mod = 0.5       # Determines the middlepoint of each plate's altitude gradient

        self.mtn_peak_reduction_factor = 0.1    # The maximum amount that mountain peaks are allowed to sit below 1.0
        self.mtn_peak_weight = 0.9           # The weight given to the peak when averaging for mountain ridges
        self.mtn_max_node_chain = 200        # Number vertexes in a mountain chain at maximum
        self.mtn_fork_chance = 0.15      # Percent chance a mountain node will fork
        self.mtn_ridges_max = 25        # Sets the maximum number of mountain ridges placed above the tectonic peaks
        self.mtn_ridges_min = 7         # Sets the minimum number

        self.wtr_sea_level = 0.3    # The sea level of the terrain, all lower points will be underwater

    def db_print(self, string, detail=0):
        """A debugging function that allows selective printing of debug console text based on a
        level of detail set per message. Helps cut down on console clutter/vomit."""
        if self.debug_console and detail <= self.debug_detail:
            print(string)

    def project_to_screen(self, x, y):
        """Takes an x, y between -1.0 and 1.0, and projects them into the coordinates based on the screen size."""
        # Find the width of a pixel on the screen, expressed as a ratio of 1, divide in half because 0,0 is centered
        ss_x = self.screen_size[0] / 2
        ss_y = self.screen_size[1] / 2

        # Readjust relative to the outlying cells to include them in the window
        ss_x = (ss_x * 3) / (self.map.far_x + 2)
        ss_y = (ss_y * 3) / (self.map.far_y + 2)

        # Find the relative position by multiplying the pixel ratio by the position
        ss_x *= x
        ss_y *= y

        # Add 1/2 the screen width to adjust for the 0,0 of the screen being offset of the map's 0,0 center
        ss_x += self.screen_size[0] / 2
        ss_y += self.screen_size[1] / 2

        # Return the result
        return ss_x, ss_y

