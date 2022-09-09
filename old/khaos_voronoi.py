import scipy
import numpy
import matplotlib
import math

# Settings
bbox_offset = (-100, -100)
bbox_size = (200, 200)
points_to_generate = 10
seed = 0


def generate_voronoi(points, relax_passes=0):
    """Generates a voronoi diagram from the given points, bounded to the given bounding box
    (a tuple of tuples defining the corner closest to -inf, -inf, and its opposite)."""
    # Generates the unbounded diagram from scipy
    diagram = scipy.spatial.Voronoi(points)
    scipy.spatial.voronoi_plot_2d(diagram)
    matplotlib.pyplot.show()

    # Create an empty regions list to rebuild from the generated one
    bounded_regions = []

    for region in diagram.regions:
        # Creates an empty region to place into the bounded_regions list at the end of this loop
        new_region = []

        for vertex_index in enumerate(region):
            if vertex_index[1] != -1 and is_in_bounding_box(diagram.vertices[vertex_index[1]], bbox_offset, bbox_size):
                new_region.append(vertex_index[1])

            elif vertex_index[1] != -1 and not is_in_bounding_box(diagram.vertices[vertex_index[1]], bbox_offset, bbox_size):
                # If the current vertex is out of the box, but does exist, we find the co-linear point within the box
                search_index = 1
                collinear_point = diagram.vertices[region[vertex_index[0] - search_index]]
                while not is_in_bounding_box(collinear_point, bbox_offset, bbox_size):
                    search_index += 1
                    collinear_point = diagram.vertices[region[vertex_index[0] - search_index]]

                # The current vertex and the collinear point describe a line segment which must
                # intersect with one of the bounding box walls, find that intersection
                new_vertex = None

                for wall in get_iterable_bounds(bbox_offset, bbox_size):
                    new_vertex = get_intersect((diagram.vertices[vertex_index[1]], collinear_point), wall, True)
                    if new_vertex is not None:
                        break

                add_vertex_to_region(new_vertex, new_region, diagram.vertices)

            else:
                # The vertex index is -1, there is no point outside the bounding box to self correct with
                # find the generator point for the current region
                print(diagram.points)
                print(diagram.vertices)
                print(diagram.regions)
                generator_point = diagram.points[get_region_point_index(region, diagram)]
                equidistant_point = None

                # find a generator equidistant to the last real vertex from the current region's generator
                last_real_vertex = diagram.vertices[region[vertex_index[0] - 1]]
                distance = math.dist(generator_point, last_real_vertex)

                # Finds a point that is equidistant to the last real vertex, and which defines a region that does not
                # share a ridge with the current region in the unbounded diagram
                # (thus their shared ridge is the infinite ray)
                for point in enumerate(diagram.points):
                    if equidistant_point is None:
                        equidistant_point = point[1]
                    else:
                        if abs(math.dist(point[1], last_real_vertex) - distance) < abs(math.dist(equidistant_point, last_real_vertex) - distance):
                            equidistant_point = point[1]


                # Find the mid-point of the two points
                generators_midpoint = (average(generator_point[0], equidistant_point[0]),
                                       average(generator_point[1], equidistant_point[1]))

                # Using the line defined by the last vertex and generator midpoint find the intersections with its
                # boundaries. Then determine which of those is closest to the generator, and thus the one belonging to
                # the current region

                intersects = []
                for wall in get_iterable_bounds(bbox_offset, bbox_size):
                    intersects.append(get_intersect((last_real_vertex, generators_midpoint), wall))

                least_distance = None
                least_index = None
                for intersect in enumerate(intersects):
                    distance = math.dist(generator_point, intersect[1][0])
                    if least_distance is None or distance < least_distance:
                        least_distance = distance
                        least_index = intersect[0]

                add_vertex_to_region(intersects[least_index], new_region, diagram.vertices)

        bounded_regions.append(new_region)

    diagram.regions = bounded_regions
    return diagram


def average(*items):
    return sum(items) / len(items)


