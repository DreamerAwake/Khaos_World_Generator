import pygame


class Cell:
    def __init__(self, point_index, vor, parent_map):

        # Sets all the positional data for the cell.
        self.index = point_index
        self.map = parent_map
        self.generator = vor.points[point_index]
        self.region = []
        self.region_polygon = []
        self.neighbors = []

    def get_vertices(self, vertices):
        self.region = []
        self.region_polygon = []
        for each_index in self.map.voronoi.regions[self.map.voronoi.point_region[self.index]]:
            if each_index != -1:
                self.region.append(vertices[each_index])
                self.region_polygon.append(self.map.voronoi.vertices[each_index])

    def get_neighbors(self, cells):
        self.neighbors = []
        for index1, index2 in self.map.voronoi.ridge_points:
            if index1 == self.index and 0 <= index2 < self.map.stg.seed_points:
                self.neighbors.append(cells.queue[index2])
            elif index2 == self.index and 0 <= index1 < self.map.stg.seed_points:
                self.neighbors.append(cells.queue[index1])

    def update(self):
        pygame.draw.polygon(self.map.render.screen, (30, 180, 30), self.region_polygon)
        pygame.draw.polygon(self.map.render.screen, (30, 30, 30), self.region_polygon, width=2)


class RidgeVertex:
    def __init__(self, index, position):

        self.index = index
        self.position = position
        self.adjacent_vertices = []
        self.altitude = 0.0

    def find_adjacent_vertices(self, vor, vertices):
        self.adjacent_vertices = []
        found_vertices = []
        for ridge in vor.ridge_vertices:
            if ridge[0] == self.index:
                found_vertices.append(ridge[1])
            elif ridge[1] == self.index:
                found_vertices.append(ridge[0])

        for each_vertex in vertices:
            if each_vertex.index in found_vertices:
                self.adjacent_vertices.append(each_vertex)
