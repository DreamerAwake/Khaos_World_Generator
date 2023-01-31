import random
import math
import pygame
from dataclasses import dataclass


class Heightmap:
    """Generates the heightmap for the world using techtonics via vector force calculations.
    Requires either both a resolution and a plate number, or a pre-built cell array to be initialized."""

    def __init__(self, resolution_tuple=(10, 10), number_of_plates=10, use_map=None):
        # If passed a tectonic cell array, use that instead of generating your own map.
        if use_map is not None:
            self.map = use_map
        # Creates the map array of Tectonic Cells used for the calculations
        else:
            self.map = init_map(resolution_tuple, number_of_plates)

    def __getitem__(self, item):
        if type(item) is tuple:
            return self.map[item[0]][item[1]]
        else:
            return self.map[item]

    def __iter__(self):
        return self.map

    def __len__(self):
        return len(self.map)

    def copy(self):
        """Returns an identical but unlinked Heightmap with the exact same properties."""
        new_map = []
        for each_column in self.map:

            this_column = []
            for each_cell in each_column:
                this_column.append(TectonicCell(each_cell.vector.copy(), each_cell.density, altitude=each_cell.altitude))

            new_map.append(tuple(this_column))

        return Heightmap(use_map=tuple(new_map))

    def match(self, heightmap):
        """Makes this map match the given heightmap by copying the settings from its Cells over its own."""
        if len(heightmap) != len(self.map) or len(heightmap[0]) != len(self.map[0]):
            raise IndexError

        for x in range(0, len(heightmap)):
            for y in range(0, len(heightmap[0])):
                self.map[x][y].vector.xy = heightmap[x][y].vector.xy
                self.map[x][y].altitude = heightmap[x][y].altitude

    def get_surface(self):
        """Returns a pygame surface that reflects the values of the heightmap."""
        heightmap_surface = pygame.Surface((len(self.map), len(self.map[0])))

        heightmap_pixel_array = pygame.PixelArray(heightmap_surface)

        # Assign a color to each pixel
        for x in range(0, len(self.map)):
            for y in range(0, len(self.map[0])):
                """-Color by vector/altitude-
                
                # r = horizontal vector
                r = (self.map[x][y].vector.x + 1) * 127
                # g = vertical vector
                g = (self.map[x][y].vector.y + 1) * 127
                # b = altitude
                b = self.map[x][y].altitude * 255"""

                r, g, b = self.map[x][y].altitude * 255, self.map[x][y].altitude * 255, self.map[x][y].altitude * 255
                if r < 100:
                    r, g = 0, 0

                # Bound each value
                if r < 0:
                    r = 0
                elif r > 255:
                    r = 255
                if g < 0:
                    g = 0
                elif g > 255:
                    g = 255
                if b < 0:
                    b = 0
                elif b > 255:
                    b = 255

                # Color the pixel
                heightmap_pixel_array[x, y] = (r, g, b)

        heightmap_pixel_array.close()

        return heightmap_surface

