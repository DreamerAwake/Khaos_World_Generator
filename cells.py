import math

import pygame.draw

from render import *


class Cell(Renderable):
    """Stores information about a single cell, which has a generator point treated as a pseudo-center and a region
    formed of shared edge vertices with its neighbor cells."""

    def __init__(self, point, settings):
        super().__init__()

        self.settings = settings

        # Cell data
        self.x, self.y = point
        self.ss_x = None
        self.ss_y = None
        self.region = {}
        self.neighbors = {}

        # Associated Terrain data
        self.altitude = 0.0
        self.lowest_vertex = None
        self.wind_deflection = None
        self.wind_vector = pygame.math.Vector2(0, 0)
        self.temperature = (settings.temps_equatorial + settings.temps_lowest) / 2
        self.humidity = 0.0

        # Rainfall data
        self.rainfall_this_year = 0
        self.rainfall_last_year = 0
        self.watertable = 1000 * self.settings.wtr_sea_level

        # Set pressure based on location on the map, northern climes start with low pressure
        if abs(self.y) > 1.2 - self.settings.atmo_arctic_extent:
            self.pressure = -0.2
        elif abs(self.y) < self.settings.atmo_tropics_extent:
            self.pressure = 0.2
        else:
            self.pressure = 0.01

        # The delta values for atmosphere calculation
        self.wind_vector_delta = pygame.math.Vector2(0, 0)
        self.temperature_delta = 0
        self.pressure_delta = 0
        self.humidity_delta = 0.0

        # Rendering Settings
        self.polygon = None
        self.cell_color = (0, 64, 0)
        self.is_focus = False

    def find_altitude(self):
        """Finds the average altitude of the vertices and makes it the total altitude of the cell"""
        self.altitude = 0.0

        for each_vertex in self.region.keys():
            self.altitude += each_vertex.altitude

        self.altitude /= len(self.region)

    def find_color(self):

        if self.temperature > self.settings.temps_freezing:
            total_temps_range = (self.settings.temps_equatorial - self.settings.temps_lowest)
            ave_temps = (total_temps_range / 2)
            heat_r_mod = ((self.temperature - self.settings.temps_lowest) - ave_temps) / ave_temps
            heat_g_mod = ((self.temperature - self.settings.temps_lowest) - self.settings.temps_lowest) / total_temps_range
            heat_b_mod = ((self.temperature - self.settings.temps_lowest) - ave_temps) / ave_temps + 0.25

            rainfall_mod = self.rainfall_this_year / 1000
            if rainfall_mod > 1:
                rainfall_mod = 1

            colors = [(86 * self.altitude) + (20 * heat_r_mod),
                      128 + (92 * self.altitude) + (20 * rainfall_mod) - (6 ** (heat_g_mod + 1)),
                      (100 * self.altitude) + (64 * self.humidity) + (28 * rainfall_mod) - (32 * heat_b_mod)]

            for index in range(0, len(colors)):
                if colors[index] < 0:
                    colors[index] = 0
                elif colors[index] > 255:
                    colors[index] = 255

        else:
            colors = [128 + (128 * self.altitude), 128 + (128 * self.altitude), 128 + (128 * self.altitude)]

        self.cell_color = colors

    def find_screen_space(self):
        """Finds the x and y of the cell on the screen."""
        self.ss_x, self.ss_y = self.settings.project_to_screen(self.x, self.y)

    def find_wind_deflection(self):
        """Finds the wind deflection vector for the cell."""
        self.wind_deflection = None

        # Creates the vector objects and makes a linear interpolation of them, scaling based on the total to crea
        for each_vector in self.region.keys():
            x_diff = each_vector.x - self.x
            y_diff = each_vector.y - self.y
            deflector = pygame.math.Vector2(x_diff, y_diff)
            if each_vector.altitude == 0.0:
                deflector.scale_to_length(0.0)
            else:
                deflector.scale_to_length(-each_vector.altitude * 0.1)
            if self.wind_deflection is None:
                self.wind_deflection = deflector
            else:
                self.wind_deflection += deflector

    def find_region(self, index, vor, vertices):
        """Finds the region for the cell, which are stored as a dictionary of the vertex objects
        that make up that region : the distance to that vertex."""
        self.region.clear()

        for vertex_index in vor.regions[vor.point_region[index]]:
            if vertex_index != -1:
                vert = vertices[vertex_index]
                dist = math.sqrt(abs(self.x - vert.x) + abs(self.y - vert.y))

                self.region[vert] = dist
                vert.generators[self] = dist

    def find_neighbors(self, index, vor, cells):
        """Finds the neighboring cells by looking them up in the voronoi diagram, then builds a dictionary where
        Cell Object: Distance Between Cells."""
        self.neighbors.clear()

        for index_a, index_b in vor.ridge_points:
            if index == index_a and index_b != -1 and index_b < len(cells):
                cell = cells[index_b]
            elif index == index_b and index_a != -1 and index_a < len(cells):
                cell = cells[index_a]
            else:
                continue
            self.neighbors[cell] = math.sqrt(abs(self.x - cell.x) + abs(self.y - cell.y))

    def find_lowest_vertex(self):
        """Finds the neighboring vertex with the lowest altitude, and stores it in self.lowest_vertex."""
        lowest_vertex = None
        lowest_alt_found = 2.0

        for vertex in self.region:
            if vertex.altitude < lowest_alt_found:
                lowest_vertex = vertex
                lowest_alt_found = vertex.altitude

        self.lowest_vertex = lowest_vertex

    def is_equatorial(self):
        """Returns True if the cell lies on the equator, otherwise returns false."""
        is_above = False
        is_below = False

        for each_vertex in self.region:
            if each_vertex.y > 0.0:
                is_above = True
            elif each_vertex.y < 0.0:
                is_below = True

        if is_above and is_below:
            return True
        else:
            return False

    def take_baro(self, baro_multiplier, source):
        """Given a wind_multiplier between 1 and 0, returns the transfer of pressure between this cell and the source"""
        delta = (self.pressure - source.pressure) * baro_multiplier * self.settings.baro_transfer_rate

        # Calculate the current temperature into a percentage of the min-max temps
        temps_as_percent = (self.temperature - self.settings.temps_lowest) / \
                           (self.settings.temps_equatorial - self.settings.temps_lowest)

        # High temps cause a lower pressure transfer rate (simulating low pressure zones caused by rising hot air)
        if temps_as_percent > 0.5:
            # The greater self pressure is relative to source_pressure, donate more pressure, inverse is also true
            delta *= (1 + self.pressure) / (1 + source.pressure + temps_as_percent)

        # Low temps cause higher pressure transfer rate (simulating high pressure zones caused by dense cool air)
        else:
            delta *= (1 + self.pressure + (1 - temps_as_percent)) / (1 + source.pressure)

        # Cap pressure at 1.0
        if source.pressure + source.pressure_delta + delta >= 1.0 and delta > 0.0:
            return 0

        # Floor pressure at -1.0
        if self.pressure + self.pressure_delta - delta <= -1.0 and delta < 0.0:
            return 0

        self.pressure_delta -= delta

        return delta

    def take_wind(self, wind_multiplier):
        """Given a wind_multiplier between 1 and 0, returns a segment of its vector,
        automatically reducing its own delta by the same amount."""

        delta = self.wind_vector * wind_multiplier * self.settings.wind_take_strength

        # Local pressure affects the transfer rate of the wind
        delta *= ((self.pressure + self.settings.baro_wind_effect + 1) / self.settings.baro_wind_effect + 1) * self.settings.baro_wind_effect

        self.wind_vector_delta -= delta

        return delta

    def take_humidity(self, humidity_multiplier, source):
        """Given a humidity_multiplier between 1 and 0, returns a number to be added to the source,
        automatically reducing its own delta by the same amount."""

        delta = (self.humidity + self.humidity_delta) * humidity_multiplier * \
                (1 - source.humidity + source.humidity_delta)

        return delta

    def take_temp(self, temp_multiplier, source):
        """Given a wind_multiplier between 1 and 0, returns the change in temperature affected on the source cell."""
        delta = ((self.temperature - self.settings.temps_lowest + self.temperature_delta) -
                 (source.temperature - self.settings.temps_lowest + source.temperature_delta)) * temp_multiplier

        # Set the bias toward heat/cold
        if delta >= 0.0:
            delta *= self.settings.temps_heat_bias
        else:
            delta /= self.settings.temps_heat_bias

        self.temperature_delta -= delta

        return delta

    def calculate_atmosphere_update(self, k_map):
        """Calculates updates to the local atmosphere based on wind speed, direction, temp and current pressure.
        Sends delta calls to neighbors, and sets internal deltas."""
        stg = self.settings

        # Cells poll their neighbors for valid wind angles, and call their delta functions
        for each_neighbor in self.neighbors.keys():

            x_adjust = self.x - each_neighbor.x
            y_adjust = self.y - each_neighbor.y
            angle_to_self = math.atan(x_adjust / y_adjust)

            # Prevent a divide by 0 error in angle calcs
            if each_neighbor.wind_vector.y == 0:
                if each_neighbor.wind_vector.x >= 0.0:
                    neighbor_wind_angle = 0
                else:
                    neighbor_wind_angle = math.pi
            else:
                neighbor_wind_angle = math.atan(each_neighbor.wind_vector.x /
                                                each_neighbor.wind_vector.y)
            neighbor_wind_angle = abs(neighbor_wind_angle - angle_to_self)

            # Check wind angle, create a multiplier and pass it to the individual atmosphere calcs in the cell
            if neighbor_wind_angle < stg.wind_critical_angle:
                wind_multiplier = (1 / stg.wind_critical_angle) * neighbor_wind_angle
                self.wind_vector_delta += each_neighbor.take_wind(wind_multiplier)
                self.pressure_delta += each_neighbor.take_baro(wind_multiplier, self)
                self.humidity_delta += each_neighbor.take_humidity(wind_multiplier, self)

            if neighbor_wind_angle < stg.temps_critical_angle:
                temps_multiplier = (1 / stg.temps_critical_angle) * neighbor_wind_angle
                self.temperature_delta += each_neighbor.take_temp(temps_multiplier, self)


        # Adds the equatorial jet stream and heating
        if abs(self.y + stg.season_ticks_modifier) < stg.atmo_tropics_extent:
            self.wind_vector_delta += stg.wind_streams_vector * \
                                      (abs(self.y + stg.season_ticks_modifier) / stg.atmo_tropics_extent)

            # Only heat if below the target temp for the equator
            if self.temperature < self.settings.temps_equatorial:
                self.temperature_delta += stg.temps_equatorial_rise * \
                                          (abs(self.y + stg.season_ticks_modifier) / stg.atmo_tropics_extent)

        # Same process but inverted for the arctic zones, jetstreams run backwards here
        elif abs(self.y + stg.season_ticks_modifier) > k_map.far_y - stg.atmo_arctic_extent:
            self.wind_vector_delta -= stg.wind_streams_vector * \
                                      ((abs(self.y + stg.season_ticks_modifier) - (k_map.far_y - stg.atmo_arctic_extent)) / stg.atmo_arctic_extent)
            self.temperature_delta -= stg.temps_arctic_cooling * \
                                      ((abs(self.y + stg.season_ticks_modifier) - (k_map.far_y - stg.atmo_arctic_extent)) / stg.atmo_arctic_extent)

        # Apply radiant atmospheric cooling
        self.temperature_delta -= stg.temps_natural_cooling

        # Apply the terrain deflection value generated by the cell, if it is above sea level
        if self.altitude > stg.wtr_sea_level:
            self.wind_vector_delta += self.wind_deflection * stg.wind_deflection_weight

        # Add rising water vapor over the oceans to both the humidity and pressure of the cell
        else:
            # Create a ratio of the current temp of the cell compared to the range of temps from max to freezing
            temps_multiplier = self.temperature + self.temperature_delta - stg.temps_freezing \
                               / (stg.temps_highest - stg.temps_freezing)
            self.pressure_delta += stg.wtr_baro_evap_rate * temps_multiplier
            self.humidity_delta += stg.wtr_humid_evap_rate * temps_multiplier

    def update_atmosphere(self):
        """Using the previously calculated data, update the atmosphere to reflect those changes."""

        # Wind
        self.wind_vector = self.wind_vector_delta
        self.wind_vector_delta = self.wind_vector

        # if the wind is stronger than the soft cap, it is reduced by wind_res * (wind speed - the soft cap)
        if self.wind_vector.magnitude() > self.settings.wind_soft_cap:
            modifier = self.wind_vector.magnitude() - self.settings.wind_soft_cap
            modifier *= self.settings.wind_resistance
            self.wind_vector.scale_to_length(self.wind_vector.magnitude() - modifier)

        # If still stronger than the hard cap, clamp it
        if self.wind_vector.magnitude() > self.settings.wind_hard_cap:
            self.wind_vector.scale_to_length(self.settings.wind_hard_cap)

        # Temps
        self.temperature += self.temperature_delta
        self.temperature_delta = 0

        # Apply altitude based cooling
        altct = self.settings.temps_alt_cooling_threshold    # alias

        if self.altitude > altct:
            self.temperature -= ((self.altitude - altct) / (1 - altct)) * self.settings.temps_alt_cooling

        if self.temperature < self.settings.temps_lowest:
            self.temperature = self.settings.temps_lowest
        elif self.temperature > self.settings.temps_highest:
            self.temperature = self.settings.temps_highest

        # Drop a percentage of moisture based on current altitude and temperature
        temps_mod = abs((self.temperature - self.settings.temps_freezing) - self.settings.temps_highest) / \
                    (self.settings.temps_highest - self.settings.temps_freezing)
        rainfall = (self.humidity + self.humidity_delta) * (2 * self.altitude) * temps_mod
        self.humidity_delta -= rainfall
        self.pressure_delta -= rainfall
        self.rainfall_this_year += rainfall * self.settings.wtr_rainfall_mod

        # Add rainfall to the watertable above sea level
        if self.altitude > self.settings.wtr_sea_level:
            self.watertable += rainfall * self.settings.wtr_rainfall_mod

        # Adjust the watertable relative to altitude
        watertable_delta = self.watertable - (self.watertable * self.altitude)
        drop_dist_mod = ((self.altitude - self.lowest_vertex.altitude)
                         / (self.altitude + 0.0001)) * self.settings.wtr_drop_dist_mod

        watertable_delta += drop_dist_mod

        self.watertable -= watertable_delta
        self.lowest_vertex.water_volume += watertable_delta

        # Moisture
        self.humidity += self.humidity_delta
        self.humidity_delta = 0.0

        # Clamp to 0 - 1
        if self.humidity > 1.0:
            self.humidity = 1.0
        elif self.humidity < 0.0:
            self.humidity = 0.0

        # Baro
        self.pressure += self.pressure_delta
        self.pressure_delta = 0.0
        if self.pressure >= 1.0:
            self.pressure = 0.999
        elif self.pressure <= -1.0:
            self.pressure = -0.999

    def write(self):
        """Method returns a string containing all the info about the cell for output into a textbox."""
        output = f"This cell is at {round(self.x, 3)}, {round(self.y, 3)}. * * "
        output += f"Local Altitude: {round(self.altitude, 3)} * Temperature: {round(self.temperature, 1)} * "
        output += f"Humidity {round(self.humidity, 2)} * Pressure: {round(self.pressure, 3)} * "
        output += f"Wind Angle: {round(math.atan(self.wind_vector.x / self.wind_vector.y), 3)}, "
        output += f"Magnitude: {round(self.wind_vector.magnitude(), 2)} * * "

        output += f"Rainfall this year: {round(self.rainfall_this_year, 2)} * "
        output += f"Rainfall last year: {round(self.rainfall_last_year, 2)} * * "

        output += f"Watertable Volume here: {round(self.watertable)} * "
        for iteration, key in enumerate(self.region.keys()):
            output += f"Vertex {iteration +1} water volume is: {round(key.water_volume)} * "

        return output

    def update(self, renderer):
        """The update function of the Cell as a Renderable object. Calls to pygame to draw the cell."""
        # If the polygon is None, then this item has never run before, calculate the polygon
        if self.polygon is None:
            project = self.settings.project_to_screen
            self.settings.db_print(f"calculating polygon for Cell at {self.x}, {self.y},"
                                   f"projects to {project(self.x, self.y, )}", detail=5)
            self.polygon = []

            # Takes each vertex and projects it to fit the screen size
            for each_vertex in self.region.keys():
                self.polygon.append(project(each_vertex.x, each_vertex.y))

            # Calculate the color
            self.find_color()

        # Refind color at the beginning of each season
        if self.settings.season_ticks_this_year == 0:
            self.find_color()
        elif self.settings.season_ticks_this_year == round(self.settings.season_ticks_per_year * 0.25):
            self.find_color()
        elif self.settings.season_ticks_this_year == round(self.settings.season_ticks_per_year * 0.5):
            self.find_color()
        elif self.settings.season_ticks_this_year == round(self.settings.season_ticks_per_year * 0.75):
            self.find_color()

        # Now we can render the shape if we are in the CellQ
        if renderer.label == 'cell':
            if self.altitude > self.settings.wtr_sea_level:
                # If render rainfall is on, mix the colors with the rainfall colors
                if self.settings.do_render_rainfall:
                    if self.rainfall_last_year == 0:
                        rainfall_mod = self.rainfall_this_year / 1000
                    else:
                        rainfall_mod = self.rainfall_last_year / 1000
                    if rainfall_mod > 1:
                        rainfall_mod = 1
                    rainfall_mod *= 255
                    pygame.draw.polygon(renderer.screen, ((self.cell_color[0] + rainfall_mod / 2) / 2,
                                                                  (self.cell_color[1] + rainfall_mod / 2) / 2,
                                                                  (self.cell_color[2] + rainfall_mod) / 2), self.polygon, 0)
                else:
                    pygame.draw.polygon(renderer.screen, self.cell_color, self.polygon, 0)
            else:
                pygame.draw.polygon(renderer.screen, renderer.settings.clr['ocean'], self.polygon, 0)

        # Render the wind vector if we are in the AtmosphereQ
        elif renderer.label == 'atmosphere':

            # Actual atmosphere rendering begins here
            temp_as_percent = (self.temperature - self.settings.temps_freezing) \
                              / abs(self.settings.temps_equatorial - self.settings.temps_freezing)
            if temp_as_percent > 1.0:
                temp_as_percent = 1.0
            if temp_as_percent < 0.0:
                temp_as_percent = 0.0

            pygame.draw.line(renderer.screen, (200 * temp_as_percent,
                                                       128 - abs(128 - 14 ** (1 + temp_as_percent)),
                                                       255 - 200 * temp_as_percent),
                             (self.ss_x, self.ss_y),
                             (self.ss_x + self.wind_vector.x * (self.settings.screen_size[0] / 35),
                              self.ss_y + self.wind_vector.y * (self.settings.screen_size[1] / 35)), 1)

            pressure_color = 32 + 111 * (self.pressure + 1)
            pygame.draw.circle(renderer.screen, (pressure_color, pressure_color, pressure_color),
                               (self.ss_x, self.ss_y), 3)

        # Render the border in the guiQ if self is the focus cell
        elif renderer.label == 'gui' and self.is_focus:
            pygame.draw.polygon(renderer.screen, (0, 0, 0), self.polygon, 3)