def add_vertex_to_region(new_vertex, region, vertices_array):
    print(f"adding vertex to region R:{region}, V {new_vertex}")
    in_array = is_in_vertices(new_vertex, vertices_array)
    if in_array is None:
        numpy.append(vertices_array, new_vertex, 0)
        region.append(numpy.size(vertices_array, 0) - 1)
    else:
        region.append(in_array)


def is_in_bounding_box(point, bbox_offset, bbox_size):
    if bbox_offset[0] <= point[0] <= bbox_offset[0] + bbox_size[0] and bbox_offset[1] <= point[1] <= bbox_offset[1] + bbox_size[1]:
        return True
    else:
        return False


def is_in_vertices(sample_vertex, vertices):
    """Checks if the sample_vertex is already in the vertices array, and if so, returns that vertex's index number."""
    for vertex in enumerate(vertices):
        boolarr = vertex[1] == sample_vertex
        if numpy.all(boolarr):
            return vertex[0]
    return None


def do_regions_share_ridge(region1, region2):
    co_vertices = 0
    for index1 in region1:
        for index2 in region2:
            if index1 == index2:
                co_vertices += 1
            if co_vertices > 1:
                return True
    return False


def get_iterable_bounds(bbox_offset, bbox_size):
    """Returns a list of lines (pairs of tuple pairs), corresponding to the walls of the bounding box.
    They are returned in the order (assuming local 0,0 is the bottom right) of Left, """
    bounds = []
    bounds.append((bbox_offset, (bbox_offset[0], bbox_offset[1] + bbox_size[1])))
    bounds.append(((bbox_offset[0] + bbox_size[0], bbox_offset[1]),
                   (bbox_offset[0] + bbox_size[0], bbox_offset[1] + bbox_size[1])))
    bounds.append((bbox_offset, (bbox_offset[0] + bbox_size[0], bbox_offset[1])))
    bounds.append(((bbox_offset[0], bbox_offset[1] + bbox_size[1]),
                   (bbox_offset[0] + bbox_size[0], bbox_offset[1] + bbox_size[1])))
    return bounds

def get_slope(point1, point2):
    if point1[0] - point2[0] == 0:
        return 0
    else:
        return (point1[1] - point2[1]) / (point1[0] - point2[0])


def get_y_intercept(point, slope):
    return point[1] - slope * point[0]


def get_intersect(line1, line2, treat_as_segment=False):
    """If treated as a line segment, determines if there is an intersection by determining the rotation of ordered
    pairs of points. See https://www.geeksforgeeks.org/check-if-two-given-line-segments-intersect/.
    Returns None if there is no intersect."""

    if treat_as_segment:
        orient1 = get_orientation(line1[0], line1[1], line2[0])
        orient2 = get_orientation(line1[0], line1[1], line2[1])
        orient3 = get_orientation(line2[0], line2[1], line1[0])
        orient4 = get_orientation(line2[0], line2[1], line1[1])

        if orient1 is not orient2 and orient3 is not orient4:
            pass
        else:
            return None

    line1_slope = get_slope(line1[0], line1[1])
    line2_slope = get_slope(line2[0], line2[1])

    line1_intercept = get_y_intercept(line1[0], line1_slope)
    line2_intercept = get_y_intercept(line2[0], line2_slope)

    if line1_slope == line2_slope:
        return None

    x = (line2_intercept - line1_intercept) / (line1_slope - line2_slope)
    y = line1_slope * x * line1_intercept

    return numpy.array([[x, y]])


def get_orientation(point1, point2, point3):
    val = (float(point2[1] - point1[1]) * (point3[0] - point2[0])) - \
          (float(point2[0] - point1[0]) * (point3[1] - point2[1]))
    if val > 0:
        # Clockwise orientation
        return 1
    elif val < 0:
        # Counterclockwise orientation
        return 2
    else:
        # Collinear orientation
        return 0


if __name__ == '__main__':
    numpy.random.seed(seed)
    sample_points = numpy.random.uniform(-100, 100, (10, 2))
    voronoi_diagram = generate_voronoi(sample_points)
    scipy.spatial.voronoi_plot_2d(voronoi_diagram)
    for vertex in voronoi_diagram.vertices:
        print(vertex)
        matplotlib.pyplot.scatter(vertex[0], vertex[1], s=12)
    matplotlib.pyplot.show()
