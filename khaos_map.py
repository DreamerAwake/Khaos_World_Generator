import random

from cells import *
import numpy
import scipy.spatial as sptl


class Settings:
    """Contains the settings for the KhaosMap."""
    def __init__(self):
        self.map = None

        # Set the random seed
        self.seed = 26
        numpy.random.seed(self.seed)
        random.seed(self.seed)

        # Program settings
        self.debug_console = True
        self.debug_detail = 3       # All debug console calls with a LESSER debug detail will show. Range of (1-5)

        # Pygame settings
        self.screen_size = (1200, 900)

        # Voronoi generation settings
        self.total_cells = 3000
        self.relax_passes = 6

        # Terrain generation settings
        self.mtn_height_skew = 0.9  # Skews the generation of mountains toward being taller or shorter, on average
        self.mtn_coverage = 0.12    # Coverage determines how much of the map should be targeted to be mountaintops.
        self.mtn_continuity = 1.1  # Continuity determines how long mountain ridges tend to be.
        self.mtn_forks = 0.4       # Rate at which the mountain ridges tend to fork into sub-ridges
        self.mtn_max_forks = 6      # Maximum number of forks allowed, to prevent infinite loops
        self.mtn_ridge_grade = -0.7  # The grade of the mountain ridge found through the get_altitude function
        self.mtn_slope_grade = 1.1   # The grade of the mountain slopes
        self.mtn_drop_dist_mod = 6   # Higher numbers allow for longer mountain ranges

        self.wtr_sea_level = 0.05    # The sea level of the terrain, all lower points will be underwater

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
        dbprint("Finding altitudes...")
        self.gen_vertex_altitudes()

        dbprint("Extrapolating altitudes...")
        for each_cell in self.cells:
            each_cell.find_altitude()

        # TODO Wind patterns, rainfall
        # TODO Temperature

    def gen_altitude_ridges(self):
        """Creates the mountain ridge paths used by the altitude generator."""
        alt_ridges = []
        total_mountain_nodes = 0
        all_closed = False

        while total_mountain_nodes / len(self.vertices) < self.settings.mtn_coverage:
            # Debug console printout
            self.settings.db_print(f"Total MTN Nodes: {total_mountain_nodes}, "
                                   f"Target Nodes = {len(self.vertices) * self.settings.mtn_coverage}, - "
                                   f"{total_mountain_nodes/len(self.vertices) * self.settings.mtn_coverage}%", detail=4)

            # Create a new mountain ridge
            self.create_new_mtn_ridge(alt_ridges)
            total_mountain_nodes += alt_ridges[-1].length()

            # Work through the unforked ridges and fork them at random intervals, start with the new one just added
            current_ridge = alt_ridges[-1]

            while not all_closed:
                # Fork the current ridge
                self.settings.db_print(f"Adding fork to ridge beginning at "
                                       f"{current_ridge.path[0].x}, {current_ridge.path[0].y}", detail=5)
                for each_vertex in current_ridge.path:
                    if random.random() < self.settings.mtn_forks and current_ridge.depth < self.settings.mtn_max_forks:
                        # Make the new ridges shorter based on the number of previous forks
                        self.create_new_mtn_ridge(alt_ridges, each_vertex,
                                                  1 / (current_ridge.depth + 1))
                        alt_ridges[-1].depth = current_ridge.depth + 1
                        total_mountain_nodes += alt_ridges[-1].length()

                # Find an unforked ridge, otherwise, kick back to making new ridges
                all_closed = True

                for ridge in alt_ridges:
                    if ridge.open:
                        # Make an open ridge into the current one, close it and make the forking process continue.
                        current_ridge = ridge
                        current_ridge.open = False
                        all_closed = False
                        break
        return alt_ridges

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

    def gen_vertex_altitudes(self):
        """Given the vertex list, this function gives them all altitudes.
        First, it finds several mountain ridges and then projects them based on a few characteristics found in the
        settings class. Then it creates a number of plate structures which simulate continental plains.
        In the end, each vertex has an altitude based on a projection from the nearest ridge point."""

        # Create the ridge paths used to model mountains
        mtn_ridges = self.gen_altitude_ridges()

        # We now begin applying altitudes to our ridge points.
        # Set the very first ridge node to 1.0
        mtn_ridges[0].path[0].altitude = 1.0

        for each_ridge in mtn_ridges:
            for vertex_path_index, ridge_point in enumerate(each_ridge.path):
                # Skip vertices that already have altitudes, which will have been set by a parent ridge or the 1.0 point
                if ridge_point.altitude != 0.0:
                    continue
                # If the current location is the first entry in a path and 0.0, then we give it a random altitude
                elif vertex_path_index == 0:
                    # Take (random range 0.0-1.0 + the mtn_height_skew) * the mtn_height_skew
                    ridge_point.altitude = \
                        (random.random() + self.settings.mtn_height_skew) * self.settings.mtn_height_skew

                # Otherwise we assign a height based on the drop from the previous ridge point
                else:
                    ridge_point.altitude = \
                        get_altitude_drop(each_ridge.path[vertex_path_index - 1].altitude,
                                          each_ridge.path[vertex_path_index - 1].neighbors[ridge_point]
                                          / self.settings.mtn_drop_dist_mod,
                                          self.settings.mtn_ridge_grade)

        # Now we will calculate each vertex altitude on the map
        # First we create a list containing all the unique altitude ridge vertices
        current_vertices = []
        next_vertices = []

        for each_ridge in mtn_ridges:
            for each_vertex in each_ridge.path:
                if each_vertex not in current_vertices:
                    current_vertices.append(each_vertex)

        # Begin the crawler loop
        while current_vertices:
            # For each vertex adjacent to a current vertex we calculate the height drop.
            for each_vertex in current_vertices:
                for each_neighbor in each_vertex.neighbors.keys():
                    new_alt = get_altitude_drop(each_vertex.altitude,
                                                each_vertex.neighbors[each_neighbor], self.settings.mtn_slope_grade)
                    # If the altitude calculated is greater, adjust the neighbor's altitude and add it to the next list
                    if new_alt > each_neighbor.altitude:
                        each_neighbor.altitude = new_alt
                        next_vertices.append(each_neighbor)

            # Once done processing the list, clear it, make it a copy of the next, then clear that as well
            current_vertices.clear()
            current_vertices = next_vertices.copy()
            next_vertices.clear()

            # If there are no more vertices lower than the last pass, we're done and the list.clear() will end the loop

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

    def create_new_mtn_ridge(self, mtn_ridges, starting_point=None, continuity_mod=1.0):
        """Creates a new mountain ridge for the altitude generator.
        If not provided a starting point, it finds a random one."""

        if starting_point is None:
            starting_point = self.vertices[random.randrange(0, len(self.vertices))]

        self.settings.db_print(f"Creating new ridge at {starting_point.x}, {starting_point.y}", detail=5)

        # Place the ridge path in the provided list
        mtn_ridges.append(Path(starting_point))

        # Find a suitable endpoint for the new random ridge based on mtn_continuity
        next_random_point = None
        number_of_passes = 0
        self.settings.db_print(f"Entering random endpoint loop", detail=5)
        while next_random_point is None and number_of_passes < 15:
            next_random_point = self.vertices[random.randrange(0, len(self.vertices))]
            if get_distance(next_random_point, mtn_ridges[-1].path[-1]) < self.settings.mtn_continuity * continuity_mod:
                mtn_ridges[-1].add_endpoint(next_random_point)
                self.settings.db_print(f"Endpoint at {next_random_point.x}, {next_random_point.y}", detail=5)
            else:
                next_random_point = None
                number_of_passes += 1
                self.settings.db_print(f"Fork generation iterations = {number_of_passes}", detail=5)
                if number_of_passes == 15:
                    self.settings.db_print("Fork generation reached max iterations, moving on...", detail=4)


def lloyds_relax(vor):
    """Applies Lloyd's algorithm to the given voronoi diagram, finding the centroid of each region and then passing
    those to scipy to re-create a relaxed diagram."""
    centroids = None
    for each_point in enumerate(vor.points):
        if centroids is not None and abs(each_point[1][0]) > 1.0 or centroids is not None and abs(each_point[1][1]) > 1.0:
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


def get_altitude_drop(init_altitude, distance, grade):
    """Given the source's distance from a point, that point's altitude, and a grade,
    finds the altitude lost over that distance, then returns the new altitude."""
    # First find the converted starting_altitude
    # Then, add the distance between the two points
    new_dist = convert_dist_alt(init_altitude, grade) + distance

    if new_dist > 1.0:
        new_dist = 1.0

    # return the conversion back to altitude as the new altitude
    return convert_dist_alt(new_dist, grade)


def convert_dist_alt(x, grade, scale=1.0):
    """y = (b - x) / (xg + 1); where b is a scalar for the range of the numbers produced, and g is the grade.
    Graph it for a better idea of what's going on here."""
    result = (scale-x)/((x * grade) + 1)
    return result


if __name__ == "__main__":
    new_map = KhaosMap()
