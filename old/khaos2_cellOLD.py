class Cell:
    def __init__(self, point_index, vor, parent_map):

        # Sets all the positional data for the cell.
        self.map = parent_map
        self.generator = vor.points[point_index]
        self.region = vor.regions[vor.point_region[point_index]]
        self.ridges, self.neighbors_indices = self.get_cell_bounds(vor, point_index)
        self.neighbors = []

    def get_cell_bounds(self, vor, cell_index):
        """Returns cell_ridges and neighbors. Cell_ridges contains all the ridge indices for the edges of the shape,
        which can be fed to ridge_vertices for the vertices of the ridge. neighbors_indices contains all the indices for
        the generator points of the cell's neighbors."""

        cell_ridges = []
        neighbors = []
        for ridge_index, points in enumerate(vor.ridge_points):
            if cell_index == points[0]:
                cell_ridges.append(ridge_index)
                if points[1] >= self.map.stg.seed_points:
                    neighbors.append(-1)
                else:
                    neighbors.append(points[1])
            elif cell_index == points[1]:
                cell_ridges.append(ridge_index)
                if points[0] >= self.map.stg.seed_points:
                    neighbors.append(-1)
                else:
                    neighbors.append(points[0])
        return cell_ridges, neighbors

    def get_neighbors(self, cells_list):
        self.neighbors = []
        for each_index in self.neighbors_indices:
            if each_index == -1:
                self.neighbors.append(None)
            else:
                self.neighbors.append(cells_list[each_index])