class DeformCrawler:
    """Crawls over all of the tectonic cells and issues them updates based on their current state. Can crawl
    asynchronously with rendering to maintain framerate even under high processing strain. wrap_horizontal determines
    if the crawler considers cells in the leftmost and rightmost columns to be adjacent to one another on their
    out-facing side."""
    def __init__(self, parent_heightmap, wrap_horizontal=False, deform_weight=4.0, deform_speed=0.1):
        self.parent_map = parent_heightmap  # The source map to be deformed
        self.deform_map = self.parent_map.copy()    # The internal map for storing deformations mid-cycle

        # Functional settings
        self.wrap_x = wrap_horizontal
        self.deform_weight = deform_weight
        self.deform_speed = deform_speed

        # Crawler tracking settings
        self.resolution_x, self.resolution_y = len(self.parent_map), len(self.parent_map[0])
        self.x, self.y = 0, 0

    def deform_accretion(self, donator_xy, target_xy):
        """Accretion is the process whereby the donator cell places a portion of its vector and altitude into the
        target. Higher densities transfer slower, higher relative altitudes and vectors transfer more quickly."""

        donator_density = self.parent_map[donator_xy].density
        donator_altitude = self.parent_map[donator_xy].altitude
        donator_vector = self.parent_map[donator_xy].vector.copy()

        target_altitude = self.parent_map[donator_xy].altitude
        target_magnitude = self.parent_map[target_xy].vector.length()

        transfer_rate = ((donator_altitude + donator_vector.length()) / (target_altitude + target_magnitude + 0.000001)) - donator_density

        transfer_rate = get_sigmoid_function(transfer_rate, slope=self.deform_weight) * self.deform_speed

        # Set the current cell effects on the deform map
        self.deform_map[donator_xy].density = get_capped_number(self.deform_map[donator_xy].density - donator_density * transfer_rate, minimum_output=0.0, maximum_output=1.0)
        self.deform_map[donator_xy].altitude = get_capped_number(self.deform_map[donator_xy].altitude - donator_altitude * transfer_rate, minimum_output=0.0, maximum_output=1.0)
        self.deform_map[donator_xy].vector -= donator_vector * transfer_rate
        if self.deform_map[donator_xy].vector.length() > 1.0:
            self.deform_map[donator_xy].vector.normalize_ip()

        # Set the target effects on the deform map.
        self.deform_map[target_xy].density = get_capped_number(self.deform_map[target_xy].density + donator_density * transfer_rate, minimum_output=0.0, maximum_output=1.0)
        self.deform_map[target_xy].altitude = get_capped_number(self.deform_map[target_xy].altitude + donator_altitude * transfer_rate, minimum_output=0.0, maximum_output=1.0)
        self.deform_map[target_xy].vector += donator_vector * transfer_rate
        if self.deform_map[target_xy].vector.length() > 1.0:
            self.deform_map[target_xy].vector.normalize_ip()

    def deform_collision(self, collider_a_xy, collider_b_xy, density_deviance=0.1):
        """When two vectors collide, if they have a roughly equivalent density, they buckle and begin to rise up.
        Otherwise, the denser plate subducts, granting much of its altitude to the less dense plate."""

        # Reflect and incorporate a portion of the force vector
        a_magnitude = self.parent_map[collider_a_xy].vector.length()
        a_altitude = self.parent_map[collider_a_xy].altitude
        b_magnitude = self.parent_map[collider_b_xy].vector.length()
        b_altitude = self.parent_map[collider_b_xy].altitude

        if b_magnitude > 0.001:
            add_to_a_vector = self.parent_map[collider_a_xy].vector.reflect(self.parent_map[collider_b_xy].vector)
            vector_reflect_rate = get_sigmoid_function(a_magnitude / b_magnitude, slope=self.deform_weight, x_offset=1) * self.deform_speed
        else:
            add_to_a_vector = pygame.Vector2(0, 0)
            vector_reflect_rate = get_sigmoid_function(a_magnitude / 0.00001, slope=self.deform_weight, x_offset=1) * self.deform_speed

        if a_magnitude > 0.001:
            add_to_b_vector = self.parent_map[collider_b_xy].vector.reflect(self.parent_map[collider_a_xy].vector)
        else:
            add_to_b_vector = pygame.Vector2(0, 0)

        self.deform_map[collider_a_xy].vector += add_to_a_vector * vector_reflect_rate
        if self.deform_map[collider_a_xy].vector.length() > 1.0:
            self.deform_map[collider_a_xy].vector.normalize_ip()
        self.deform_map[collider_b_xy].vector += add_to_b_vector * vector_reflect_rate
        if self.deform_map[collider_b_xy].vector.length() > 1.0:
            self.deform_map[collider_b_xy].vector.normalize_ip()

        # Now determine if there is buckling or subduction occuring based on relative cell density
        if abs(self.parent_map[collider_a_xy].density - self.parent_map[collider_b_xy].density) < density_deviance:  # Buckle

            # Raise the height of the cells
            a_altitude = get_capped_number(a_magnitude + b_magnitude - (a_altitude * 2), minimum_output=0.0) * self.deform_speed
            b_altitude = get_capped_number(a_magnitude + b_magnitude - (b_altitude * 2), minimum_output=0.0) * self.deform_speed

            self.deform_map[collider_a_xy].altitude = get_capped_number(self.deform_map[collider_a_xy].altitude + a_altitude, minimum_output=0.0, maximum_output=1.0)
            self.deform_map[collider_b_xy].altitude = get_capped_number(self.deform_map[collider_b_xy].altitude + b_altitude, minimum_output=0.0, maximum_output=1.0)

        else:   # Subduct
            # Determine which side is the altitude donator and which is the reciever
            if self.parent_map[collider_a_xy].density > self.parent_map[collider_b_xy].density:
                donator_xy = collider_a_xy
                target_xy = collider_b_xy
            else:
                donator_xy = collider_b_xy
                target_xy = collider_a_xy

            change_in_altitude = get_capped_number(self.parent_map[donator_xy].altitude / 2, maximum_output=1 - self.parent_map[target_xy].altitude)

            # Apply the determined altitude deforms
            self.deform_map[donator_xy].altitude = get_capped_number(self.deform_map[donator_xy].altitude - change_in_altitude, minimum_output=0.0, maximum_output=1.0)
            self.deform_map[target_xy].altitude = get_capped_number(self.deform_map[target_xy].altitude + change_in_altitude, minimum_output=0.0, maximum_output=1.0)

    def deform_ridge_growth(self, ridge_a_xy, ridge_b_xy, neighbor_direction, growth_rate=0.005):
        """Creates a volcanic ridge rising up from a spreading plate boundary. This occurs when two cells have opposing vector directions."""

        self.deform_map[ridge_a_xy].altitude = get_capped_number(self.deform_map[ridge_a_xy].altitude + growth_rate, minimum_output=0.0, maximum_output=1.0)

        if self.deform_map[ridge_a_xy].vector.length() >= 0.0:
            self.deform_map[ridge_a_xy].vector = pygame.Vector2((neighbor_direction[0] * growth_rate, neighbor_direction[1] * growth_rate))
        else:
            self.deform_map[ridge_a_xy].vector.scale_to_length(self.deform_map[ridge_a_xy].vector.length() + growth_rate * self.deform_speed)

        if self.deform_map[ridge_a_xy].vector.length() > 1.0:
            self.deform_map[ridge_a_xy].vector.normalize_ip()

        self.deform_map[ridge_b_xy].altitude = get_capped_number(self.deform_map[ridge_b_xy].altitude + growth_rate, minimum_output=0.0, maximum_output=1.0)

        if self.deform_map[ridge_b_xy].vector.length() >= 0.0:
            self.deform_map[ridge_b_xy].vector = pygame.Vector2((neighbor_direction[0] * growth_rate * -1, neighbor_direction[1] * growth_rate * -1))
        else:
            self.deform_map[ridge_b_xy].vector.scale_to_length(self.deform_map[ridge_b_xy].vector.length() + growth_rate * self.deform_speed)

        if self.deform_map[ridge_b_xy].vector.length() > 1.0:
            self.deform_map[ridge_b_xy].vector.normalize_ip()

    def deform_sliding_rift(self, fault_a_xy, fault_b_xy, faulting_magnitude=0.2):
        """Force vectors moving past one another break and rift in unexpected ways creating
        wide canyons, trenches, hills and mountains. Altitude is exchanged at random with one another."""
        this_fault_magnitude = (random.random() * (2 * faulting_magnitude)) - faulting_magnitude

        self.deform_map[fault_a_xy].altitude = get_capped_number(self.deform_map[fault_a_xy].altitude + this_fault_magnitude, minimum_output=0.0, maximum_output=1.0) * self.deform_speed
        self.deform_map[fault_b_xy].altitude = get_capped_number(self.deform_map[fault_b_xy].altitude - this_fault_magnitude, minimum_output=0.0, maximum_output=1.0) * self.deform_speed

    def deform_by_neighbor(self, neighbor_direction):
        """Given a neighbor's direction, performs the deform calculations between it and the current cell.
        Applies the result to the current cell in the deform map."""
        this_cell_vector_direction = get_v2_direction(self.parent_map[self.x, self. y].vector)

        # Check for available neighbors at the given location
        if self.x < len(self.parent_map) - 1:
            neighbor_x = self.x + neighbor_direction[0]
        elif self.wrap_x:
            neighbor_x = 1
        else:
            return False

        if self.y < len(self.parent_map) - 1:
            neighbor_y = self.y + neighbor_direction[1]
        else:
            return False

        neighbor_cell_vector_direction = get_v2_direction(self.parent_map[neighbor_x, neighbor_y].vector)

        # Check if the current cell vector faces the target cell.
        if neighbor_direction == this_cell_vector_direction:
            if this_cell_vector_direction == neighbor_cell_vector_direction:  # Vectors run parallel
                self.deform_accretion((self.x, self.y), (neighbor_x, neighbor_y))  # TODO accretion to target
            elif this_cell_vector_direction[0] == neighbor_cell_vector_direction[0] or this_cell_vector_direction[1] == neighbor_cell_vector_direction[1]:  # Vectors are polar
                self.deform_collision((self.x, self.y), (neighbor_x, neighbor_y))  # TODO subduction and buckling
            else:
                self.deform_accretion((self.x, self.y), (neighbor_x, neighbor_y))  # TODO accretion to target

        # Check if the vector runs polar opposite to the target cell.
        elif neighbor_direction[0] == this_cell_vector_direction[0] or neighbor_direction[1] == this_cell_vector_direction[1]:
            if this_cell_vector_direction == neighbor_cell_vector_direction:  # Vectors run parallel
                self.deform_accretion((neighbor_x, neighbor_y), (self.x, self.y))  # TODO accretion from target
            elif this_cell_vector_direction[0] == neighbor_cell_vector_direction[0] or this_cell_vector_direction[1] == neighbor_cell_vector_direction[1]:  # Vectors are polar
                self.deform_ridge_growth((self.x, self.y), (neighbor_x, neighbor_y), neighbor_direction)  # TODO ridge spreading
            else:
                pass
                # TODO Pretty sure this will be a nunce interaction, this plate moves away as the other slides laterally

        # Otherwise the vector runs obliquely to the target.
        else:
            if not this_cell_vector_direction == neighbor_cell_vector_direction:
                if this_cell_vector_direction[0] == neighbor_cell_vector_direction[0] or this_cell_vector_direction[1] == neighbor_cell_vector_direction[1]:  # Vectors are polar
                    self.deform_sliding_rift((self.x, self.y), (neighbor_x, neighbor_y))   # TODO sliding
                elif not neighbor_cell_vector_direction == neighbor_direction:
                    self.deform_accretion((neighbor_x, neighbor_y), (self.x, self.y))   # TODO accretion from target
                else:
                    pass
                    # TODO Pretty sure this will be a nunce interaction, this plate moves away as the other slides laterally

    def end_of_map(self):
        """Handles the crawler reaching the end of the map."""
        self.x, self.y = 0, 0
        self.parent_map.match(self.deform_map)

    def record_deform(self):
        """Given a target cell position, deforms the target cell and the crawler's current cell based on a comparison of
        their properties. Records deformations to the self.deform_map."""
        # Only the right and bottom neighbors are calculated, as any left or top neighbors will already have
        # performed their calculations by the time a cell is reached by the crawler.
        self.deform_by_neighbor((1, 0))
        self.deform_by_neighbor((0, 1))

    def step(self):
        """Causes the crawler to take one 'step' performing its calculations and storing the change expected for that
        cell, then moving on to the next cell.
        Returns True only if the end of the map is reached, returns False otherwise."""
        # Determine the change to the current cell
        self.record_deform()

        # Find the next location to move to
        if self.x < self.resolution_x - 1:
            self.x += 1

        elif self.y < self.resolution_y - 1:
            self.x = 0
            self.y += 1

        else:
            self.end_of_map()
            return True

        return False

    def walk(self, duration):
        """The crawler takes steps until it is nearing the duration given.
        Breaks and Returns true if the end of the map is reached.
        Returns False when it runs without reaching the end."""
        start_time = pygame.time.get_ticks()
        last_step_duration = 0

        while pygame.time.get_ticks() < start_time + duration - last_step_duration:
            step_started_at = pygame.time.get_ticks()
            if self.step():
                return True
            last_step_duration = pygame.time.get_ticks() - step_started_at

        return False


