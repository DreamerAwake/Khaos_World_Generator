import random

import pygame
from math import trunc
from cells import KhaosCell, KhaosVertex
from heightmap import Heightmap, get_capped_number


class KhaosMap:
    """The core data object for the map generator. Contains all of the cells and vertices produced by the generator."""
    def __init__(self, cells):
        self.cells = tuple(cells)


def get_khaos_map(voronoi_diagram, heightmap):
    """Uses the provided data to generate the map object."""
    cells = []
    vertices = [None for x in range(0, len(voronoi_diagram.vertices))]

    # For each point in the voronoi diagram:
    for each_cell_index in range(0, len(voronoi_diagram.points) - 8):

        cell_position = voronoi_diagram.points[each_cell_index]
        this_cell_vertices = []

        # Find its vertices and make sure they are instantiated, or else do so
        for each_vertex_index in get_vertices_indices(each_cell_index, voronoi_diagram):
            if vertices[each_vertex_index] is None:
                vertex_position = voronoi_diagram.vertices[each_vertex_index]
                vertices[each_vertex_index] = KhaosVertex(
                    vertex_position,
                    get_altitude_from_heightmap(vertex_position, heightmap)
                )

            this_cell_vertices.append(vertices[each_vertex_index])  # Add that vertex object to the current cell's list

        # Create and add the new cell
        cells.append(KhaosCell(
            cell_position,
            get_altitude_from_heightmap(cell_position, heightmap),
            this_cell_vertices
        ))

    # Do post-hoc clean-up
    for each_cell in cells:
        find_neighbors(each_cell)

    # Create the KhaosMap object and return it
    return KhaosMap(cells)


def find_neighbors(cell):
    """Finds and links a cell's neighbors. Should only run after all cells and vertices are created."""
    for each_vertex in cell.region_vertices:
        for each_parent_cell in each_vertex.parent_cells:
            if each_parent_cell not in cell.neighbor_cells:
                cell.neighbor_cells.append(each_parent_cell)

    # freeze neighbors to a tuple
    cell.neighbor_cells = tuple(cell.neighbor_cells)


def get_altitude_from_heightmap(position, heightmap):
    """Given a position in the range of -1.0 to 1.0 in the x, y and a heighmap object: returns the altitude at that
    adjusted location on the map."""
    return heightmap[get_position_in_resolution(position, heightmap.resolution)].altitude


def get_polygon_from_cell(cell, resolution):
    """Returns a polygon from a cell object that can be used to render a pygame object.
    Adjusts to fit the given surface resolution."""
    return [get_position_in_resolution((vertex.x, vertex.y), resolution) for vertex in cell.region_vertices]


def get_position_in_resolution(float_position, new_resolution):
    """Given a position in the range of -1.0 to 1.0 in the x, y and a resolution:
    returns an adjusted location to the resolution as a tuple of (int, int)."""
    adjusted_x = trunc(((float_position[0] + 1) / 2) * (new_resolution[0]))
    adjusted_y = trunc(((float_position[1] + 1) / 2) * (new_resolution[1]))

    adjusted_x = get_capped_number(adjusted_x, 0, new_resolution[0] - 1)
    adjusted_y = get_capped_number(adjusted_y, 0, new_resolution[1] - 1)

    return adjusted_x, adjusted_y


def get_image_from_khaos_map(khaos_map, image_resolution):
    """Produces a pygame surface from a khaos_map object's cells."""
    surface = pygame.Surface(image_resolution)
    surface.fill((0, 0, 0))

    for each_cell in khaos_map.cells:
        pygame.draw.polygon(surface,
                            get_average_color(get_color_from_cell_altitude(each_cell), get_color_from_temperature(each_cell), ignore_g=True, ignore_b=True),
                            get_polygon_from_cell(each_cell, image_resolution)
                            )

    return surface


def get_color_from_cell_altitude(cell):
    """Returns a pygame color reflecting the given cell's altitude."""
    color = pygame.Color(
        round(get_capped_number((cell.altitude * 255), 0, 255)),
        round(get_capped_number((cell.altitude * 255), 0, 255)),
        round(get_capped_number((cell.altitude * 255), 0, 255))
    )

    return color

def get_color_from_temperature(cell):
    """Returns a pygame color reflecting the given cell's temperature."""
    color = pygame.Color(
        round(get_capped_number((cell.atmosphere.temperature * 25.5), 0, 255)),
        0,
        0
    )

    return color


def get_average_color(color_1, color_2, ignore_r=False, ignore_g=False, ignore_b=False):
    """Gets the average of two given pygame colors. Can be told to ignore color channels individually,
    in which case the first color passed will provide that channel exclusively."""

    if ignore_r:
        r = color_1.r
    else:
        r = round(get_capped_number((color_1.r + color_2.r) / 2, 0, 255))

    if ignore_g:
        g = color_1.g
    else:
        g = round(get_capped_number((color_1.g + color_2.g) / 2, 0, 255))

    if ignore_b:
        b = color_1.b
    else:
        b = round(get_capped_number((color_1.b + color_2.b) / 2, 0, 255))

    return pygame.Color(r, g, b)


def get_random_color():
    """Returns a random tuple of (int, int, int) that is a valid pygame color."""
    color = (
        round(get_capped_number((random.random() * 255), 0, 255)),
        round(get_capped_number((random.random() * 255), 0, 255)),
        round(get_capped_number((random.random() * 255), 0, 255))
    )

    return color


def get_vertices_indices(point_index, voronoi_diagram):
    """Given a point index, finds the indices of the vertices in that point's voronoi region.
    Returns them as a list of ints."""
    return voronoi_diagram.regions[voronoi_diagram.point_region[point_index]]


if __name__ == "__main__":
    new_htmp = Heightmap()
    get_altitude_from_heightmap((-0.99999999, -0.99999999), new_htmp)
    get_altitude_from_heightmap((0.9999, 0.999999), new_htmp)
    get_altitude_from_heightmap((0.0, 0.0), new_htmp)
