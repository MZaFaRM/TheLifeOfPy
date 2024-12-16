import os
import pygame
from config import image_assets


class LaboratoryComponent:
    def __init__(self, main_surface, context=None):
        self.surface = pygame.image.load(
            os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
        )

    def _event_handler(self, event):
        pass

    def update(self, context=None):
        pass
