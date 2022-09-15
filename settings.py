from pygame.math import Vector2
import pygame
import numpy.random
import random


class Settings:
    """Contains the settings for the KhaosMap."""
    def __init__(self):
        self.map = None

        # Set the random seed
        self.seed = 42
        numpy.random.seed(self.seed)
        random.seed(self.seed)

        # Program settings
        self.debug_console = True
        self.debug_detail = 0       # All debug console calls with a LESSER debug detail will show. Range of (1-5)

        # Pygame settings
        self.window_size = (1800, 1000)
        self.text_box_width = 400
        self.screen_size = (self.window_size[0] - self.text_box_width, self.window_size[1])
        self.framerate = 60
        self.do_render_vertices = False
        self.do_render_atmosphere = True

        # Text settings
        pygame.font.init()
        self.font_size = 18
        self.font_body = pygame.font.Font('fonts/reemkufi.ttf', self.font_size)

        # Voronoi generation settings
        self.total_cells = 3000
        self.relax_passes = 5

        # Terrain generation settings
        self.tect_plates_min = 10    # The minimum number of tectonic plates used in altitude generation
        self.tect_plates_max = 35    # The maximum number of tectonic plates
        self.tect_min_dist = 0.1       # The minimum distance between two plate centers
        self.tect_attempt_to_place = 30     # Number of times the generator will try to place a single tectonic plate
        self.tect_smoothing_resolution = 4  # Depth of samples when smoothing by average altitude
        self.tect_smoothing_repetitions = 2  # Number of times to perform altitude smoothing
        self.tect_final_alt_mod = 0.5       # Determines the middlepoint of each plate's altitude gradient

        self.mtn_peak_reduction_factor = 0.05    # The maximum amount that mountain peaks are allowed to sit below 1.0
        self.mtn_peak_weight = 0.9           # The weight given to the peak when averaging for mountain ridges
        self.mtn_max_node_chain = 300        # Number vertexes in a mountain chain at maximum
        self.mtn_fork_chance = 0.15      # Percent chance a mountain node will fork
        self.mtn_ridges_max = 25        # Sets the maximum number of mountain ridges placed above the tectonic peaks
        self.mtn_ridges_min = 7         # Sets the minimum number

        self.atmo_tropics_extent = 0.2  # The +/- Y value where the tropics extend to from the "equator" (y = 0)
        self.atmo_arctic_extent = 0.2   # The Y value where the arctic zones extend to from the map's edges (far_y)
        self.atmo_iterations_per_frame = 2  # The number of times per frame to run the atmospheric calculations

        self.wind_streams_vector = Vector2(0.15, 0)  # The vector of the jetstreams added to wind vectors
        self.wind_deflection_weight = 1.3   # The weight given to the effect of a deflection modifier
        self.wind_take_strength = 0.22       # The percentage of a cell's wind that is lost to take_wind at wind_multi 1
        self.wind_critical_angle = 2     # Maximum angle that wind will
        self.wind_soft_cap = 0.7        # Soft cap on max wind speed
        self.wind_hard_cap = 1.1        # Hard cap for wind speed
        self.wind_resistance = 0.15     # Resistance offered by the soft cap and by air friction
        self.wind_presim = 0        # Number of wind ticks to presimulate in worldgen

        self.temps_equatorial = 95.0    # The target temperature for the equator (in F, because I am a dumb American)
        self.temps_freezing = 32.0   # A number used by the atmosphere renderer to determine the cold gradient
        self.temps_lowest = -35.0       # The lowest allowed temperature
        self.temps_highest = 130           # The temperature cap
        self.temps_equatorial_rise = 11.0  # The rise in temperature added at the equator to radiate heat to the map
        self.temps_arctic_cooling = 6.0  # The amount of temp lost in the arctic regions per tick
        self.temps_natural_cooling = 0.1    # Amount of heat lost each tick
        self.temps_critical_angle = 4  # The maximum angle (in radians) that allows a tile's wind to transfer heat
        self.temps_heat_bias = 1.2  # This is applied as a multiplier to heat propagation, inverse is applied to cold

        self.baro_transfer_rate = 0.04   # A multiplier on the value of pressure transfer between cells

        self.wtr_sea_level = 0.33    # The sea level of the terrain, all lower points will be underwater

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
