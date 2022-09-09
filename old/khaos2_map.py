import scipy
import numpy
import matplotlib
from khaos2_cell import *


def average(*items):
    return sum(items) / len(items)


class Settings:
    def __init__(self):
        # Program control
        self.seed = 2
        self.quickstart = True
        self.window_size = (1700, 1000)

        # Controllers for map size and shape
        self.seed_points = 500
        self.relax_passes = 5

        # Terrain features
        self.mountain_incidence = 0.15


class Renderer:
    def __init__(self, size):
        self.screen = pygame.display.set_mode(size)
        self.clock = pygame.time.Clock()

        # Create the master queue, calling update() in the master queue calls all the other render containers inside.
        self.mstq = RenderQueueContainer(self)


class RenderQueueContainer:
    def __init__(self, renderer):
        self.renderer = renderer
        self.do_update = True
        self.queue = []

    def add(self, renderable_object, orient='top'):
        if renderable_object not in self.queue:
            if orient == 'top':
                self.queue.append(renderable_object)
            elif orient == 'bottom':
                self.queue.insert(0, renderable_object)

    def remove(self, renderable_object=None, remove_all=False):
        if remove_all:
            self.queue.clear()
            return True
        else:
            for index, each_object in enumerate(self.queue):
                if each_object == renderable_object:
                    del self.queue[index]
                    return True
            return False

    def switch(self, default='toggle'):
        if default == 'toggle':
            if self.do_update:
                self.do_update = False
                return False
            else:
                self.do_update = True
                return True
        elif default == 'off':
            self.do_update = False
        elif default == 'on':
            self.do_update = True

    def update(self):
        if self.do_update:
            for each_object in self.queue:
                each_object.update()


class MasterContainer(RenderQueueContainer):
    def __init__(self, renderer):
        super().__init__(renderer)

    def update(self):
        self.renderer.clock.tick(60)
        if self.do_update:
            for each_object in self.queue:
                each_object.update()
            pygame.display.flip()


class Map:
    def __init__(self, map_settings):
        self.stg = map_settings
        numpy.random.seed(self.stg.seed)

        # Create an instance of the renderer
        self.render = Renderer(self.stg.window_size)

        # Generate the voronoi map then convert it into cell and vertex objects
        self.voronoi = self.generate_voronoi()
        self.vertices = self.initialize_vertices()
        self.cells = RenderQueueContainer(self.render)
        self.render.mstq.add(self.cells)
        self.initialize_cells()

        self.render.mstq.update()
        input()

        # Generate a height-map
        self.generate_tectonic_heightmap()

    def generate_voronoi(self):
        # Makes the array containing all the initial seed points, then adds the eight additional distant points.
        seed_points = numpy.random.uniform(-1.0, 1.0, (self.stg.seed_points, 2))
        finitive_points = numpy.array([[2.0, 0], [0, 2.0],
                                       [-2.0, 0], [0, -2.0],
                                       [2.0, 2.0], [2.0, -2.0],
                                       [-2.0, 2.0], [-2.0, -2.0]])
        seed_points = numpy.append(seed_points, finitive_points, axis=0)

        # Generates and shows the Voronoi diagram
        voronoi_diagram = scipy.spatial.Voronoi(seed_points)
        scipy.spatial.voronoi_plot_2d(voronoi_diagram)
        if not self.stg.quickstart:
            matplotlib.pyplot.show()

        # Applies Lloyd's Algorithm to the diagram for the number of relax_passes
        for iteration in range(0, self.stg.relax_passes):
            voronoi_diagram = self.lloyds_relax(voronoi_diagram)
            print(f"Completed relaxation pass {iteration + 1}/{self.stg.relax_passes}")
            if not self.stg.quickstart:
                matplotlib.pyplot.close()
                scipy.spatial.voronoi_plot_2d(voronoi_diagram)
                matplotlib.pyplot.show()

        return voronoi_diagram

    def generate_tectonic_heightmap(self):
        pass

    def lloyds_relax(self, vor):
        """Applies Lloyd's algorithm to the given voronoi diagram, finding the centroid of each region and then passing
        those to scipy to re-create a relaxed diagram."""
        centroids = None
        for each_point in enumerate(vor.points):
            if abs(each_point[1][0]) > 1.0 or abs(each_point[1][1]) > 1.0:
                centroids = numpy.append(centroids, [each_point[1]], axis=0)
            else:
                region_vertices = None
                for each_index in vor.regions[vor.point_region[each_point[0]]]:
                    if region_vertices is None:
                        region_vertices = numpy.array([vor.vertices[each_index]])
                    else:
                        region_vertices = numpy.append(region_vertices, [vor.vertices[each_index]], axis=0)

                centroid = (numpy.mean(region_vertices[0:, 0]), numpy.mean(region_vertices[0:, 1]))

                if centroids is None:
                    centroids = numpy.array([centroid])
                else:
                    centroids = numpy.append(centroids, [centroid], axis=0)
        return scipy.spatial.Voronoi(centroids)

    def initialize_vertices(self):
        vertices = []
        for index, vertex in enumerate(self.voronoi.vertices):
            vertices.append(RidgeVertex(index, vertex))

        for each_vertex in vertices:
            each_vertex.find_adjacent_vertices(self.voronoi, vertices)

        return vertices

    def initialize_cells(self):
        self.cells.remove(remove_all=True)
        # Create the cells
        for each_point in enumerate(self.voronoi.points):
            if abs(each_point[1][0]) == 2.0 or abs(each_point[1][1]) == 2.0:
                continue
            else:
                self.cells.add(Cell(each_point[0], self.voronoi, self))

        # Run get_neighbors to populate the list of neighboring cells.
        for each_cell in self.cells.queue:
            each_cell.get_vertices(self.vertices)
            each_cell.get_neighbors(self.cells)


if __name__ == '__main__':
    settings = Settings()
    cell_map = Map(settings)
