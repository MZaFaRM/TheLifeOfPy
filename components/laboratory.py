import os
import pygame
from config import image_assets


class LaboratoryComponent:
    def __init__(self, main_surface, context=None):
        self.surface = pygame.image.load(
            os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
        )
        self.back_button = {
            "current_image": None,
            "position": {"topleft": (50, 50)},
            "absolute_rect": None,
            "image": pygame.image.load(
                os.path.join(image_assets, "laboratory", "back_button.svg")
            ),
            "clicked_image": pygame.image.load(
                os.path.join(image_assets, "laboratory", "back_button_clicked.svg")
            ),
        }

        self.back_button["rect"] = self.back_button["image"].get_rect(
            **self.back_button["position"]
        )
        self.back_button["current_image"] = self.back_button["image"]

        self.back_button["absolute_rect"] = self.back_button["image"].get_rect(
            topleft=(
                50 + ((main_surface.get_width() - self.surface.get_width()) // 2),
                50 + ((main_surface.get_height() - self.surface.get_height()) // 2),
            )
        )
        self.main_surface = main_surface

    def _event_handler(self, event):
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            if self.back_button["absolute_rect"].collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.back_button["current_image"] = self.back_button[
                        "clicked_image"
                    ]
                elif event.type == pygame.MOUSEBUTTONUP:
                    yield "navigate_home"
            else:
                self.back_button["current_image"] = self.back_button["image"]

        pass

    def update(self, context=None):
        self.surface.blit(self.back_button["current_image"], self.back_button["rect"])