@dataclass
class TectonicCell:
    vector: pygame.Vector2
    density: float
    altitude: float = 0.5


def init_map(resolution, number_of_plates):
    """Initializes the tectonic cell objects and places them in an array of the correct size. Returns the generated map."""
    # Get the starting tectonic plates
    plate_centers = get_random_tuples(number_of_plates)
    plate_vectors = get_random_vectors(number_of_plates)
    plate_densities = get_random_floats(number_of_plates)

    # Generate the map array of the given size, with all vectors closest to each point starting with that vector.
    this_map = []

    for x_row in range(0, resolution[0]):
        this_column = []  # Start this column

        for y_column in range(0, resolution[1]):
            # Find the closest plate to this location
            this_center = x_row / resolution[0], y_column / resolution[1]
            closest_center = 100

            for index in range(0, number_of_plates):
                if math.dist(plate_centers[index], this_center) < closest_center:
                    closest_center = math.dist(plate_centers[index], this_center)
                    closest_vector = plate_vectors[index].copy()
                    closest_density = plate_densities[index]

            this_column.append(TectonicCell(closest_vector.copy(), closest_density, 1 - closest_density))

        this_map.append(tuple(this_column))

    return tuple(this_map)


def get_capped_number(number, minimum_output=None, maximum_output=None):
    """Returns the given number, capped to the given minimum and/or maximum outputs."""
    if minimum_output is not None and number < minimum_output:
        number = minimum_output
    if maximum_output is not None and number > maximum_output:
        number = maximum_output

    return number


