import math

from pygame.math import Vector2
import pygame
import numpy.random
import random


class Settings:
    """Contains the settings for the KhaosMap."""
    def __init__(self):
        self.map = None

        # Set the random seed
        self.seed = 91
        numpy.random.seed(self.seed)
        random.seed(self.seed)

        # Program settings
        self.debug_console = True
        self.debug_detail = 2       # All debug console calls with a LESSER debug detail will show. Range of (1-5)

        # Pygame settings
        self.enableAA = True
        self.window_size = (1800, 1000)
        self.text_box_width = 400
        if self.enableAA:
            self.render_size = (self.window_size[0] * 2, self.window_size[1] * 2)
            self.text_box_width *= 2
        else:
            self.render_size = (self.window_size[0], self.window_size[1])
        self.screen_size = (self.render_size[0] - self.text_box_width, self.render_size[1])
        self.framerate = 60
        self.do_render_altitudes = False
        self.do_render_rivers = True
        self.do_render_atmosphere = False
        self.do_render_rainfall = False

        # Color settings
        self.clr = {'black': (8, 8, 8),
                    'ocean': (128, 128, 224),
                    'river': (64, 64, 128)}

        # Text settings
        pygame.font.init()
        self.font_head_size = 30
        self.font_body_size = 18
        if self.enableAA:
            self.font_head_size *= 2
            self.font_body_size *= 2
        self.font_head = pygame.font.Font('fonts/sylfaen.ttf', self.font_head_size)
        self.font_body = pygame.font.Font('fonts/reemkufi.ttf', self.font_body_size)

        # Voronoi generation settings
        self.total_cells = 500
        self.relax_passes = 5

        # Terrain generation settings
        self.tect_plates_min = 15    # The minimum number of tectonic plates used in altitude generation
        self.tect_plates_max = 40    # The maximum number of tectonic plates
        self.tect_min_dist = 0.015       # The minimum distance between two plate centers
        self.tect_attempt_to_place = 30     # Number of times the generator will try to place a single tectonic plate
        self.tect_smoothing_resolution = 3  # Depth of samples when smoothing by average altitude
        self.tect_smoothing_repetitions = 2  # Number of times to perform altitude smoothing
        self.tect_final_alt_mod = 0.5       # Determines the middlepoint of each plate's altitude gradient

        self.mtn_peak_reduction_factor = 0.05    # The maximum amount that mountain peaks are allowed to sit below 1.0
        self.mtn_peak_weight = 0.9           # The weight given to the peak when averaging for mountain ridges
        self.mtn_max_node_chain = 300        # Number vertexes in a mountain chain at maximum
        self.mtn_fork_chance = 0.15      # Percent chance a mountain node will fork
        self.mtn_ridges_max = 25        # Sets the maximum number of mountain ridges placed above the tectonic peaks
        self.mtn_ridges_min = 7         # Sets the minimum number

        self.atmo_tropics_extent = 0.15  # The +/- Y value where the tropics extend to from the "equator" (y = 0)
        self.atmo_arctic_extent = 0.2   # The Y value where the arctic zones extend to from the map's edges (far_y)
        self.atmo_iterations_per_frame = 1  # The number of times per frame to run the atmospheric calculations

        self.wind_streams_vector = Vector2(0.12, 0)  # The vector of the jetstreams added to wind vectors
        self.wind_deflection_weight = 1.2   # The weight given to the effect of a deflection modifier
        self.wind_take_strength = 0.22       # The percentage of a cell's wind that is lost to take_wind at wind_multi 1
        self.wind_critical_angle = 2     # Maximum angle that wind will
        self.wind_soft_cap = 0.5        # Soft cap on max wind speed
        self.wind_hard_cap = 1.0        # Hard cap for wind speed
        self.wind_resistance = 0.02     # Resistance offered by the soft cap and by air friction
        self.wind_presim = 0        # Number of wind ticks to presimulate in worldgen

        self.temps_equatorial = 95.0    # The target temperature for the equator (in F, because I am a dumb American)
        self.temps_freezing = 32.0   # A number used by the atmosphere renderer to determine the cold gradient
        self.temps_lowest = -35.0       # The lowest allowed temperature
        self.temps_highest = 130           # The temperature cap
        self.temps_equatorial_rise = 10.0  # The rise in temperature added at the equator to radiate heat to the map
        self.temps_arctic_cooling = 7.0  # The amount of temp lost in the arctic regions per tick
        self.temps_natural_cooling = 0.3    # Amount of heat lost each tick
        self.temps_alt_cooling_threshold = 0.8  # The minimum altitude to experience elevation cooling effects
        self.temps_alt_cooling = 4.5    # The amount of cooling applied to an altitude of 1.0
        self.temps_critical_angle = 3.14  # The maximum angle (in radians) that allows a tile's wind to transfer heat
        self.temps_heat_bias = 1.4  # This is applied as a multiplier to heat propagation, inverse is applied to cold

        self.baro_transfer_rate = 0.3   # A multiplier on the value of pressure transfer between cells
        self.baro_wind_effect = 0.2  # The strength of pressure systems' ability to dampen wind interaction

        self.season_ticks_per_year = 360  # The number of atmosphere ticks per full 4 season year
        self.season_ticks_this_year = 0  # Controls the part of the year you start in. Must be lower than the above
        self.season_incline = 0.22  # The incline of the heat gradient relative to the equator at the solstices
        self.season_ticks_modifier = 0.0    # A Modifier calculated internally by the function .find_season_multi

        self.wtr_sea_level = 0.30  # The sea level of the terrain, all lower points will be underwater
        self.wtr_rainfall_mod = 1.0  # A multiplier on per-tick rainfall, only affects precipitation, not humidity
        self.wtr_baro_evap_rate = 0.001  # The size of a parcel of sea water evaporation pressure
        self.wtr_humid_evap_rate = 0.02   # The size of a parcel of sea water evaporation humidity
        self.wtr_drop_dist_mod = 1.0    # The multiplier of how much a drop in elevation causes draw from the watertable
        self.wtr_reabsorption = 0.7     # A multiplier on the rate that running water reabsorbs into the soil
        self.wtr_flow_ticks_to_ave = 10  # Number of previous ticks of waterflow averaged to produce a flowrate
        self.wtr_min_flow_to_render = 0   # Minimum flow rate for rendering to occur on a river
        self.wtr_river_flow_as_width = 650  # River flow is divided by this number to produce the render width
        self.wtr_max_river_render_width = 4  # The maximum width of a river when rendered

        if self.enableAA:
            self.wtr_river_flow_as_width /= 2
            self.wtr_max_river_render_width *= 2

    def db_print(self, string, detail=0):
        """A debugging function that allows selective printing of debug console text based on a
        level of detail set per message. Helps cut down on console clutter/vomit."""
        if self.debug_console and detail <= self.debug_detail:
            print(string)

    def find_season_multi(self, year_as_percent):
        """Takes the percentage of this year's ticks that have been completed already and sets season_ticks_modifier"""
        self.season_ticks_modifier = math.sin(year_as_percent / (math.pi / 20)) * self.season_incline

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
