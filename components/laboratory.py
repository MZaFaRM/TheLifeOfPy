import os
import pygame
from config import Fonts, image_assets


class LaboratoryComponent:
    def __init__(self, main_surface, context=None):
        self.surface = pygame.image.load(
            os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
        )
        self.configure_back_button(main_surface)
        self.configure_dp_circle()
        self.traits_schema = {
            "font": pygame.font.Font(Fonts.PixelifySans, 21),
            "text_color": pygame.Color(26, 26, 26),
            "bg_color": pygame.Color(74, 227, 181),
            "options": [
                {
                    "Initial Population": {"choice": "user_input", "type": int},
                    "Species": {"choice": "user_input", "type": str},
                    "Traitline": {
                        "choice": ["Swordling", "Mineling", "Shieldling", "Camoufling"],
                        "type": "single choice list",
                    },
                    "Domain": {
                        "choice": ["Square", "Circle", "Triangle", "Camoufling"],
                        "type": "single choice list",
                    },
                    "Kingdom": {
                        "choice": ["Predator", "Prey"],
                        "type": "single choice list",
                    },
                    "Vision Radius": {"choice": "user_input", "type": int},
                    "Size": {"choice": "user_input", "type": int},
                    "Color": {"choice": "user_input", "type": "color"},
                    "Speed": {"choice": "user_input", "type": int},
                    "Max Energy": {"choice": "user_input", "type": int},
                    "Blood Thirsty": {
                        "choice": ["False", "True"],
                        "type": "single choice list",
                    },
                }
            ],
        }

    def configure_dp_circle(self):
        self.pic_circle = {
            "angle": 0,
            "border_image": pygame.image.load(
                os.path.join(image_assets, "laboratory", "pic_circle_border.svg")
            ),
            "bg_image": pygame.image.load(
                os.path.join(image_assets, "laboratory", "pic_circle_bg.svg")
            ),
            "position": {
                "center": (
                    (3 / 4) * self.surface.get_width(),
                    (1 / 2) * self.surface.get_height(),
                )
            },
        }

        self.pic_circle["rect"] = self.pic_circle["bg_image"].get_rect(
            **self.pic_circle["position"]
        )
        self.pic_circle["border_rect"] = self.pic_circle["rect"]

    def configure_back_button(self, main_surface):
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

    def rotated_pic_circle(self):
        self.pic_circle["angle"] += 1
        rotated_image = pygame.transform.rotate(
            self.pic_circle["border_image"], self.pic_circle["angle"]
        )
        self.pic_circle["border_rect"] = rotated_image.get_rect(
            center=self.pic_circle["rect"].center
        )
        return rotated_image

    def update(self, context=None):
        self.surface.blit(self.back_button["current_image"], self.back_button["rect"])
        self.surface.blit(self.pic_circle["bg_image"], self.pic_circle["rect"])
        self.surface.blit(self.rotated_pic_circle(), self.pic_circle["border_rect"])


TRAITS_SCHEMA = {
    "font": pygame.font.Font(Fonts.PixelifySans, 21),
    "text_color": pygame.Color(26, 26, 26),
    "bg_color": pygame.Color(74, 227, 181),
    "options": [
        {
            "Initial Population": {
                "choices": {
                    "user_input": {"selected": False, "surface": None, "switched_surface": None}
                },
                "type": int,
                "surface": None,
                "switched_surface": None
            },
            "Species": {
                "choices": {
                    "user_input": {"selected": False, "surface": None, "switched_surface": None}
                },
                "type": str,
                "surface": None,
                "switched_surface": None
            },
            "Traitline": {
                "choices": [
                    {"value": "Swordling", "selected": True, "surface": None, "switched_surface": None},
                    {"value": "Mineling", "selected": False, "surface": None, "switched_surface": None},
                    {"value": "Shieldling", "selected": False, "surface": None, "switched_surface": None},
                    {"value": "Camoufling", "selected": False, "surface": None, "switched_surface": None},
                ],
                "type": "single choice list",
                "surface": None,
                "switched_surface": None
            },
            "Domain": {
                "choices": [
                    {"value": "Square", "selected": True, "surface": None, "switched_surface": None},
                    {"value": "Circle", "selected": False, "surface": None, "switched_surface": None},
                    {"value": "Triangle", "selected": False, "surface": None, "switched_surface": None},
                    {"value": "Camoufling", "selected": False, "surface": None, "switched_surface": None},
                ],
                "type": "single choice list",
                "surface": None,
                "switched_surface": None
            },
            "Kingdom": {
                "choices": [
                    {"value": "Predator", "selected": True, "surface": None, "switched_surface": None},
                    {"value": "Prey", "selected": False, "surface": None, "switched_surface": None},
                ],
                "type": "single choice list",
                "surface": None,
                "switched_surface": None
            },
            "Vision Radius": {
                "choices": {
                    "user_input": {"selected": False, "surface": None, "switched_surface": None}
                },
                "type": int,
                "surface": None,
                "switched_surface": None
            },
            "Size": {
                "choices": {
                    "user_input": {"selected": False, "surface": None, "switched_surface": None}
                },
                "type": int,
                "surface": None,
                "switched_surface": None
            },
            "Color": {
                "choices": {
                    "user_input": {"selected": False, "surface": None, "switched_surface": None}
                },
                "type": "color",
                "surface": None,
                "switched_surface": None
            },
            "Speed": {
                "choices": {
                    "user_input": {"selected": False, "surface": None, "switched_surface": None}
                },
                "type": int,
                "surface": None,
                "switched_surface": None
            },
            "Max Energy": {
                "choices": {
                    "user_input": {"selected": False, "surface": None, "switched_surface": None}
                },
                "type": int,
                "surface": None,
                "switched_surface": None
            },
            "Blood Thirsty": {
                "choices": [
                    {"value": "False", "selected": True, "surface": None, "switched_surface": None},
                    {"value": "True", "selected": False, "surface": None, "switched_surface": None},
                ],
                "type": "single choice list",
                "surface": None,
                "switched_surface": None
            },
        }
    ],
}