def get_v2_direction(vector2):
    """Given a vector returns a tuple of (x, y) showing which cardinal direction it is pointing in.
    (1, 0) for east, (0, 1) for south, (-1, 0) for west, (0, -1) for north."""
    if abs(vector2.x) > abs(vector2.y):
        if vector2.x > 0:
            return 1, 0     # East
        else:
            return -1, 0    # West
    else:
        if vector2.y > 0:
            return 0, 1     # South
        else:
            return 0, -1    # North


def get_sigmoid_function(x, slope=1.0, x_offset=0.0):
    """Returns the product of X in a logistic sigmoid function with the given parameters."""
    return 1 / (1 + math.e**(-slope * (x - x_offset)))


def get_random_floats(number):
    """Returns a tuple of the given number of random floats in the range of 0.0 to 1.0."""
    list_of_floats = []

    while len(list_of_floats) < number:
        list_of_floats.append(random.random())

    return tuple(list_of_floats)


def get_random_tuples(number):
    """Returns a tuple of the given number of random 2d tuples in a range of (0.0, 0.0) to (1.0, 1.0)."""
    list_of_tuples = []

    while len(list_of_tuples) < number:
        list_of_tuples.append((random.random(), random.random()))

    return tuple(list_of_tuples)


def get_random_vectors(number):
    """Returns a tuple of the given length built from randomized pygame Vector2s with a range of -1.0 to 1.0 in both the x and y."""
    list_of_vectors = []

    while len(list_of_vectors) < number:
        list_of_vectors.append(pygame.Vector2((random.random() * 2) - 1, (random.random() * 2) - 1))

    return tuple(list_of_vectors)



