from scipy.spatial import Voronoi

def get_voronoi(cell_centers):
    """Uses SciPy to generate a bounded Voronoi diagram from the supplied list of coordinate tuples."""
    distant_points = [(2.0, 0.0), (0.0, 2.0),
                      (-2.0, 0.0), (0.0, -2.0),
                      (2.0, 2.0), (-2.0, -2.0),
                      (-2.0, 2.0), (2.0, -2.0)]

    points = cell_centers + distant_points

    return Voronoi(points)

