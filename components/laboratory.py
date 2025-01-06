import os
import re

import numpy as np
import pygame

from config import Fonts, image_assets
from enums import EventType, MessagePacket, MessagePackets


class LaboratoryComponent:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface
        self.bg_image = pygame.image.load(
            os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
        )
        self.sub_component_states = {
            "sub_components": ["attributes_lab"],
            "current_sub_component": "attributes_lab",
        }
        self.surface = pygame.Surface(size=(self.bg_image.get_size()))
        self.configure_back_button()
        self.attributes_lab = AttributesLab(main_surface, context)

    def update(self, context=None):
        self.surface.blit(self.bg_image, (0, 0))
        self.surface.blit(self.back_button["current_image"], self.back_button["rect"])
        self.attributes_lab.update(context)
        self.surface.blit(self.attributes_lab.surface, (0, 0))

    def configure_back_button(self):
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
                50 + ((self.main_surface.get_width() - self.surface.get_width()) // 2),
                50
                + ((self.main_surface.get_height() - self.surface.get_height()) // 2),
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
                    yield MessagePackets(MessagePacket(EventType.NAVIGATION, "home"))

        yield from self.attributes_lab._event_handler(event)


class NeuralLab:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface
        self.surface = pygame.Surface(
            size=(
                pygame.image.load(
                    os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
                ).get_size()
            ),
            flags=pygame.SRCALPHA,
        )

    def _event_handler(self, main_surface):
        pass


class AttributesLab:
    def __init__(self, main_surface, context=None):
        self.time = 0
        self.main_surface = main_surface
        self.surface = pygame.Surface(
            size=(
                pygame.image.load(
                    os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
                ).get_size()
            ),
            flags=pygame.SRCALPHA,
        )

        self.attrs_lab_text = pygame.image.load(
            os.path.join(image_assets, "laboratory", "lab_intro_text.svg")
        )
        self.surface.blit(
            self.attrs_lab_text,
            self.attrs_lab_text.get_rect(topleft=(75, 225)),
        )

        self.configure_dp_circle()

        self.configure_traits_schema()
        self.configure_neural_network_button()

    def configure_traits_schema(self):
        self.traits_schema = self.initialize_traits_schema()
        self.create_option_surfaces()

    def get_user_input(self):
        return {
            "initial_population": int(
                self.traits_schema["options"]["Initial Population: "]["data"]
            ),
        }

    def initialize_traits_schema(self):
        return {
            "font": pygame.font.Font(Fonts.PixelifySansMedium, 21),
            "text_color": pygame.Color(0, 0, 0),
            "bg_color": pygame.Color(74, 227, 181),
            "yIncrement": 34,
            "highlight_width": 25,
            "selected_option": "Initial Population: ",
            "options": {
                "Initial Population: ": {
                    "selected": True,
                    "type": "user_input_int",
                    "data": "100",
                },
                "Species: ": {
                    "selected": False,
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
                        {"value": "Squarionidae", "selected": True},
                        {"value": "Circulonidae", "selected": False},
                        {"value": "Trigonidae", "selected": False},
                        {"value": "Rhombronidae", "selected": False},
                    ],
                    "type": "single_choice_list",
                },
                "Vision Radius: ": {
                    "selected": False,
                    "type": "user_input_int",
                    "data": "0",
                },
                "Size: ": {
                    "selected": False,
                    "type": "user_input_int",
                    "data": "0",
                },
                "Color: ": {
                    "selected": False,
                    "type": "user_input_color",
                    "data": "1A1A1A",
                },
                "Speed: ": {
                    "selected": False,
                    "type": "user_input_int",
                    "data": "0",
                },
                "Max Energy: ": {
                    "selected": False,
                    "type": "user_input_int",
                    "data": "0",
                },
            },
        }

    def create_option_surfaces(self):
        x, y = 75, 350
        for option, value in self.traits_schema["options"].items():
            option_surface = self.create_option_surface(option)
            self.configure_option_rhs(option, value, option_surface, x, y)
            self.traits_schema["options"][option]["surface"] = option_surface
            self.traits_schema["options"][option]["rect"] = option_surface.get_rect(
                topleft=(x, y)
            )
            y += self.traits_schema["yIncrement"]

    def create_option_surface(self, option):
        option_surface = pygame.Surface((1000, self.traits_schema["highlight_width"]))
        option_surface.fill(self.traits_schema["bg_color"])

        text_surface = pygame.Surface((900, self.traits_schema["highlight_width"]))
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

    def configure_option_rhs(self, option, value, option_surface, x, y):
        if value["type"] == "user_input_int":
            self.configure_user_input(value, option_surface, x, y, input_type="int")
        elif value["type"] == "user_input_str":
            self.configure_user_input(value, option_surface, x, y, input_type="str")
        elif value["type"] == "user_input_color":
            self.configure_user_input(value, option_surface, x, y, input_type="color")
        elif value["type"] == "single_choice_list":
            self.configure_single_choice_list(value, option_surface, x, y)

    def configure_user_input(self, value, option_surface, x, y, input_type="str"):
        data = value["data"]
        if input_type == "int":
            data = "{:,}".format(int(value["data"]))
        elif input_type == "color":
            data = "#" + data

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
        value["absolute_rect"] = text_surface.get_rect(
            topleft=(
                x
                + 200
                + ((self.main_surface.get_width() - self.surface.get_width()) // 2),
                y + ((self.main_surface.get_height() - self.surface.get_height()) // 2),
            )
        )

    def configure_single_choice_list(self, value, option_surface, x, y):
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
                    + ((self.main_surface.get_width() - self.surface.get_width()) // 2),
                    y
                    + (
                        (self.main_surface.get_height() - self.surface.get_height())
                        // 2
                    ),
                )
            )
            choice_x += choice["surface"].get_width() + 10

    def configure_neural_network_button(self):
        self.neural_network_button = {
            "current_image": None,
            "image": pygame.image.load(
                os.path.join(image_assets, "laboratory", "neural_network_button.svg")
            ),
            "clicked_image": pygame.image.load(
                os.path.join(
                    image_assets, "laboratory", "neural_network_button_clicked.svg"
                )
            ),
            "position": {
                "topright": (
                    self.surface.get_width() - 50,
                    self.surface.get_height() - 150,
                )
            },
        }
        self.neural_network_button["rect"] = self.neural_network_button.get(
            "image"
        ).get_rect(**self.neural_network_button["position"])

        self.neural_network_button["absolute_rect"] = self.neural_network_button.get(
            "image"
        ).get_rect(
            topleft=(
                np.array(self.neural_network_button["rect"].topleft)
                + np.array(
                    (
                        (self.main_surface.get_width() - self.surface.get_width()) // 2,
                        (self.main_surface.get_height() - self.surface.get_height())
                        // 2,
                    )
                )
            )
        )

        self.neural_network_button["current_image"] = self.neural_network_button.get(
            "image"
        )

    def configure_dp_circle(self):
        self.pic_circle = {
            "organism_image": pygame.image.load(
                os.path.join(image_assets, "creatures", "triangle.svg"),
            ),
            "organism_angle": 0,
            "border_angle": 0,
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
        self.pic_circle["organism_rect"] = self.pic_circle["organism_image"].get_rect(
            **self.pic_circle["position"]
        )

    def _event_handler(self, event):
        selected_option = self.traits_schema.get("selected_option")
        selected_option_type = self.traits_schema["options"][selected_option]["type"]
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            if self.neural_network_button["absolute_rect"].collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.neural_network_button["current_image"] = (
                        self.neural_network_button["clicked_image"]
                    )
                elif event.type == pygame.MOUSEBUTTONUP:
                    yield MessagePackets(
                        MessagePacket(
                            EventType.NAVIGATION,
                            "home",
                        ),
                        MessagePacket(
                            EventType.OTHER,
                            "create_organism",
                            context=self.get_user_input(),
                        ),
                    )
            else:
                self.back_button["current_image"] = self.back_button["image"]
                self.neural_network_button["current_image"] = (
                    self.neural_network_button["image"]
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

                elif value["type"] in [
                    "user_input_int",
                    "user_input_str",
                    "user_input_color",
                ]:
                    if value["absolute_rect"].collidepoint(event.pos):
                        if event.type == pygame.MOUSEBUTTONDOWN:
                            value["selected"] = True
                            self.traits_schema["selected_option"] = option
                    else:
                        value["selected"] = False

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.traits_schema["options"][selected_option]["data"] = (
                    self.traits_schema["options"][selected_option]["data"][:-1]
                )
            elif re.match("[a-zA-Z0-9 ]", event.unicode):
                if selected_option_type == "user_input_str":
                    self.traits_schema["options"][selected_option][
                        "data"
                    ] += event.unicode
                elif selected_option_type == "user_input_color":
                    data = self.traits_schema["options"][selected_option]["data"]
                    if len(data) < 6 and re.match("[a-fA-F0-9]", event.unicode):
                        self.traits_schema["options"][selected_option]["data"] = (
                            data + event.unicode
                        )

                elif selected_option_type == "user_input_int":
                    self.traits_schema["options"][selected_option]["data"] += (
                        event.unicode if event.unicode.isdigit() else ""
                    )

            elif event.key == pygame.K_TAB:
                selected_option_index = list(
                    self.traits_schema["options"].keys()
                ).index(selected_option)
                next_option = list(self.traits_schema["options"].keys())[
                    (selected_option_index + 1) % len(self.traits_schema["options"])
                ]
                self.traits_schema["selected_option"] = next_option
                self.traits_schema["options"][selected_option]["selected"] = False
                self.traits_schema["options"][next_option]["selected"] = True

            elif event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
                if selected_option_type == "single_choice_list":
                    selected_index = 0
                    for i, choice in enumerate(
                        self.traits_schema["options"][selected_option]["choices"]
                    ):
                        if choice["selected"]:
                            selected_index = i
                            break

                    if event.key == pygame.K_LEFT:
                        new_index = (selected_index - 1) % len(
                            self.traits_schema["options"][selected_option]["choices"]
                        )
                    else:
                        new_index = (selected_index + 1) % len(
                            self.traits_schema["options"][selected_option]["choices"]
                        )

                    for i, choice in enumerate(
                        self.traits_schema["options"][selected_option]["choices"]
                    ):
                        choice["selected"] = i == new_index

    def rotate_pic_circle_border(self):
        self.pic_circle["border_angle"] += 1
        rotated_image = pygame.transform.rotate(
            self.pic_circle["border_image"], self.pic_circle["border_angle"]
        )
        self.pic_circle["border_rect"] = rotated_image.get_rect(
            center=self.pic_circle["rect"].center
        )
        return rotated_image

    def rotate_pic_circle_organism(self):
        self.pic_circle["organism_angle"] += 1
        rotated_image = pygame.transform.rotate(
            self.pic_circle["organism_image"], self.pic_circle["organism_angle"]
        )
        self.pic_circle["organism_rect"] = rotated_image.get_rect(
            center=self.pic_circle["rect"].center
        )
        return rotated_image

    def update_user_input(self, value, option_surface, input_type="str"):
        data = value["data"]
        if input_type == "int":
            data = "{:,}".format(int(value["data"] or 0))
        elif input_type == "color":
            data = "#" + data.ljust(6, "-").upper()

        if value["selected"] and (self.time // 20) % 2 == 0:
            data += "_"

        text = self.traits_schema["font"].render(
            data,
            True,
            self.traits_schema["bg_color"],
            self.traits_schema["text_color"],
        )
        text_bg = pygame.Surface(
            (
                # text width of "_" is 9
                text.get_width() + (11 if data.endswith("_") else 20),
                self.traits_schema["highlight_width"],
            )
        )
        text_surface = pygame.Surface(
            (
                800,
                self.traits_schema["highlight_width"],
            )
        )
        text_bg.fill(self.traits_schema["text_color"])
        text_bg.blit(text, (5, 0))
        text_surface.fill(self.traits_schema["bg_color"])
        text_surface.blit(text_bg, (0, 0))
        option_surface.blit(text_surface, (200, 0))

    def update(self, context=None):
        self.time += 1
        self.surface.blit(self.pic_circle["bg_image"], self.pic_circle["rect"])
        self.surface.blit(
            self.rotate_pic_circle_organism(), self.pic_circle["organism_rect"]
        )
        self.surface.blit(
            self.rotate_pic_circle_border(), self.pic_circle["border_rect"]
        )
        self.surface.blit(
            self.neural_network_button["current_image"],
            self.neural_network_button["rect"],
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
                self.update_user_input(value, value["surface"], input_type="int")
            elif value["type"] == "user_input_str":
                self.update_user_input(value, value["surface"], input_type="str")
            elif value["type"] == "user_input_color":
                self.update_user_input(value, value["surface"], input_type="color")
