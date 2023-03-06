import sys
import pygame
import heightmap as htmp
from khaos_map import get_khaos_map, get_image_from_khaos_map
from voronoi import get_voronoi
from poissondisc import PoissonGrid


class Main:
    def __init__(self):
        pygame.init()

        self.display = pygame.display.set_mode((1200, 780))
        self.htmp_map = htmp.Heightmap((300, 200), 50)
        self.crawler = htmp.DeformCrawler(self.htmp_map, wrap_horizontal=True)

        self.heightmap_image = pygame.transform.scale(self.htmp_map.get_surface(), (600, 400))
        self.heightmap_rect = self.heightmap_image.get_rect()
        self.heightmap_rect.center = self.display.get_rect().center
        self.display.blit(self.heightmap_image, self.heightmap_rect)

    def height_crawler_loop(self):
        while self.crawler.completed_full_passes <= 100:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            if self.crawler.completed_full_passes % 10 == 0:
                if self.crawler.walk(50/3):
                    self.heightmap_image = pygame.transform.scale(self.htmp_map.get_surface(), (600, 400))
                    self.display.blit(self.heightmap_image, self.heightmap_rect)
            elif self.crawler.completed_full_passes <= 100:
                if self.crawler.walk(50/3):
                    self.display.blit(self.heightmap_image, self.heightmap_rect)
            else:
                self.heightmap_image = pygame.transform.scale(self.htmp_map.get_surface(), (600, 400))
                self.display.blit(self.heightmap_image, self.heightmap_rect)

            pygame.display.flip()

    def display_khaos_map_loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            pygame.display.flip()

if __name__ == "__main__":
    window = Main()
    window.height_crawler_loop()

    new_pgrid = PoissonGrid()
    new_pgrid.generate()
    new_khaos_map = get_khaos_map(get_voronoi(new_pgrid.found_points), window.htmp_map)
    window.display.blit(get_image_from_khaos_map(new_khaos_map, window.display.get_rect().size), (0, 0))

    window.display_khaos_map_loop()