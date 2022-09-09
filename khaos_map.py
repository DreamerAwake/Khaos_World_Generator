import random

from cells import *
import numpy
import scipy.spatial as sptl


class Settings:
    """Contains the settings for the KhaosMap."""
    def __init__(self):
        self.map = None

        # Set the random seed
        self.seed = 35
        numpy.random.seed(self.seed)
        random.seed(self.seed)

        # Program settings
        self.debug_console = True
        self.debug_detail = 4       # All debug console calls with a LESSER debug detail will show. Range of (1-5)

        # Pygame settings
        self.screen_size = (1200, 900)
        self.do_render_vertices = False

        # Voronoi generation settings
        self.total_cells = 3000
        self.relax_passes = 5

        # Terrain generation settings
        self.tect_plates_min = 12    # The minimum number of tectonic plates used in altitude generation
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
        self.mtn_ridges_min = 10         # Sets the minimum number

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


class KhaosMap:
    """This map contains a set of objects describing a voronoi diagram produced from scipy.spatial.Voronoi."""
    def __init__(self):
        # Instantiates a settings object
        self.settings = Settings()
        self.settings.map = self
        dbprint = self.settings.db_print

        # Generates the initial voronoi object and runs the lloyds relaxation to regularize the cell sizes.
        dbprint("Generating voronoi diagram...")
        self.voronoi = self.gen_vor()

        # Uses the voronoi diagram to produce the Cell and Vertex objects for the map.
        dbprint("Creating map objects...")
        self.cells, self.vertices = self.gen_map_objs(self.voronoi)

        # Find the furthest x and y coordinates in the voronoi at this point, store them for later.
        self.far_x, self.far_y = self.get_furthest_members()

        # Generate the altitudes for the vertices and the cells
        dbprint("Beginning altitude generation...")
        dbprint("Locating tectonic plates...", detail=2)
        plate_centers = self.get_plate_centers()   # Finds the plates used for altitude generation
        slopes = self.get_plate_slopes(plate_centers)

        dbprint("Deriving altitudes...", detail=2)
        self.set_altitudes(plate_centers, slopes)

        dbprint("Smoothing vertex altitudes...", detail=3)
        for iteration in range(0, self.settings.tect_smoothing_repetitions):
            self.smooth_altitudes(self.settings.tect_smoothing_resolution)

        dbprint("Pathing mountain ranges...", detail=2)
        number_of_ridges = random.randint(self.settings.mtn_ridges_min, self.settings.mtn_ridges_max)
        peaks = self.get_peaks()
        self.ridges = []        # TODO remove this debug variable
        for iteration in range(0, number_of_ridges):
            self.ridges += self.gen_single_ridge(peaks)

        dbprint("Extrapolating altitudes to cells...", detail=3)
        for each_cell in self.cells:
            each_cell.find_altitude()

        self.peaks = self.get_peaks()  # TODO remove this debug variable

        # TODO Wind patterns, rainfall
        # TODO Temperature

    def gen_vor(self):
        """Generates a voronoi diagram and passes it through several relax iterations as decided in the settings."""
        # Initial generation, produces the random list, then adds 8 distant points to bound the cells properly
        points = numpy.random.uniform(-1.0, 1.0, (self.settings.total_cells, 2))
        distant_points = [[2.0, 0.0], [0.0, 2.0],
                          [-2.0, 0.0], [0.0, -2.0],
                          [2.0, 2.0], [-2.0, -2.0],
                          [-2.0, 2.0], [2.0, -2.0]]
        points = numpy.append(points, distant_points, axis=0)

        # Make the first voronoi diagram
        vor = sptl.Voronoi(points)

        # Relax passes
        for passes in range(0, self.settings.relax_passes):
            vor = lloyds_relax(vor)

        return vor

    def gen_map_objs(self, vor):
        """Returns a list of Cell objects and a list of Vertex objects, drawn from the provided voronoi diagram."""
        cells = []
        vertices = []

        # Fills both of the lists with objects which can then be further worked with
        for each_point in vor.points:
            # Ignores the bounding points added in the generation step
            if abs(each_point[0]) == 2.0 or abs(each_point[1]) == 2.0:
                continue
            else:
                cells.append(Cell(each_point))

        for each_vertex in vor.vertices:
            vertices.append(Vertex(each_vertex))

        # Runs the functions to attach vertices to their regions
        for index, each_cell in enumerate(cells):
            each_cell.find_region(index, vor, vertices)
            each_cell.find_neighbors(index, vor, cells)

        for index, each_vertex in enumerate(vertices):
            each_vertex.find_neighbors(index, vor, vertices)

        return cells, vertices

    def gen_single_ridge(self, peaks):
        """Creates a high forking mountain ridge on the altitude map."""
        dbprint = self.settings.db_print

        # Gets a random peak to start with, sets its altitude to the maximum, minus a factor
        random_peak = peaks[random.randrange(0, len(peaks))]
        new_alt = 1.0 - random.random() * self.settings.mtn_peak_reduction_factor

        # Make sure not to accidentally reduce the height
        if random_peak.altitude < new_alt:
            random_peak.altitude = new_alt

        dbprint(f"Adding peak at {random_peak.x}, {random_peak.y}, ALT: {random_peak.altitude}", detail=4)

        # Create lists for pathing
        total_nodes = 0
        opened = [random_peak]
        closed = []

        # Begin looping through the path lists
        while opened and total_nodes < self.settings.mtn_max_node_chain:

            for each_vertex in opened:

                # Ready the current vertex for closing before the next pass starts
                closed.append(each_vertex)

                # Decide if the ridge will fork
                if random.random() < self.settings.mtn_fork_chance:
                    dbprint(f"Forking at {each_vertex.x}, {each_vertex.y}")
                    self.get_next_ridge(each_vertex, opened, closed)
                    self.get_next_ridge(each_vertex, opened, closed)
                    total_nodes += 2
                else:
                    self.get_next_ridge(each_vertex, opened, closed)
                    total_nodes += 1

                if total_nodes > self.settings.mtn_max_node_chain:
                    break

            # Remove closed vertices from open
            for each_vertex in closed:
                if each_vertex in opened:
                    opened.remove(each_vertex)

        return closed

    def get_furthest_members(self):
        """Used to obtain the most distant members of the voronoi diagram.
        After relaxation, these can be quite far past 1.0."""
        furthest_x = 0.0
        furthest_y = 0.0

        for each_cell in self.cells:
            if each_cell.x > furthest_x:
                furthest_x = each_cell.x
            if each_cell.y > furthest_y:
                furthest_y = each_cell.y

        return furthest_x, furthest_y

    def get_next_ridge(self, vertex, opened, closed):
        """Finds the tallest neighbor of a vertex for the mountain range builder's pathfinder."""
        # Find next tallest neighbor to form the next portion of the ridge
        tallest_neighbor_alt = -0.1
        tallest_neighbor = None
        for each_neighbor in vertex.neighbors.keys():
            # Ignore vertices already found by the ridge builder
            if each_neighbor not in closed and each_neighbor not in opened:
                if each_neighbor.altitude > tallest_neighbor_alt:
                    tallest_neighbor_alt = each_neighbor.altitude
                    tallest_neighbor = each_neighbor

        # If something is found, average its current altitude with the peak's altitude, add it to open
        if tallest_neighbor:
            tallest_neighbor.altitude = vertex.altitude * self.settings.mtn_peak_weight + \
                                        tallest_neighbor.altitude * abs(self.settings.mtn_peak_weight - 1.0)
            opened.append(tallest_neighbor)

    def get_peaks(self):
        """Finds the vertices that have higher altitudes than all of their neighbors,
        sets is_peak internally and records them in a list."""
        peaks = []
        for each_vertex in self.vertices:
            each_vertex.is_peak = True
            for each_neighbor in each_vertex.neighbors:
                if each_neighbor.altitude > each_vertex.altitude:
                    each_vertex.is_peak = False
                    break
            if each_vertex.is_peak:
                peaks.append(each_vertex)

        return peaks

    def get_plate_centers(self):
        """Used to find the central vertices of the tectonic plates used by the altitude/mountain generator."""

        number_of_plates = random.randrange(self.settings.tect_plates_min, self.settings.tect_plates_max)
        plates = []

        for iteration in range(0, number_of_plates):
            rand_index = random.randrange(0, len(self.vertices))
            if not plates:
                plates.append(self.vertices[rand_index])
            else:
                # Check that the distance between plates meets the minimum requirements, or choose a new one
                far_enough = False
                attempts = 0
                while not far_enough and attempts < self.settings.tect_attempt_to_place:
                    attempts += 1
                    far_enough = True
                    for each_plate in plates:
                        if get_distance(self.vertices[rand_index], each_plate) < self.settings.tect_min_dist:
                            far_enough = False
                            rand_index = random.randrange(0, len(self.vertices))
                            break
                if far_enough:
                    plates.append(self.vertices[rand_index])

        return plates

    def get_plate_slopes(self, plates):
        """Gets the slopes for each tectonic plate used by the height generator"""

        slopes = []
        for iteration in range(0, len(plates)):
            tilt_inversion = random.random()

            if tilt_inversion < 0.5:
                rand_x = random.random()
            else:
                rand_x = -random.random()

            if tilt_inversion < 0.25 or tilt_inversion > 0.75:
                rand_y = random.random()
            else:
                rand_y = -random.random()

            slopes.append((rand_x, rand_y))

        return slopes

    def smooth_altitudes(self, resolution):
        """Smooths out the altitudes on the map by finding an average of the surrounding vertices to a sample distance
        equal to the resolution. Builds a list of smoothed altitudes first, then applies them to prevent changes from
        affecting the results of further calculations."""

        smoothed_altitudes = []
        for each_vertex in self.vertices:
            smoothed_altitudes.append(each_vertex.get_average_altitude(resolution))

        for iteration in range(0, len(self.vertices)):
            self.vertices[iteration].altitude = smoothed_altitudes[iteration]

    def set_altitudes(self, plates, slopes):
        """Uses the tectonic plates to assign altitudes to each vertex.
        For each vertex assigns an altitude based on its plate and slope."""
        x_dist = 0
        y_dist = 0

        for each_vertex in self.vertices:
            shortest_dist = 3.0
            best_plate_index = None

            # Finds the closest plate
            for iteration in range(0, len(plates)):

                # Finds the distances of both axes from the center point of the plate
                x_dist = each_vertex.x - plates[iteration].x
                y_dist = each_vertex.y - plates[iteration].y

                total_dist = math.sqrt(abs(x_dist**2) + abs(y_dist**2))

                # Determines if we've found the nearest plate so far
                if total_dist < shortest_dist:
                    shortest_dist = total_dist
                    best_plate_index = iteration

            # Applies the slope to the centerpoint distances
            x_alt_delta = x_dist * slopes[best_plate_index][0]
            y_alt_delta = y_dist * slopes[best_plate_index][1]

            # Calculates the final altitude
            each_vertex.altitude = x_alt_delta + y_alt_delta + self.settings.tect_final_alt_mod

            # If the altitude rises over 1.0 drift from that point is inverted
            if each_vertex.altitude > 1.0:
                each_vertex.altitude = -1 * each_vertex.altitude + 1.0
            # 0.0 is simply an altitude floor
            if each_vertex.altitude < 0.0:
                each_vertex.altitude = 0.0


def lloyds_relax(vor):
    """Applies Lloyd's algorithm to the given voronoi diagram, finding the centroid of each region and then passing
    those to scipy to re-create a relaxed diagram."""
    centroids = None
    for each_point in enumerate(vor.points):
        if centroids is not None and abs(each_point[1][0]) > 1.0 \
                or centroids is not None and abs(each_point[1][1]) > 1.0:
            centroids = numpy.append(centroids, [each_point[1]], axis=0)
        else:
            region_vertices = None
            for each_index in vor.regions[vor.point_region[each_point[0]]]:
                if region_vertices is None:
                    region_vertices = numpy.array([vor.vertices[each_index]])
                else:
                    region_vertices = numpy.append(region_vertices, [vor.vertices[each_index]], axis=0)

            centroid = (numpy.mean(region_vertices[0:, 0]), numpy.mean(region_vertices[0:, 1]))

            if centroids is None:
                centroids = numpy.array([centroid])
            else:
                centroids = numpy.append(centroids, [centroid], axis=0)
    return sptl.Voronoi(centroids)


if __name__ == "__main__":
    new_map = KhaosMap()