class Vertex(Renderable):
    """A single vertex defining a number of the voronoi ridges. Offers a point sample of the map where much of the
    terrain data is stored and maintained. Vertices along with the generator point are the constituents of a Cell."""

    def __init__(self, point):
        super().__init__()

        # Vertex data
        self.x, self.y = point
        self.neighbors = {}
        self.generators = {}

        # Associated Terrain data
        self.altitude = 0.0
        self.lowest_neighbor = None
        self.is_peak = False

        # Hydrology data
        self.water_volume = 0
        self.water_flow_ticks = []
        self.water_flow_rate = 0
        self.is_lake = False

        # Rendering data
        self.color = (0, 0, 0)
        self.ss_x = None
        self.ss_y = None

    def get_average_altitude(self, resolution):
        """Gets the average altitude of a vertex by looking at each neighbor and running this method recursively at one
        lower resolution. Resolution = the number of neighbors iteratively queried.
        Resolution:0 = the vertex's local altitude."""
        if resolution <= 0:
            return self.altitude
        else:
            total_altitude = 0.0
            for each_neighbor in self.neighbors.keys():
                total_altitude += each_neighbor.get_average_altitude(resolution - 1)
            total_altitude /= len(self.neighbors)
            return total_altitude

    def find_neighbors(self, index, vor, vertices):
        """Finds the neighboring vertices by looking them up in the voronoi diagram, then builds a dictionary where
        Vertex Object: Distance Between Vertices."""
        self.neighbors.clear()
        for index_a, index_b in vor.ridge_vertices:
            if index == index_a and index_b != -1:
                vertex = vertices[index_b]
            elif index == index_b and index_a != -1:
                vertex = vertices[index_a]
            else:
                continue
            distance = get_distance(self, vertex)
            self.neighbors[vertex] = distance

    def find_lowest_neighbor(self):
        """Finds the neighboring vertex with the lowest altitude among neighbors and self, and stores it in
        self.lowest_neighbor. Sets lowest_neighbor to None, if this vertex is the lower than all neighbors.
        Returns the lowest of the neighbors regardless of whether or not it is lower than the self."""
        lowest_neighbor = None
        lowest_alt_found = 2.0

        for neighbor in self.neighbors.keys():
            if neighbor.altitude < lowest_alt_found:
                lowest_neighbor = neighbor
                lowest_alt_found = neighbor.altitude

        if lowest_neighbor.altitude > self.altitude:
            self.lowest_neighbor = None
        else:
            self.lowest_neighbor = lowest_neighbor

        return lowest_neighbor

    def update_hydrology(self, settings):
        """Updates this vertex's hydrology."""
        tot_water_volume_delta = 0

        # If a generator has a lower watertable than this has water volume, add some of the volume to the generator
        for cell in self.generators.keys():
            if cell.watertable < self.water_volume and self.water_volume > cell.altitude * 1000:
                water_volume_delta = (self.water_volume - cell.watertable) * settings.wtr_reabsorption
                cell.watertable += water_volume_delta
                tot_water_volume_delta += water_volume_delta
                self.water_volume -= water_volume_delta

        # Check if there is a lower neighbor than self
        if self.lowest_neighbor:
            self.is_lake = False
            # Dump all water if you've encountered a sea cell
            for cell in self.generators.keys():
                if cell.altitude < settings.wtr_sea_level:
                    tot_water_volume_delta += self.water_volume
                    self.water_volume = 0

        # TODO Refactor this
        # Water flows toward the lowest point
            flow_delta = self.water_volume - self.lowest_neighbor.water_volume
            if flow_delta > 0.0:
                tot_water_volume_delta += flow_delta
                self.water_volume -= flow_delta
                self.lowest_neighbor.water_volume += flow_delta

        # Else, if water is above altitude become a basin lake
        elif self.water_volume > self.altitude * 1000 and self.altitude > settings.wtr_sea_level:
            self.is_lake = True
            next_lowest_n = self.find_lowest_neighbor()
            # If the water level rises above that of the lowest adjacent neighbor, dump into it
            if next_lowest_n.water_volume + (next_lowest_n.altitude * 1000) < \
                    self.water_volume + (self.altitude * 1000):
                water_volume_delta = (self.water_volume + (self.altitude * 1000)) - \
                                     (next_lowest_n.water_volume + (next_lowest_n.altitude * 1000))
                next_lowest_n.water_volume += water_volume_delta
                self.water_volume -= water_volume_delta
                tot_water_volume_delta += water_volume_delta

        # If above sea level
        if self.altitude > settings.wtr_sea_level:
            # Set flowrate variables
            self.water_flow_ticks.append(tot_water_volume_delta)
            if len(self.water_flow_ticks) > settings.wtr_flow_ticks_to_ave:
                self.water_flow_ticks.pop(0)
            self.water_flow_rate = round(sum(self.water_flow_ticks)/(len(self.water_flow_ticks) + 0.0001))

        # Below sea level
        else:
            self.is_lake = False
            self.water_volume = settings.wtr_sea_level * 1000
            if self.water_flow_ticks:
                self.water_flow_ticks.clear()
                self.water_flow_rate = 0

    def update(self, renderer):
        """Update call for the Vertex."""
        # Initialize the Vertex if it has never run before
        if self.ss_x is None:
            self.ss_x, self.ss_y = renderer.settings.project_to_screen(self.x, self.y)
            self.color = (255 * self.altitude, 255 * self.altitude, 255 * self.altitude)

        if self.altitude > renderer.settings.wtr_sea_level and renderer.settings.do_render_altitudes:
            pygame.draw.circle(renderer.screen, self.color, (self.ss_x, self.ss_y), 3)

        # Render rivers
        if self.lowest_neighbor and renderer.settings.do_render_rivers:
            if self.is_lake:
                pygame.draw.circle(renderer.screen, renderer.settings.clr['river'],
                                   (self.ss_x, self.ss_y), round(self.water_volume/1000))
            elif self.lowest_neighbor.ss_x:
                if self.water_flow_rate > renderer.settings.wtr_min_flow_to_render:
                    river_width = 1 + round(self.water_flow_rate/renderer.settings.wtr_river_flow_as_width)
                else:
                    river_width = 0
                if river_width > renderer.settings.wtr_max_river_render_width:
                    river_width = renderer.settings.wtr_max_river_render_width
                pygame.draw.line(renderer.screen, renderer.settings.clr['river'],
                                 (self.ss_x, self.ss_y), (self.lowest_neighbor.ss_x, self.lowest_neighbor.ss_y),
                                 river_width)


