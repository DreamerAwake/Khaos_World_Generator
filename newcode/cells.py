from dataclasses import dataclass
from math import atan2, pi, tau, trunc

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
    def __init__(self, parent_cell, starting_temperature=50):
        self.wind_vector = pygame.Vector2(0, 0)
        self.wind_speed_by_latitude = get_latitude_wind_speed(parent_cell)

        self.moisture = 0
        self.temperature = starting_temperature

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
        adjustment_multiplier = get_transfer_adjustment_multiplier(this_cell)

        # Apply logged adjustments
        apply_logged_adjustments(this_cell, adjustment_multiplier)

        # Subtract the windspeed lost to resistance.
        new_magnitude = get_capped_number(this_cell.atmosphere.wind_vector.magnitude() - self.wind_resistance,
                                          minimum_output=0.0, maximum_output=1.0)
        this_cell.atmosphere.wind_vector.scale_to_length(new_magnitude)

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
        this_cell.atmosphere.logged_adjustments[this_cell] = get_atmosphere_log(this_cell.atmosphere, 0.0)

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
        this_cell.neighbor_cells[neighbor_index].atmosphere.logged_adjustments[this_cell] = get_atmosphere_log(this_cell.atmosphere, transfer_rate)

        self.current_index += 1  # Increment the step counter
        return False  # Let the crawler know it hasn't hit the end yet

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

@dataclass
class KhaosVertex:
    """A class containing information about a map vertex."""
    def __init__(self, position, altitude):
        self.x, self.y = position
        self.altitude = altitude
        self.parent_cells = []


def apply_logged_adjustments(cell, adjustment_multiplier):
    """Applies a cell's logged atmospheric adjustments. Then, clears the log so new calculations can be done."""
    for each_donor_cell in cell.atmosphere.logged_adjustments.keys():
        donor_transfer_rate, donor_wind_vector, donor_moisture, donor_temperature = cell.atmosphere.logged_adjustments[
            each_donor_cell]
        donate_this_windspeed = donor_transfer_rate * donor_wind_vector.magnitude() * adjustment_multiplier
        donate_this_moisture = trunc(donor_transfer_rate * donor_moisture * adjustment_multiplier)
        donate_this_temperature = get_temperature_change(donor_transfer_rate, cell, donor_temperature)

        # Adjust windspeed
        each_donor_cell.atmosphere.wind_vector.scale_to_length(
            get_capped_number(each_donor_cell.atmosphere.wind_vector.magnitude() - donate_this_windspeed,
                              minimum_output=0.0))
        cell.atmosphere.wind_vector += donor_wind_vector.scale_to_length(donate_this_windspeed)

        # Adjust moisture
        each_donor_cell.atmosphere.moisture -= donate_this_moisture
        cell.atmosphere.moisture += donate_this_moisture

        # Adjust temperature
        each_donor_cell.atmosphere.temperature -= donate_this_temperature
        cell.atmosphere.temperature += donate_this_temperature

        # Clear logged adjustments
        cell.atmosphere.logged_adjustments.clear()


def get_transfer_adjustment_multiplier(cell):
    """Returns the adjustment multiplier that caps windspeed gains when facing multiple input wind vectors
    during atmospheric calculations."""
    total_adjustments = [transfer_rate * wind_vector.magnitude() for transfer_rate, wind_vector, moisture in
                         cell.atmosphere.logged_adjustments.values()]
    maximum_additional_windspeed = 1.0 - cell.atmosphere.logged_adjustments[cell][1].magnitude()
    if sum(total_adjustments) < maximum_additional_windspeed:
        return 1.0
    else:
        return maximum_additional_windspeed / sum(total_adjustments)


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


def get_atmosphere_log(atmosphere, transfer_rate):
    """Returns the log of that atmosphere's current state for the adjustment logger."""
    return transfer_rate, atmosphere.wind_vector.copy(), atmosphere.moisture, atmosphere.temperature


def get_temperature_change(donor_transfer_rate, cell, donor_temperature, tropics_extent=0.15, tropics_temp=100, tropics_warming=5, arctic_extent=0.85, arctic_temp=0, arctic_cooling=5):
    """Gets the change in temperature for the atmosphere crawler's adjustment applier."""
    temperature_difference = donor_temperature - cell.atmosphere.temperature
    temperature_change = temperature_difference * donor_transfer_rate

    if abs(cell.y) > arctic_extent and cell.atmosphere.temperature + temperature_change > arctic_temp:
        temperature_change -= arctic_cooling

    elif abs(cell.y) < tropics_extent and cell.atmosphere.temperature + temperature_change < tropics_temp:
        temperature_change += tropics_warming

    return temperature_change

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
