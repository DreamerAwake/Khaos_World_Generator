import pygame.draw

from render import *

import math


class Cell(Renderable):
    """Stores information about a single cell, which has a generator point treated as a pseudo-center and a region
    formed of shared edge vertices with its neighbor cells."""
    def __init__(self, point):
        super().__init__()

        # Cell data
        self.x, self.y = point
        self.ss_x = None
        self.ss_y = None
        self.region = {}
        self.neighbors = {}

        # Associated Terrain data
        self.altitude = 0.0
        self.wind_deflection = None

        # Rendering Settings
        self.polygon = None
        self.cell_color = (0, 64, 0)

    def find_altitude(self):
        """Finds the average altitude of the vertices and makes it the total altitude of the cell"""
        self.altitude = 0.0

        for each_vertex in self.region.keys():
            self.altitude += each_vertex.altitude

        self.altitude /= len(self.region)

    def find_screen_space(self, settings):
        """Finds the x and y of the cell on the screen."""
        self.ss_x, self.ss_y = settings.project_to_screen(self.x, self.y)

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
        """Finds the region for the cell, which are stored as the vertex objects that make up that region."""
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

    def update(self, surface, settings):
        """The update function of the Cell as a Renderable object. Calls to pygame to draw the cell."""
        # If the polygon is None, then this item has never run before, calculate the polygon
        if self.polygon is None:
            project = settings.project_to_screen
            settings.db_print(f"calculating polygon for Cell at {self.x}, {self.y},"
                              f"projects to {project(self.x, self.y, )}", detail=5)
            self.polygon = []

            # Takes each vertex and projects it from a range of -1.0 to 1.0 to fit the screen size
            for each_vertex in self.region.keys():
                self.polygon.append(project(each_vertex.x, each_vertex.y))

            # Calculate the color
            self.cell_color = (200 * self.altitude, 127 + 128 * self.altitude, 200 * self.altitude)

        # Now we can render the shape
        if self.altitude > settings.wtr_sea_level:
            pygame.draw.polygon(surface, self.cell_color, self.polygon, 0)
        else:
            pygame.draw.polygon(surface, (0, 64, 196), self.polygon, 0)

        # Also render the wind redirection vector
        # pygame.draw.line(surface, (100, 0, 0), (self.ss_x, self.ss_y), (self.ss_x + self.wind_deflection.x * 1000, self.ss_y + self.wind_deflection.y * 1000), 2)
        # pygame.draw.circle(surface, (0, 0, 0), (self.ss_x, self.ss_y), 3)


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
        self.is_peak = False

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

    def update(self, surface, settings):
        """Update call for the Vertex."""
        if self.ss_x is None:
            self.ss_x, self.ss_y = settings.project_to_screen(self.x, self.y)
            self.color = (255 * self.altitude, 255 * self.altitude, 255 * self.altitude)

        if self.altitude > settings.wtr_sea_level:
            pygame.draw.circle(surface, self.color, (self.ss_x, self.ss_y), 3)


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