class Path:
    """Paths contains a list of a line of Vertices and or Cells. This is used for many functions of the generator."""

    def __init__(self, starting_position):
        # Path variables
        self.path = [starting_position]
        self.total_distance = 0.0

        # State variables
        self.depth = 0  # Used by the generator for a number of functions depending on the particular Path
        self.open = True

    def add_next(self, location):
        """Add a given cell or vertex object as the next item in the list."""
        self.total_distance += get_distance(self.path[-1], location)
        self.path.append(location)

    def add_endpoint(self, endpoint, limit=1.0):
        """Adds an endpoint by populating the path list as it travels there.
        Right now only supports a straight line of vertices."""
        best_vertex = None
        while best_vertex != endpoint and self.total_distance < limit:
            shortest_dist = 100.0

            for each_vertex in self.path[-1].neighbors.keys():
                this_distance = get_distance(each_vertex, endpoint)
                if this_distance < shortest_dist:
                    shortest_dist = this_distance
                    best_vertex = each_vertex
                else:
                    continue
            if len(self.path) > 2 and best_vertex == self.path[-2].neighbors.keys():
                break
            self.add_next(best_vertex)

    def length(self):
        """Returns the number of nodes in the path."""
        return len(self.path)

    def clear(self):
        """Clears out unused or soon-to-be reused paths."""
        self.path.clear()
        self.total_distance = 0.0


def get_distance(location1, location2):
    """Used to get the distance between two objects with valid .x and .y co-ordinates set up."""
    return math.sqrt(abs(location1.x - location2.x) + abs(location1.y - location2.y))
