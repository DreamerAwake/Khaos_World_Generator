from dataclasses import dataclass

import pygame

from heightmap import get_sigmoid_function


@dataclass
class KhaosCell:
    """A class containing information about a map cell."""
    def __init__(self, position, altitude, vertices):
        self.x, self.y = position
        self.altitude = altitude

        self.region_vertices = tuple(vertices)
        link_cell_to_vertices(self)

        self.neighbor_cells = []


@dataclass
class CellAtmosphere:
    """Contains information about a cell's atmospheric conditions."""
    def __init__(self, parent_cell):
        self.wind_vector = pygame.Vector2(0, 0)
        self.wind_speed_by_latitude = get_latitude_wind_speed(parent_cell)


@dataclass
class KhaosVertex:
    """A class containing information about a map vertex."""
    def __init__(self, position, altitude):
        self.x, self.y = position
        self.altitude = altitude
        self.parent_cells = []


def get_latitude_wind_speed(cell):
    """Gets the added windspeed per tick for a cell's atmosphere based on its latitude."""
    result = get_sigmoid_function(abs(cell.y), slope=-15, x_offset=0.9, y_offset=-0.15, scale=0.15) + \
             get_sigmoid_function(abs(cell.y), slope=-15, x_offset=0.1, y_offset=0.0, scale=0.15)

    return result


def link_cell_to_vertices(cell):
    """Adds the given cell to the list of parent cells inside each vertex of that cell."""
    for each_vertex in cell.region_vertices:
        if cell not in each_vertex.parent_cells:
            each_vertex.parent_cells.append(cell)
