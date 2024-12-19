import os
import pygame
from config import Fonts, image_assets


class LaboratoryComponent:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface
        self.surface = pygame.image.load(
            os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
        )
        self.time = 0

        self.configure_back_button(main_surface)
        self.configure_dp_circle()

        self.configure_traits_schema(main_surface)
        self.configure_unleash_organism_button(main_surface)

    def configure_traits_schema(self, main_surface):
        self.traits_schema = self.initialize_traits_schema()
        self.create_option_surfaces(main_surface)

    def initialize_traits_schema(self):
        return {
            "font": pygame.font.Font(Fonts.PixelifySansMedium, 21),
            "text_color": pygame.Color(0, 0, 0),
            "bg_color": pygame.Color(74, 227, 181),
            "yIncrement": 34,
            "highlight_width": 25,
            "options": {
                "Initial Population: ": {
                    "selected": True,
                    "type": "user_input_int",
                    "data": 100,
                },
                "Species: ": {
                    "selected": True,
                    "type": "user_input_str",
                    "data": "",
                },
                "Traitline: ": {
                    "choices": [
                        {"value": "Swordling", "selected": True},
                        {"value": "Mineling", "selected": False},
                        {"value": "Shieldling", "selected": False},
                        {"value": "Camoufling", "selected": False},
                    ],
                    "type": "single_choice_list",
                },
                "Domain: ": {
                    "choices": [
                        {"value": "Square", "selected": True},
                        {"value": "Circle", "selected": False},
                        {"value": "Triangle", "selected": False},
                        {"value": "Rhombus", "selected": False},
                    ],
                    "type": "single_choice_list",
                },
                "Kingdom: ": {
                    "choices": [
                        {"value": "Predator", "selected": False},
                        {"value": "Prey", "selected": True},
                    ],
                    "type": "single_choice_list",
                },
                "Vision Radius: ": {
                    "selected": False,
                    "type": "user_input_int",
                    "data": 0,
                },
                "Size: ": {
                    "selected": False,
                    "type": "user_input_int",
                    "data": 0,
                },
                "Color: ": {
                    "selected": False,
                    "type": "user_input_color",
                    "data": 0,
                },
                "Speed: ": {
                    "selected": False,
                    "type": "user_input_int",
                    "data": 0,
                },
                "Max Energy: ": {
                    "selected": False,
                    "type": "user_input_int",
                    "data": 0,
                },
                "Blood Thirsty: ": {
                    "choices": [
                        {"value": "False", "selected": True},
                        {"value": "True", "selected": False},
                    ],
                    "type": "single_choice_list",
                },
            },
        }

    def create_option_surfaces(self, main_surface):
        x, y = 75, 350
        for option, value in self.traits_schema["options"].items():
            option_surface = self.create_option_surface(option)
            self.configure_option_rhs(option, value, option_surface, x, y, main_surface)
            self.traits_schema["options"][option]["surface"] = option_surface
            self.traits_schema["options"][option]["rect"] = option_surface.get_rect(
                topleft=(x, y)
            )
            y += self.traits_schema["yIncrement"]

    def create_option_surface(self, option):
        option_surface = pygame.Surface(
            (1000, self.traits_schema["highlight_width"]),
        )
        option_surface.fill(self.traits_schema["bg_color"])

        text_surface = pygame.Surface(
            (200, self.traits_schema["highlight_width"]),
        )
        text_surface.fill(self.traits_schema["bg_color"])
        text = self.traits_schema["font"].render(
            option,
            True,
            self.traits_schema["text_color"],
            self.traits_schema["bg_color"],
        )
        text_surface.blit(text, (0, 0))
        option_surface.blit(text_surface, (0, 0))

        return option_surface

    def configure_option_rhs(self, option, value, option_surface, x, y, main_surface):
        if value["type"] == "user_input_int":
            self.configure_user_input_int(value, option_surface)
        elif value["type"] == "user_input_str":
            self.configure_user_input_str(value, option_surface)
        elif value["type"] == "single_choice_list":
            self.configure_single_choice_list(value, option_surface, x, y, main_surface)

    def configure_user_input_int(self, value, option_surface):
        data = "{:,}".format(value["data"])
        if value["selected"] and (self.time // 20) % 2 == 0:
            data += "_"

        text = self.traits_schema["font"].render(
            data,
            True,
            self.traits_schema["bg_color"],
            self.traits_schema["text_color"],
        )
        text_surface = pygame.Surface(
            (
                text.get_width() + 15,
                self.traits_schema["highlight_width"],
            )
        )
        text_surface.blit(text, (5, 0))
        option_surface.blit(text_surface, (200, 0))

    def configure_user_input_str(self, value, option_surface):
        data = value["data"]
        if value["selected"] and (self.time // 20) % 2 == 0:
            data += "_"

        text = self.traits_schema["font"].render(
            data,
            True,
            self.traits_schema["bg_color"],
            self.traits_schema["text_color"],
        )
        text_surface = pygame.Surface(
            (
                text.get_width() + 15,
                self.traits_schema["highlight_width"],
            )
        )
        text_surface.blit(text, (5, 0))
        option_surface.blit(text_surface, (200, 0))

    def configure_single_choice_list(self, value, option_surface, x, y, main_surface):
        choice_x = 200
        for choice in value["choices"]:
            for state, color in [
                ("surface", self.traits_schema["bg_color"]),
                ("surface_selected", self.traits_schema["text_color"]),
            ]:
                text = self.traits_schema["font"].render(
                    choice["value"],
                    True,
                    (
                        self.traits_schema["text_color"]
                        if state == "surface"
                        else self.traits_schema["bg_color"]
                    ),
                    color,
                )
                choice_surface = pygame.Surface(
                    (
                        text.get_width() + 10,
                        self.traits_schema["highlight_width"],
                    )
                )
                choice_surface.fill(color)
                choice_surface.blit(text, (5, 0))
                choice[state] = choice_surface

            choice["rect"] = choice["surface"].get_rect(topleft=(x + choice_x, y))
            choice["absolute_rect"] = choice["surface"].get_rect(
                topleft=(
                    x
                    + choice_x
                    + ((main_surface.get_width() - self.surface.get_width()) // 2),
                    y + ((main_surface.get_height() - self.surface.get_height()) // 2),
                )
            )
            choice_x += choice["surface"].get_width() + 10

    def configure_unleash_organism_button(self, main_surface):
        self.unleash_organism_button = {
            "current_image": None,
            "image": pygame.image.load(
                os.path.join(image_assets, "laboratory", "unleash_organism_button.svg")
            ),
            "clicked_image": pygame.image.load(
                os.path.join(
                    image_assets, "laboratory", "unleash_organism_button_clicked.svg"
                )
            ),
            "position": {"topleft": (70, self.surface.get_height() - 150)},
        }
        self.unleash_organism_button["rect"] = self.unleash_organism_button.get(
            "image"
        ).get_rect(**self.unleash_organism_button["position"])

        self.unleash_organism_button[
            "absolute_rect"
        ] = self.unleash_organism_button.get("image").get_rect(
            topleft=(
                70 + ((main_surface.get_width() - self.surface.get_width()) // 2),
                self.surface.get_height()
                - 150
                + ((main_surface.get_height() - self.surface.get_height()) // 2),
            )
        )

        self.unleash_organism_button["current_image"] = (
            self.unleash_organism_button.get("image")
        )

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

            elif self.unleash_organism_button["absolute_rect"].collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.unleash_organism_button["current_image"] = (
                        self.unleash_organism_button["clicked_image"]
                    )
                elif event.type == pygame.MOUSEBUTTONUP:
                    yield "navigate_home"
            else:
                self.back_button["current_image"] = self.back_button["image"]
                self.unleash_organism_button["current_image"] = (
                    self.unleash_organism_button["image"]
                )
            for option, value in self.traits_schema["options"].items():
                if value["type"] == "single_choice_list":
                    selected_choice = None
                    for choice in value["choices"]:
                        if choice["absolute_rect"].collidepoint(event.pos):
                            if event.type == pygame.MOUSEBUTTONDOWN:
                                selected_choice = choice["value"]

                    if selected_choice:
                        for choice in value["choices"]:
                            choice["selected"] = choice["value"] == selected_choice

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
        self.time += 1
        self.surface.blit(self.back_button["current_image"], self.back_button["rect"])
        self.surface.blit(self.pic_circle["bg_image"], self.pic_circle["rect"])
        self.surface.blit(self.rotated_pic_circle(), self.pic_circle["border_rect"])
        self.surface.blit(
            self.unleash_organism_button["current_image"],
            self.unleash_organism_button["rect"],
        )

        for option, value in self.traits_schema["options"].items():
            self.surface.blit(
                value["surface"],
                value["rect"],
            )

            if value["type"] == "single_choice_list":
                for choice in value["choices"]:
                    self.surface.blit(
                        (
                            choice["surface_selected"]
                            if choice["selected"]
                            else choice["surface"]
                        ),
                        choice["rect"],
                    )
            elif value["type"] == "user_input_int":
                self.configure_user_input_int(value, value["surface"])
            elif value["type"] == "user_input_str":
                self.configure_user_input_str(value, value["surface"])
