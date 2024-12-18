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
            "font": pygame.font.Font(Fonts.PixelifySansMedium, 21),
            "text_color": pygame.Color(0, 0, 0),
            "bg_color": pygame.Color(74, 227, 181),
            "yIncrement": 34,
            "options": {
                "Initial Population: ": {
                    "choices": {"user_input": {"selected": False}},
                    "type": int,
                },
                "Species: ": {
                    "choices": {"user_input": {"selected": False}},
                    "type": str,
                },
                "Traitline: ": {
                    "choices": [
                        {"value": "Swordling", "selected": True},
                        {"value": "Mineling", "selected": False},
                        {"value": "Shieldling", "selected": False},
                        {"value": "Camoufling", "selected": False},
                    ],
                    "type": "single choice list",
                },
                "Domain: ": {
                    "choices": [
                        {"value": "Square", "selected": True},
                        {"value": "Circle", "selected": False},
                        {"value": "Triangle", "selected": False},
                        {"value": "Camoufling", "selected": False},
                    ],
                    "type": "single choice list",
                },
                "Kingdom: ": {
                    "choices": [
                        {"value": "Predator", "selected": False},
                        {"value": "Prey", "selected": False},
                    ],
                    "type": "single choice list",
                },
                "Vision Radius: ": {
                    "choices": {"user_input": {"selected": False}},
                    "type": int,
                },
                "Size: ": {
                    "choices": {"user_input": {"selected": False}},
                    "type": int,
                },
                "Color: ": {
                    "choices": {"user_input": {"selected": False}},
                    "type": "color",
                },
                "Speed: ": {
                    "choices": {"user_input": {"selected": False}},
                    "type": int,
                },
                "Max Energy: ": {
                    "choices": {"user_input": {"selected": False}},
                    "type": int,
                },
                "Blood Thirsty: ": {
                    "choices": [
                        {"value": "False", "selected": True},
                        {"value": "True", "selected": False},
                    ],
                    "type": "single choice list",
                },
            },
        }

        option_x, option_y = 75, 350
        for option, value in self.traits_schema["options"].items():
            text_surface = pygame.Surface((200, 30))
            text_surface.fill(self.traits_schema["bg_color"])
            text = self.traits_schema["font"].render(
                option,
                True,
                self.traits_schema["text_color"],
                self.traits_schema["bg_color"],
            )
            text_surface.blit(text, (0, 0))
            self.traits_schema["options"][option]["surface"] = text_surface
            self.traits_schema["options"][option]["rect"] = text_surface.get_rect(
                topleft=(option_x, option_y)
            )
            option_y += self.traits_schema["yIncrement"]

        # self.unleash_organisms_button = {
        #     "image" : pygame.image.load(
        #         os.path.join(image_assets, 'laboratory', )
        #     )
        # }

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

        for option, value in self.traits_schema["options"].items():
            self.surface.blit(
                value["surface"],
                value["rect"],
            )
        # self.surface.blit(self.traits_schema_titles, self.traits_schema_titles_rect)
