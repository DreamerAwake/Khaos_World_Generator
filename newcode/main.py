import sys
import pygame
import heightmap as htmp


class Main:
    def __init__(self):
        pygame.init()

        self.display = pygame.display.set_mode((1200, 780))
        self.htmp_map = htmp.Heightmap((250, 250), 30)
        self.crawler = htmp.DeformCrawler(self.htmp_map, wrap_horizontal=True)

        self.heightmap_image = pygame.transform.scale(self.htmp_map.get_surface(), (500, 500))
        self.heightmap_rect = self.heightmap_image.get_rect()
        self.heightmap_rect.center = self.display.get_rect().center
        self.display.blit(self.heightmap_image, self.heightmap_rect)


    def loop(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    sys.exit()

            if self.crawler.walk(50/3):
                self.heightmap_image = pygame.transform.scale(self.htmp_map.get_surface(), (500, 500))
                self.display.blit(self.heightmap_image, self.heightmap_rect)

            pygame.display.flip()


if __name__ == "__main__":
    window = Main()
    window.loop()
