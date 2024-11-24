import pygame

from config import image_assets
from config import Colors


class EnvLayout:
    def __init__(self, main_layout):
        self.main_layout = main_layout
        self.env_image = pygame.image.load(image_assets + "/dot_grid.svg")
        self.surface = pygame.Surface(
            (self.env_image.get_width(), self.env_image.get_height()), pygame.SRCALPHA
        )
        self.surface.blit(self.env_image, (0, 0))
        self.main_layout.surface.blit(self.surface, (50, 100))

    def update(self, foods, creatures):
        self.surface.fill(Colors.bg_color)
        self.surface.blit(self.env_image, (0, 0))

        x, y = (0, 0)
        width, height = self.surface.get_width(), self.surface.get_height()
        rect = pygame.Rect(x, y, width, height)
        pygame.draw.rect(self.surface, (0, 0, 0), rect, 2)

        foods.draw(self.surface)
        for creature in creatures:
            creature.draw(self.surface)
