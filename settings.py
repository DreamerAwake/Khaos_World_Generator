import json
import math

from pygame.math import Vector2
import pygame
import numpy.random
import random


class Settings:
    """Contains the settings for the KhaosMap."""
    def __init__(self):
        self.map = None
        # Set the version number
        self.version = 'V0.01.01'  # Format of V(release).(major version).(patch version)
        self.compatible_versions = []

        # Set the random seed
        self.seed = 139
        numpy.random.seed(self.seed)
        random.seed(self.seed)

        # Program settings
        self.debug_console = True
        self.debug_detail = 2       # All debug console calls with a LESSER debug detail will show. Range of (1-5)

        # Pygame settings
        self.enableAA = False
        self.window_width = 1200
        self.window_aspect = (16, 9)
        self.window_size = (self.window_width, round((self.window_width/self.window_aspect[0])*self.window_aspect[1]))
        self.text_box_width = 0
        self.render_size = (self.window_size[0], self.window_size[1])
        self.screen_size = (self.render_size[0] - self.text_box_width, self.render_size[1])
        self.framerate = 60
        self.do_render_altitudes = False
        self.do_render_rivers = True
        self.do_render_atmosphere = False
        self.do_render_rainfall = False
        self.do_render_coastlines = True

        # Color settings
        self.clr = {'black': (8, 8, 8),
                    'white': (252, 252, 252),
                    'ocean': (128, 128, 224),
                    'river': (32, 32, 96)}

        # Menu settings
        self.button_hover_delay = 1   # The delay in frames from hovering over a button to it showing its hovered state
        self.start_menu_button_size = (212, 60)
        self.small_square_button_size = (30, 30)
        self.medium_square_button_size = (50, 50)
        self.slider_width = 160
        self.drop_down_width = 85

        # Text settings
        pygame.font.init()
        self.font_head_size = 30
        self.font_body_size = 18
        self.font_head = pygame.font.Font('fonts/sylfaen.ttf', self.font_head_size)
        self.font_body = pygame.font.Font('fonts/reemkufi.ttf', self.font_body_size)

        # Voronoi generation settings
        self.total_cells = 2500
        self.relax_passes = 5

        # Terrain generation settings
        self.tect_plates_min = 10    # The minimum number of tectonic plates used in altitude generation
        self.tect_plates_max = 40    # The maximum number of tectonic plates
        self.tect_min_dist = 0.012       # The minimum distance between two plate centers
        self.tect_attempt_to_place = 30     # Number of times the generator will try to place a single tectonic plate
        self.tect_smoothing_resolution = 3  # Depth of samples when smoothing by average altitude
        self.tect_smoothing_repetitions = 2  # Number of times to perform altitude smoothing
        self.tect_final_alt_mod = 0.5       # Determines the middlepoint of each plate's altitude gradient

        self.mtn_peak_reduction_factor = 0.09    # The maximum amount that mountain peaks are allowed to sit below 1.0
        self.mtn_peak_weight = 0.91           # The weight given to the peak when averaging for mountain ridges
        self.mtn_max_node_chain = 300        # Number vertexes in a mountain chain at maximum
        self.mtn_fork_chance = 0.15      # Percent chance a mountain node will fork
        self.mtn_ridges_max = 25        # Sets the maximum number of mountain ridges placed above the tectonic peaks
        self.mtn_ridges_min = 7         # Sets the minimum number

        self.atmo_tropics_extent = 0.18  # The +/- Y value where the tropics extend to from the "equator" (y = 0)
        self.atmo_arctic_extent = 0.22  # The Y value where the arctic zones extend to from the map's edges (far_y)
        self.atmo_iterations_per_frame = 1  # The number of times per frame to run the atmospheric calculations

        self.wind_streams_vector = Vector2(0.11, 0)  # The vector of the jetstreams added to wind vectors
        self.wind_deflection_weight = 0.7  # The weight given to the effect of a deflection modifier
        self.wind_take_strength = 0.22  # The percentage of a cell's wind that is lost to take_wind at wind_multi 1
        self.wind_critical_angle = 2.2  # Maximum angle that wind will
        self.wind_soft_cap = 0.7  # Soft cap on max wind speed
        self.wind_hard_cap = 1.0  # Hard cap for wind speed
        self.wind_resistance = 0.015  # Resistance offered by the soft cap and by air friction
        self.wind_presim = 0        # Number of wind ticks to presimulate in worldgen

        self.temps_equatorial = 95.0    # The target temperature for the equator (in F, because I am a dumb American)
        self.temps_freezing = 32.0   # A number used by the atmosphere renderer to determine the cold gradient
        self.temps_lowest = -35.0       # The lowest allowed temperature
        self.temps_highest = 130           # The temperature cap
        self.temps_equatorial_rise = 10.0  # The rise in temperature added at the equator to radiate heat to the map
        self.temps_arctic_cooling = 9.0  # The amount of temp lost in the arctic regions per tick
        self.temps_natural_cooling = 0.3  # Amount of heat lost each tick
        self.temps_alt_cooling_threshold = 0.75  # The minimum altitude to experience elevation cooling effects
        self.temps_alt_cooling = 5.0  # The amount of cooling applied to an altitude of 1.0
        self.temps_critical_angle = 3.14  # The maximum angle (in radians) that allows a tile's wind to transfer heat
        self.temps_heat_bias = 1.6  # This is applied as a multiplier to heat propagation, inverse is applied to cold

        self.baro_transfer_rate = 0.3  # A multiplier on the value of pressure transfer between cells
        self.baro_wind_effect = 0.25  # The strength of pressure systems' ability to dampen wind interaction

        self.season_ticks_per_year = 360  # The number of atmosphere ticks per full 4 season year
        self.season_ticks_this_year = 0  # Controls the part of the year you start in. Must be lower than the above
        self.season_incline = 0.26  # The incline of the heat gradient relative to the equator at the solstices
        self.season_ticks_modifier = 0.0  # A Modifier calculated internally by the function .find_season_multi

        self.wtr_sea_level = 0.20  # The sea level of the terrain, all lower points will be underwater
        self.wtr_rainfall_mod = 0.28  # A multiplier on per-tick rainfall, only affects precipitation, not humidity
        self.wtr_rainfall_altitude_mod = 1.5  # A multiplier on altitude's ability to force humidity to drop rain
        self.wtr_baro_evap_rate = 0.001  # The size of a parcel of sea water evaporation pressure
        self.wtr_humid_evap_rate = 0.04  # The size of a parcel of sea water evaporation humidity
        self.wtr_drop_dist_mod = 0.8  # The multiplier of how much a drop in elevation causes draw from the watertable
        self.wtr_reabsorption = 0.5  # A multiplier on the rate that running water reabsorbs into the soil
        self.wtr_flow_ticks_to_ave = 10  # Number of previous ticks of waterflow averaged to produce a flowrate
        self.wtr_min_flow_to_render = 0  # Minimum flow rate for rendering to occur on a river
        self.wtr_river_flow_as_width = 150  # River flow is divided by this number to produce the render width
        self.wtr_max_river_render_width = 5  # The maximum width of a river when rendered

        self.erode_enable = True  # Whether erosion is calculated at all or not
        self.erode_mod = 1.0  # The multiplier applied to erosion rates

        # Biome generation settings
        self.biome_humid_high = 0.8  # Average humidity required for high humidity biomes to form
        self.biome_humid_low = 0.35  # Average humidity required for normal humidity biomes to form
        self.biome_arid = 0.07  # Threshold for developing arid environments
        self.biome_desert_temp = 80  # Threshold temperature for deserts
        self.biome_heavy_rainfall = 35  # Annual rainfall required to count as "heavy rainfall"
        self.biome_light_rainfall = 15  # Annual rainfall required to count as "light rainfall"
        self.biome_forest_water_req = 0.4  # The required cell hydration for a forest to form
        self.biome_rainforest_req = 0.6  # The required cell hydration for a rainforest to form
        self.biome_alpine_line = 0.78  # The lowest extent of alpine biomes
        self.biome_plains_height = 0.09  # Max height above sea level for floodplain based biomes
        self.biome_water_flow_effect = 1.5  # A multiplier on the effectiveness of waterflow at changing a biome

        # Biome Colors
        self.biome_tint_strength = 0.75  # A multiplier on the tint strength of the various biome colors
        self.biome_alt_tint_strength = 0.75  # A multiplier on the tint strength of the altitude color mods
        self.biome_temp_tint_strength = 0.5  # A multiplier on the tint strength of the temperature color mods
        self.biome_colors = {'frozen ocean': (180, 180, 244),
                             'arctic ocean': (120, 120, 240),
                             'coastal waters': (100, 128, 220),
                             'ocean': (60, 90, 220),
                             'frozen peaks': (232, 232, 255),
                             'tundra': (200, 212, 255),
                             'arid scrubland': (235, 205, 135),
                             'arid peaks': (100, 64, 48),
                             'savanna': (255, 220, 100),
                             'arid steppe': (230, 216, 156),
                             'high desert': (255, 255, 190),
                             'low desert': (255, 232, 170),
                             'dryland forest': (119, 136, 68),
                             'coastal dryland forest': (149, 170, 85),
                             'dry alpine forest': (153, 187, 119),
                             'steppe': (212, 212, 156),
                             'heath': (230, 186, 212),
                             'dry scrubland': (220, 205, 140),
                             'jungle': (0, 187, 32),
                             'tropical forest': (51, 185, 91),
                             'frozen forest': (77, 255, 166),
                             'alpine forest': (153, 211, 178),
                             'rainforest': (0, 128, 32),
                             'temperate forest': (91, 176, 75),
                             'flood plain': (91, 176, 120),
                             'cold scrubland coastline': (170, 170, 119),
                             'sand dunes': (220, 220, 160),
                             'temperate coastline': (140, 255, 120),
                             'meadow': (166, 255, 120),
                             'wetland forest': (51, 149, 103),
                             'coastal swamp': (64, 160, 100),
                             'bog': (96, 128, 85),
                             'cold marsh': (96, 109, 133),
                             'marsh': (96, 109, 100),
                             'swamp': (96, 196, 100),
                             'undefined land': (0, 0, 0)}

        if self.enableAA:
            self.set_antialias(self.enableAA)

    def set_antialias(self, enableAA):
        """Adjusts all necessary settings for antialiasing. If True, sets numbers to run under AA, if False,
        it will reverse the changes made."""
        if enableAA and not self.enableAA:
            self.enableAA = True

            # Pygame settings
            self.render_size = (self.window_size[0] * 2, self.window_size[1] * 2)
            self.screen_size = (self.render_size[0] - self.text_box_width, self.render_size[1])
            self.text_box_width *= 2

            # Menu settings
            self.start_menu_button_size = (self.start_menu_button_size[0] * 2, self.start_menu_button_size[1] * 2)
            self.small_square_button_size = (self.small_square_button_size[0] * 2, self.small_square_button_size[1] * 2)
            self.medium_square_button_size = (self.medium_square_button_size[0] * 2, self.medium_square_button_size[1] * 2)
            self.slider_width *= 2
            self.drop_down_width *= 2

            # Fonts
            self.font_head_size *= 2
            self.font_body_size *= 2

            # River rendering
            self.wtr_river_flow_as_width /= 2
            self.wtr_max_river_render_width *= 2
            return True

        elif not enableAA and self.enableAA:
            self.enableAA = False

            # Pygame settings
            self.render_size = (self.window_size[0] / 2, self.window_size[1] / 2)
            self.screen_size = (self.render_size[0] - self.text_box_width, self.render_size[1])
            self.text_box_width /= 2

            # Menu settings
            self.start_menu_button_size = (self.start_menu_button_size[0] / 2, self.start_menu_button_size[1] / 2)
            self.small_square_button_size = (self.small_square_button_size[0] / 2, self.small_square_button_size[1] / 2)
            self.medium_square_button_size = (self.medium_square_button_size[0] / 2, self.medium_square_button_size[1] / 2)
            self.slider_width /= 2
            self.drop_down_width /= 2

            # Fonts
            self.font_head_size /= 2
            self.font_body_size /= 2

            # River rendering
            self.wtr_river_flow_as_width *= 2
            self.wtr_max_river_render_width /= 2
            return True

        else:
            return False

    def save(self):
        """Saves a dict from save_to_dict as a discreet file."""
        file = self.save_to_dict()

        with open('saves/settings.json', 'w') as write_file:
            json.dump(file, write_file)


    def save_to_dict(self):
        """Saves the current settings to a dict variable."""
        # Create the save file
        file = {}

        # Get version number
        file['version'] = self.version

        # Load Seed and Program data
        file['seed'] = self.seed
        file['debug_console'] = self.debug_console
        file['debug_detail'] = self.debug_detail

        # Pygame settings
        file['enableAA'] = self.enableAA
        file['window_width'] = self.window_width
        file['window_aspect'] = self.window_aspect
        file['window_size'] = self.window_size
        file['text_box_width'] = self.text_box_width
        file['render_size'] = self.render_size
        file['screen_size'] = self.screen_size
        file['framerate'] = self.framerate
        file['do_render_altitudes'] = self.do_render_altitudes
        file['do_render_rivers'] = self.do_render_rivers
        file['do_render_atmosphere'] = self.do_render_atmosphere
        file['do_render_rainfall'] = self.do_render_rainfall
        file['do_render_coastlines'] = self.do_render_coastlines

        # Color settings
        file['clr'] = self.clr

        # Menu settings
        file['button_hover_delay'] = self.button_hover_delay
        file['start_menu_button_size'] = self.start_menu_button_size
        file['small_square_button_size'] = self.small_square_button_size
        file['medium_square_button_size'] = self.medium_square_button_size
        file['slider_width'] = self.slider_width
        file['drop_down_width'] = self.drop_down_width

        # Text settings
        file['font_head_size'] = self.font_head_size
        file['font_body_size'] = self.font_body_size

        # Voronoi generation settings
        file['total_cells'] = self.total_cells
        file['relax_passes'] = self.relax_passes

        # Terrain generation settings
        file['tect_plates_min'] = self.tect_plates_min
        file['tect_plates_max'] = self.tect_plates_max
        file['tect_min_dist'] = self.tect_min_dist
        file['tect_attempt_to_place'] = self.tect_attempt_to_place
        file['tect_smoothing_resolution'] = self.tect_smoothing_resolution
        file['tect_smoothing_repetitions'] = self.tect_smoothing_repetitions
        file['tect_final_alt_mod'] = self.tect_final_alt_mod

        file['mtn_peak_reduction_factor'] = self.mtn_peak_reduction_factor
        file['mtn_peak_weight'] = self.mtn_peak_weight
        file['mtn_max_node_chain'] = self.mtn_max_node_chain
        file['mtn_fork_chance'] = self.mtn_fork_chance
        file['mtn_ridges_max'] = self.mtn_ridges_max
        file['mtn_ridges_min'] = self.mtn_ridges_min

        file['atmo_tropics_extent'] = self.atmo_tropics_extent
        file['atmo_arctic_extent'] = self.atmo_arctic_extent
        file['atmo_iterations_per_frame'] = self.atmo_iterations_per_frame

        file['wind_streams_vector'] = self.wind_streams_vector.x
        file['wind_deflection_weight'] = self.wind_deflection_weight
        file['wind_take_strength'] = self.wind_take_strength
        file['wind_critical_angle'] = self.wind_critical_angle
        file['wind_soft_cap'] = self.wind_soft_cap
        file['wind_hard_cap'] = self.wind_hard_cap
        file['wind_resistance'] = self.wind_resistance
        file['wind_presim'] = self.wind_presim

        file['temps_equatorial'] = self.temps_equatorial
        file['temps_freezing'] = self.temps_freezing
        file['temps_lowest'] = self.temps_lowest
        file['temps_highest'] = self.temps_highest
        file['temps_equatorial_rise'] = self.temps_equatorial_rise
        file['temps_arctic_cooling'] = self.temps_arctic_cooling
        file['temps_natural_cooling'] = self.temps_natural_cooling
        file['temps_alt_cooling_threshold'] = self.temps_alt_cooling_threshold
        file['temps_alt_cooling'] = self.temps_alt_cooling
        file['temps_critical_angle'] = self.temps_critical_angle
        file['temps_heat_bias'] = self.temps_heat_bias

        file['baro_transfer_rate'] = self.baro_transfer_rate
        file['baro_wind_effect'] = self.baro_wind_effect

        file['season_ticks_per_year'] = self.season_ticks_per_year
        file['season_ticks_this_year'] = self.season_ticks_this_year
        file['season_incline'] = self.season_incline
        file['season_ticks_modifier'] = self.season_ticks_modifier

        file['wtr_sea_level'] = self.wtr_sea_level
        file['wtr_rainfall_mod'] = self.wtr_rainfall_mod
        file['wtr_rainfall_altitude_mod'] = self.wtr_rainfall_altitude_mod
        file['wtr_baro_evap_rate'] = self.wtr_baro_evap_rate
        file['wtr_humid_evap_rate'] = self.wtr_humid_evap_rate
        file['wtr_drop_dist_mod'] = self.wtr_drop_dist_mod
        file['wtr_reabsorption'] = self.wtr_reabsorption
        file['wtr_flow_ticks_to_ave'] = self.wtr_flow_ticks_to_ave
        file['wtr_min_flow_to_render'] = self.wtr_min_flow_to_render
        file['wtr_river_flow_as_width'] = self.wtr_river_flow_as_width
        file['wtr_max_river_render_width'] = self.wtr_max_river_render_width

        file['erode_enable'] = self.erode_enable
        file['erode_mod'] = self.erode_mod

        # Biome generation settings
        file['biome_humid_high'] = self.biome_humid_high
        file['biome_humid_low'] = self.biome_humid_low
        file['biome_arid'] = self.biome_arid
        file['biome_desert_temp'] = self.biome_desert_temp
        file['biome_heavy_rainfall'] = self.biome_heavy_rainfall
        file['biome_light_rainfall'] = self.biome_light_rainfall
        file['biome_forest_water_req'] = self.biome_forest_water_req
        file['biome_rainforest_req'] = self.biome_rainforest_req
        file['biome_alpine_line'] = self.biome_alpine_line
        file['biome_plains_height'] = self.biome_plains_height
        file['biome_water_flow_effect'] = self.biome_water_flow_effect

        # Biome colors
        file['biome_tint_strength'] = self.biome_tint_strength
        file['biome_alt_tint_strength'] = self.biome_alt_tint_strength
        file['biome_temp_tint_strength'] = self.biome_temp_tint_strength
        file['biome_colors'] = self.biome_colors

        return file

    def load(self):
        """Loads settings dict from a file."""
        with open('saves/settings.json') as read_file:
            file = json.load(read_file)

        self.load_from_dict(file)

    def load_from_dict(self, file):
        """Loads the settings from a dict variable."""

        # Get version number
        if self.version == file['version'] or file['version'] in self.compatible_versions:

            # Load Seed and Program data
            self.seed = file['seed']
            self.debug_console = file['debug_console']
            self.debug_detail = file['debug_detail']

            # Pygame settings
            self.enableAA = file['enableAA']
            self.window_width = file['window_width']
            self.window_aspect = file['window_aspect']
            self.window_size = file['window_size']
            self.text_box_width = file['text_box_width']
            self.render_size = file['render_size']
            self.screen_size = file['screen_size']
            self.framerate = file['framerate']
            self.do_render_altitudes = file['do_render_altitudes']
            self.do_render_rivers = file['do_render_rivers']
            self.do_render_atmosphere = file['do_render_atmosphere']
            self.do_render_rainfall = file['do_render_rainfall']
            self.do_render_coastlines = file['do_render_coastlines']

            # Color settings
            self.clr = file['clr']

            # Menu settings
            self.button_hover_delay = file['button_hover_delay']
            self.start_menu_button_size = file['start_menu_button_size']
            self.small_square_button_size = file['small_square_button_size']
            self.medium_square_button_size = file['medium_square_button_size']
            self.slider_width = file['slider_width']
            self.drop_down_width = file['drop_down_width']

            # Text settings
            self.font_head_size = file['font_head_size']
            self.font_body_size = file['font_body_size']

            # Voronoi generation settings
            self.total_cells = file['total_cells']
            self.relax_passes =file['relax_passes']

            # Terrain generation settings
            self.tect_plates_min = file['tect_plates_min']
            self.tect_plates_max = file['tect_plates_max']
            self.tect_min_dist = file['tect_min_dist']
            self.tect_attempt_to_place = file['tect_attempt_to_place']
            self.tect_smoothing_resolution = file['tect_smoothing_resolution']
            self.tect_smoothing_repetitions = file['tect_smoothing_repetitions']
            self.tect_final_alt_mod = file['tect_final_alt_mod']

            self.mtn_peak_reduction_factor = file['mtn_peak_reduction_factor']
            self.mtn_peak_weight = file['mtn_peak_weight']
            self.mtn_max_node_chain = file['mtn_max_node_chain']
            self.mtn_fork_chance = file['mtn_fork_chance']
            self.mtn_ridges_max = file['mtn_ridges_max']
            self.mtn_ridges_min = file['mtn_ridges_min']

            self.atmo_tropics_extent = file['atmo_tropics_extent']
            self.atmo_arctic_extent = file['atmo_arctic_extent']
            self.atmo_iterations_per_frame = file['atmo_iterations_per_frame']

            self.wind_streams_vector = Vector2(file['wind_streams_vector'], 0)
            self.wind_deflection_weight = file['wind_deflection_weight']
            self.wind_take_strength = file['wind_take_strength']
            self.wind_critical_angle = file['wind_critical_angle']
            self.wind_soft_cap = file['wind_soft_cap']
            self.wind_hard_cap = file['wind_hard_cap']
            self.wind_resistance = file['wind_resistance']
            self.wind_presim = file['wind_presim']

            self.temps_equatorial = file['temps_equatorial']
            self.temps_freezing = file['temps_freezing']
            self.temps_lowest = file['temps_lowest']
            self.temps_highest = file['temps_highest']
            self.temps_equatorial_rise = file['temps_equatorial_rise']
            self.temps_arctic_cooling = file['temps_arctic_cooling']
            self.temps_natural_cooling = file['temps_natural_cooling']
            self.temps_alt_cooling_threshold = file['temps_alt_cooling_threshold']
            self.temps_alt_cooling = file['temps_alt_cooling']
            self.temps_critical_angle = file['temps_critical_angle']
            self.temps_heat_bias = file['temps_heat_bias']

            self.baro_transfer_rate = file['baro_transfer_rate']
            self.baro_wind_effect = file['baro_wind_effect']

            self.season_ticks_per_year = file['season_ticks_per_year']
            self.season_ticks_this_year = file['season_ticks_this_year']
            self.season_incline = file['season_incline']
            self.season_ticks_modifier = file['season_ticks_modifier']

            self.wtr_sea_level = file['wtr_sea_level']
            self.wtr_rainfall_mod = file['wtr_rainfall_mod']
            self.wtr_rainfall_altitude_mod = file['wtr_rainfall_altitude_mod']
            self.wtr_baro_evap_rate = file['wtr_baro_evap_rate']
            self.wtr_humid_evap_rate = file['wtr_humid_evap_rate']
            self.wtr_drop_dist_mod = file['wtr_drop_dist_mod']
            self.wtr_reabsorption = file['wtr_reabsorption']
            self.wtr_flow_ticks_to_ave = file['wtr_flow_ticks_to_ave']
            self.wtr_min_flow_to_render = file['wtr_min_flow_to_render']
            self.wtr_river_flow_as_width = file['wtr_river_flow_as_width']
            self.wtr_max_river_render_width = file['wtr_max_river_render_width']

            self.erode_enable = file['erode_enable']
            self.erode_mod = file['erode_mod']

            # Biome generation settings
            self.biome_humid_high = file['biome_humid_high']
            self.biome_humid_low = file['biome_humid_low']
            self.biome_arid = file['biome_arid']
            self.biome_desert_temp = file['biome_desert_temp']
            self.biome_heavy_rainfall = file['biome_heavy_rainfall']
            self.biome_light_rainfall = file['biome_light_rainfall']
            self.biome_forest_water_req = file['biome_forest_water_req']
            self.biome_rainforest_req = file['biome_rainforest_req']
            self.biome_alpine_line = file['biome_alpine_line']
            self.biome_plains_height = file['biome_plains_height']
            self.biome_water_flow_effect = file['biome_water_flow_effect']

            # Biome colors
            self.biome_tint_strength = file['biome_tint_strength']
            self.biome_alt_tint_strength = file['biome_alt_tint_strength']
            self.biome_temp_tint_strength = file['biome_temp_tint_strength']
            self.biome_colors = file['biome_colors']


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
