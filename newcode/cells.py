from dataclasses import dataclass
from math import atan2, pi, tau

import pygame

from heightmap import get_sigmoid_function, get_capped_number


@dataclass
class KhaosCell:
    """A class containing information about a map cell."""
    def __init__(self, position, altitude, vertices):
        self.x, self.y = position
        self.altitude = altitude
        self.atmosphere = CellAtmosphere(self)

        self.region_vertices = tuple(vertices)
        link_cell_to_vertices(self)

        self.neighbor_cells = []


@dataclass
class CellAtmosphere:
    """Contains information about a cell's atmospheric conditions."""
    def __init__(self, parent_cell):
        self.wind_vector = pygame.Vector2(0, 0)
        self.wind_speed_by_latitude = get_latitude_wind_speed(parent_cell)
        self.moisture = 0

        self.logged_adjustments = {}


class AtmosphereCrawler:
    """Crawls all the cell atmospheres and has them log adjustments for the next tick,
    then executes all the adjustments at once."""
    def __init__(self, cells, wind_resistance=0.1):
        self.wind_resistance = wind_resistance

        self.cells = cells
        self.calculation_phase = True
        self.current_index = 0

    def step(self):
        """Runs steps and manages the mode of the crawler."""
        if self.calculation_phase:
            if self.step_calculate():
                self.calculation_phase = False
                self.current_index = 0
        else:
            if self.step_apply():
                self.calculation_phase = True
                self.current_index = 0

    def step_apply(self):
        """The crawler applies the next cell's logged calculations."""
        if self.current_index == len(self.cells):
            return True

        this_cell = self.cells[self.current_index]

        # Calculate the changes from logged_adjustments
        total_adjustments = [transfer_rate * wind_vector.magnitude() for transfer_rate, wind_vector, moisture in this_cell.atmosphere.logged_adjustments.values()]
        maximum_additional_windspeed = 1.0 - this_cell.atmosphere.logged_adjustments[this_cell][1].magnitude()
        if sum(total_adjustments) < maximum_additional_windspeed:
            adjustment_multiplier = 1.0
        else:
            adjustment_multiplier = maximum_additional_windspeed / sum(total_adjustments)

        # Apply logged adjustments
        for each_donor_cell in this_cell.atmosphere.logged_adjustments.keys():
            donor_transfer_rate, donor_wind_vector, donor_moisture = this_cell.atmosphere.logged_adjustments[
                each_donor_cell]
            donate_this_windspeed = donor_transfer_rate * donor_wind_vector.magnitude() * adjustment_multiplier
            donate_this_moisture = donor_transfer_rate * donor_moisture * adjustment_multiplier

            # Adjust windspeed
            each_donor_cell.atmosphere.wind_vector.scale_to_length(
                get_capped_number(each_donor_cell.atmosphere.wind_vector.magnitude() - donate_this_windspeed,
                                  minimum_output=0.0))
            this_cell.atmosphere.wind_vector += donor_wind_vector.scale_to_length(donate_this_windspeed)

            # Adjust moisture
            each_donor_cell.atmosphere.moisture -= donate_this_moisture
            this_cell.atmosphere.moisture += donate_this_moisture

        # Subtract the windspeed lost to resistance.
        new_magnitude = get_capped_number(this_cell.atmosphere.wind_vector.magnitude() - self.wind_resistance,
                                          minimum_output=0.0, maximum_output=1.0)
        this_cell.atmosphere.wind_vector.scale_to_length(new_magnitude)

        # Clear logged adjustments
        this_cell.atmosphere.logged_adjustments.clear()

        self.current_index += 1  # Increment the step counter
        return False  # Let the crawler know it hasn't hit the end yet

    def step_calculate(self):
        """The crawler performs the next cell's calculations."""
        # Check if we should be done with a full pass
        if self.current_index == len(self.cells):
            return True

        this_cell = self.cells[self.current_index]
        neighbor_differences = []

        # place the cell in its own atmosphere log with a rate of 0.0
        this_cell.atmosphere.logged_adjustments[this_cell] = (0.0, this_cell.atmosphere.wind_vector.magnitude(), this_cell.atmosphere.moisture)

        # Find the neighbor with the angle from the current cell closest to the cell's wind vector angle
        wind_vector_angle = get_vector_angle(this_cell.atmosphere.wind_vector.x, this_cell.atmosphere.wind_vector.y)

        for each_neighbor in this_cell.neighbor_cells:
            to_neighbor_angle = get_vector_angle(this_cell.x + each_neighbor.x, this_cell.y + each_neighbor.y)
            neighbor_differences.append(get_angle_difference(wind_vector_angle, to_neighbor_angle))

        # This is the index of the neighbor with the best angle
        neighbor_index = neighbor_differences.index(min(neighbor_differences))

        # Now find the adjustment value to log
        transfer_rate = get_atmospheric_transfer_speed(this_cell, this_cell.neighbor_cells[neighbor_index])

        # Log is a dict of this_cell object: (transfer rate, wind magnitude, moisture level)
        this_cell.neighbor_cells[neighbor_index].atmosphere.logged_adjustments[this_cell] = (transfer_rate, this_cell.atmosphere.wind_vector.copy(), this_cell.atmosphere.moisture)

        self.current_index += 1  # Increment the step counter
        return False  # Let the crawler know it hasn't hit the end yet


@dataclass
class KhaosVertex:
    """A class containing information about a map vertex."""
    def __init__(self, position, altitude):
        self.x, self.y = position
        self.altitude = altitude
        self.parent_cells = []


def get_atmospheric_transfer_speed(cell, neighbor):
    """Given a cell and a neighbor, calculates the atmospheric transfer speed from the given cell to the neighbor.
    Assumes that the wind direction has already been checked."""
    cell_transfer_intensity = cell.atmosphere.wind_vector.magnitude() * (cell.atmosphere.moisture / neighbor.atmosphere.moisture)

    transfer_rate = get_sigmoid_function(cell_transfer_intensity, slope=10, x_offset=0.5) - \
                    get_sigmoid_function(neighbor.atmosphere.wind_vector.magnitude(), slope=10, x_offset=0.5)

    if transfer_rate < 0:
        return 0.0
    else:
        return transfer_rate


def get_latitude_wind_speed(cell):
    """Gets the added windspeed per tick for a cell's atmosphere based on its latitude."""
    result = get_sigmoid_function(abs(cell.y), slope=-15, x_offset=0.9, y_offset=-0.15, scale=0.15) + \
             get_sigmoid_function(abs(cell.y), slope=-15, x_offset=0.1, y_offset=0.0, scale=0.15)

    return result


def get_vector_angle(x, y):
    """Given a co-ordinate vector, gives the angle of that vector in radians."""
    return atan2(y, x)


def get_angle_difference(angle_a, angle_b):
    """Returns the absolute value of the difference in radians between the two angles."""
    difference = abs(angle_a - angle_b)

    if difference > pi:
        if angle_a < angle_b:
            angle_a += tau
            difference = abs(angle_a - angle_b)
        else:
            angle_b += tau
            difference = abs(angle_a - angle_b)

    return difference


def link_cell_to_vertices(cell):
    """Adds the given cell to the list of parent cells inside each vertex of that cell."""
    for each_vertex in cell.region_vertices:
        if cell not in each_vertex.parent_cells:
            each_vertex.parent_cells.append(cell)
