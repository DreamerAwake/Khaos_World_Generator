import random
from math import sqrt, trunc, dist
from matplotlib import pyplot


class PoissonGrid:
    """Generates a poisson disc sampling of a space in the range of -1.0 to 1.0 in the x and y."""
    def __init__(self, cells_to_a_side=100):
        self.grid = get_empty_grid(cells_to_a_side)
        self.grid_size = cells_to_a_side
        self.cell_size = 2/cells_to_a_side
        self.radius = sqrt(2 * self.cell_size ** 2)

        self.found_points = []
        self.open_points = []

    def generate(self, attempts_until_quit=30):
        self.find_next_point(attempts_until_quit)
        while self.open_points:
            self.find_next_point(attempts_until_quit)

    def get_coordinates(self):
        """Returns the found points list"""
        return self.found_points

    def find_next_point(self, attempts_until_quit=30):
        """Finds the next valid point for the sample."""

        if len(self.found_points) == 0:
            new_point = (2 * random.random() - 1, 2 * random.random() - 1)
            point_cell_x, point_cell_y = get_cell_from_point(new_point, self.cell_size)

            self.found_points.append(new_point)
            self.open_points.append(0)
            self.grid[point_cell_x][point_cell_y] = 0

        elif self.open_points:
            this_spawner_index = self.open_points[random.randrange(0, len(self.open_points))]
            this_spawner_center = self.found_points[this_spawner_index]
            this_spawner_found_candidate = False

            for each_attempt in range(0, attempts_until_quit):
                new_direction = ((2 * random.random() - 1), (2 * random.random() - 1))
                annulus_bound_distance = random.random() * self.radius * 2
                new_direction = (new_direction[0] * annulus_bound_distance, new_direction[1] * annulus_bound_distance)
                candidate_point = (this_spawner_center[0] + new_direction[0], this_spawner_center[1] + new_direction[1])
                point_cell_x, point_cell_y = get_cell_from_point(candidate_point, self.cell_size)

                if self.test_is_valid(candidate_point, point_cell_x, point_cell_y):
                    self.found_points.append(candidate_point)
                    self.open_points.append(len(self.found_points) - 1)
                    self.grid[point_cell_x][point_cell_y] = len(self.found_points) - 1
                    this_spawner_found_candidate = True
                    break

            if not this_spawner_found_candidate:
                self.open_points.remove(this_spawner_index)

    def test_is_valid(self, point, cellx, celly):
        """Determines if a point is a valid addition to the grid by finding if it lies within r
        distance of any point on the grid."""
        if -1.0 <= point[0] <= 1.0 and -1.0 <= point[1] <= 1.0:
            for each_cell_x in range(cellx - 2, cellx + 3):
                for each_cell_y in range(celly - 2, celly + 3):
                    if -1 < each_cell_x < self.grid_size and -1 < each_cell_y < self.grid_size:
                        if self.grid[each_cell_x][each_cell_y] is not None:
                            test_against_point = self.found_points[self.grid[each_cell_x][each_cell_y]]
                            if dist(point, test_against_point) < self.radius:
                                return False
            return True

        else:
            return False


def get_empty_grid(cells_to_a_side):
    """Returns an empty sampling grid of None values."""
    return [[None for y in range(0, cells_to_a_side)] for x in range(0, cells_to_a_side)]


def get_cell_from_point(point, cell_size):
    """Takes a point tuple, and returns its location in the cell grid."""
    adjusted_point = (point[0] + 1, point[1] + 1)
    return trunc(adjusted_point[0] / cell_size), trunc(adjusted_point[1] / cell_size)


if __name__ == "__main__":
    new_pgrid = PoissonGrid()
    new_pgrid.generate()

    print(f"This is the number of sample points: {len(new_pgrid.get_coordinates())}")

    pyplot.scatter(*zip(*new_pgrid.get_coordinates()), color='r', alpha=0.6, lw=0)
    pyplot.xlim(-1, 1)
    pyplot.ylim(-1, 1)
    pyplot.axis('off')
    pyplot.show()
