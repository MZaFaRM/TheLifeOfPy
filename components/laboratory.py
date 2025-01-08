import contextlib
import os
import re

import numpy as np
import pygame

from config import Colors, Fonts, image_assets
from enums import EventType, MessagePacket, MessagePackets


class LaboratoryComponent:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface
        self.bg_image = pygame.image.load(
            os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
        )
        self.user_inputs = {}
        self.surface = pygame.Surface(size=(self.bg_image.get_size()))
        self.__configure_back_button()

        self.curr_sub_component = "attrs_lab"
        self.sub_component_states = {
            "attrs_lab": AttributesLab(main_surface, context),
            "neural_lab": NeuralLab(main_surface, context),
        }

    def update(self, context=None):
        self.surface.blit(self.bg_image, (0, 0))
        self.surface.blit(self.back_button["current_image"], self.back_button["rect"])
        sub_component = self.sub_component_states[self.curr_sub_component]
        sub_component.update(context)
        self.surface.blit(sub_component.surface, (0, 0))

    def event_handler(self, event):
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            # Check if the back button is clicked
            if self.back_button["absolute_rect"].collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    # Set the back button to its clicked image when the button is pressed
                    self.back_button["current_image"] = self.back_button[
                        "clicked_image"
                    ]

                elif event.type == pygame.MOUSEBUTTONUP:
                    # Handle the action when the button is released
                    if self.curr_sub_component == "neural_lab":
                        # If in the "neural_lab", go back to "attrs_lab"
                        self.curr_sub_component = "attrs_lab"
                        self.back_button["current_image"] = self.back_button["image"]
                    else:
                        # If not in "neural_lab", navigate to home
                        yield MessagePackets(
                            MessagePacket(EventType.NAVIGATION, "home")
                        )

        # Handle the events for the current subcomponent
        packets = self.sub_component_states.get(self.curr_sub_component).event_handler(
            event
        )

        if packets is not None:
            # Process each packet received from the subcomponent handler
            packet = next(packets, None)
            if packet:
                if packet == MessagePacket(EventType.NAVIGATION, "neural_lab"):
                    # Navigate to "neural_lab" subcomponent and store its context
                    self.curr_sub_component = "neural_lab"
                    self.user_inputs = packet.context
                else:
                    # Yield the packet as is
                    yield MessagePackets(packet)
        else:
            # If no packets were returned, set packet to None
            packet = None

    def __configure_back_button(self):
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


class NeuralLab:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface
        self.selected_sensor = None

        surface = self.__setup_surface()

        self.surface = surface
        self.__configure_sensors(
            sensors=["Nil", "Dfd", "Bfs", "Cfl", "Dia", "Fwa", "Car", "Nil"]
        )

    def event_handler(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            for sensor in self.sensors:
                if sensor["absolute_rect"].collidepoint(event.pos):
                    # Select the sensor if clicked
                    self.selected_sensor = sensor
                    sensor["current_surface"] = sensor["clicked_surface"]
                    break  # No need to check other sensors after selection

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.selected_sensor:
                for sensor in self.sensors:
                    if sensor != self.selected_sensor:
                        # Reset all non-selected sensors to their origi nal surface
                        sensor["current_surface"] = sensor["surface"]
                # If the mouse is not on the selected sensor, unselect it
                if not self.selected_sensor["absolute_rect"].collidepoint(event.pos):
                    self.selected_sensor["current_surface"] = self.selected_sensor[
                        "surface"
                    ]
                self.selected_sensor = None  # Deselect the sensor

    def update(self, context=None):
        for sensor in self.sensors:
            self.surface.blit(sensor["current_surface"], sensor["rect"])

    def __setup_surface(self):
        surface = pygame.Surface(
            size=(
                pygame.image.load(
                    os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
                ).get_size()
            ),
            flags=pygame.SRCALPHA,
        )
        intro_text = pygame.image.load(
            os.path.join(
                image_assets, "laboratory", "neural_lab", "neural_lab_intro.svg"
            )
        )
        surface.blit(
            intro_text,
            intro_text.get_rect(topleft=(75, 225)),
        )

        sensor_title = pygame.image.load(
            os.path.join(image_assets, "laboratory", "neural_lab", "sensor_title.svg")
        )
        surface.blit(sensor_title, sensor_title.get_rect(topleft=(75, 400)))

        return surface

    def __configure_sensors(self, sensors):
        font = pygame.font.Font(Fonts.PixelifySansMedium, 20)
        num_sensors = len(sensors)
        self.sensors = []  # Use this list to store sensor data
        columns = [120 + (i * 65) for i in range(3)]
        y_start = 480
        spacing = 60

        # Adjust y_offset if the number of sensors is odd
        y_offset = spacing // 2 if num_sensors % 2 != 0 else 0

        for i in range(num_sensors):
            column_index = i % 3
            x = columns[column_index]
            y = y_start + (i // 3) * spacing + (y_offset if column_index != 1 else 0)

            # Create a new surface for each sensor
            sensor_surface = pygame.Surface((50, 50))
            sensor_surface.fill(color=Colors.primary)
            pygame.draw.circle(sensor_surface, Colors.bg_color, (25, 25), 25)
            pygame.draw.circle(sensor_surface, Colors.primary, (25, 25), 22)

            # Render title text for each sensor
            text = font.render(sensors[i], True, Colors.bg_color)
            sensor_surface.blit(text, text.get_rect(center=(25, 25)))

            # Create a new surface clicked look for each sensor
            clicked_sensor_surface = pygame.Surface((50, 50))
            clicked_sensor_surface.fill(color=Colors.primary)
            pygame.draw.circle(clicked_sensor_surface, Colors.primary, (25, 25), 25)
            pygame.draw.circle(clicked_sensor_surface, Colors.bg_color, (25, 25), 22)

            # Render title text for each sensor
            text = font.render(sensors[i], True, Colors.primary)
            clicked_sensor_surface.blit(text, text.get_rect(center=(25, 25)))

            # Add sensor data to the self.sensors list
            self.sensors.append(
                {
                    "name": sensors[i],
                    "current_surface": sensor_surface,
                    "surface": sensor_surface,
                    "clicked_surface": clicked_sensor_surface,
                    "rect": sensor_surface.get_rect(center=(x, y)),
                    "absolute_rect": sensor_surface.get_rect(
                        topleft=(
                            x
                            - 25
                            + +(
                                (
                                    self.main_surface.get_width()
                                    - self.surface.get_width()
                                )
                                // 2
                            ),
                            y
                            - 25
                            + +(
                                (
                                    self.main_surface.get_height()
                                    - self.surface.get_height()
                                )
                                // 2
                            ),
                        )
                    ),
                }
            )


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

        self.__configure_dp_circle()

        self.__configure_traits_schema()
        self.__configure_neural_network_button()

    def update(self, context=None):
        self.time += 1
        self.surface.blit(self.pic_circle["bg_image"], self.pic_circle["rect"])
        self.surface.blit(
            self.__rotate_pic_circle_organism(), self.pic_circle["organism_rect"]
        )
        self.surface.blit(
            self.__rotate_pic_circle_border(), self.pic_circle["border_rect"]
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
                self.__update_user_input(value, value["surface"], input_type="int")
            elif value["type"] == "user_input_str":
                self.__update_user_input(value, value["surface"], input_type="str")
            elif value["type"] == "user_input_color":
                self.__update_user_input(value, value["surface"], input_type="color")

    def event_handler(self, event):
        selected_option = self.traits_schema.get("selected_option")
        selected_option_type = self.traits_schema["options"][selected_option]["type"]

        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            # Handle the button click events
            if self.__handle_neural_network_button(event):
                yield self.__navigate_to_neural_lab()

            # Handle interaction with traits options
            self.__handle_traits_options(event, selected_option)

        elif event.type == pygame.KEYDOWN:
            # Handle keyboard events (backspace, alphanumeric, navigation)
            self.__handle_keydown_event(event, selected_option, selected_option_type)

    def get_user_input(self):
        return {
            "initial_population": int(
                self.traits_schema["options"]["Initial Population: "]["data"]
            ),
        }

    def __configure_traits_schema(self):
        self.traits_schema = self.__initialize_traits_schema()
        self.__create_option_surfaces()

    def __initialize_traits_schema(self):
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

    def __create_option_surfaces(self):
        x, y = 75, 400
        for option, value in self.traits_schema["options"].items():
            option_surface = self.__create_option_surface(option)
            self.__configure_option_rhs(option, value, option_surface, x, y)
            self.traits_schema["options"][option]["surface"] = option_surface
            self.traits_schema["options"][option]["rect"] = option_surface.get_rect(
                topleft=(x, y)
            )
            y += self.traits_schema["yIncrement"]

    def __create_option_surface(self, option):
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

    def __configure_option_rhs(self, option, value, option_surface, x, y):
        if value["type"] == "user_input_int":
            self.__configure_user_input(value, option_surface, x, y, input_type="int")
        elif value["type"] == "user_input_str":
            self.__configure_user_input(value, option_surface, x, y, input_type="str")
        elif value["type"] == "user_input_color":
            self.__configure_user_input(value, option_surface, x, y, input_type="color")
        elif value["type"] == "single_choice_list":
            self.__configure_single_choice_list(value, option_surface, x, y)

    def __configure_user_input(self, value, option_surface, x, y, input_type="str"):
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

    def __configure_single_choice_list(self, value, option_surface, x, y):
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

    def __configure_neural_network_button(self):
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

    def __configure_dp_circle(self):
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

    def __handle_neural_network_button(self, event):
        """Handle neural network button clicks."""
        if self.neural_network_button["absolute_rect"].collidepoint(event.pos):
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.neural_network_button["current_image"] = (
                    self.neural_network_button["clicked_image"]
                )
            elif event.type == pygame.MOUSEBUTTONUP:
                return True  # Proceed with navigation if clicked
        else:
            # Reset the button image when not clicked
            self.neural_network_button["current_image"] = self.neural_network_button[
                "image"
            ]
        return False

    def __navigate_to_neural_lab(self):
        """Return the navigation message for neural lab."""
        return MessagePacket(
            EventType.NAVIGATION,
            "neural_lab",
            context=self.get_user_input(),
        )

    def __handle_traits_options(self, event, selected_option):
        """Handle interactions with traits options."""
        for option, value in self.traits_schema["options"].items():
            if value["type"] == "single_choice_list":
                self.__handle_single_choice_list(event, value)
            elif value["type"] in [
                "user_input_int",
                "user_input_str",
                "user_input_color",
            ]:
                self.__handle_user_input(event, value, option)

    def __handle_single_choice_list(self, event, value):
        """Handle single choice list interaction."""
        selected_choice = None
        for choice in value["choices"]:
            if choice["absolute_rect"].collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    selected_choice = choice["value"]

        if selected_choice:
            for choice in value["choices"]:
                choice["selected"] = choice["value"] == selected_choice

    def __handle_user_input(self, event, value, option):
        """Handle user input (text, color, integer)."""
        if value["absolute_rect"].collidepoint(event.pos):
            if event.type == pygame.MOUSEBUTTONDOWN:
                value["selected"] = True
                self.traits_schema["selected_option"] = option
        else:
            value["selected"] = False

    def __handle_keydown_event(self, event, selected_option, selected_option_type):
        """Handle keydown events for user input and navigation."""
        if event.key == pygame.K_BACKSPACE:
            self.__handle_backspace(selected_option)
        elif re.match("[a-zA-Z0-9 ]", event.unicode):
            self.__handle_alphanumeric_input(
                event, selected_option, selected_option_type
            )
        elif event.key == pygame.K_TAB:
            self.__handle_tab_navigation(selected_option, selected_option_type)
        elif event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
            self.__handle_arrow_navigation(event, selected_option, selected_option_type)

    def __handle_backspace(self, selected_option):
        """Handle backspace for input fields."""
        self.traits_schema["options"][selected_option]["data"] = self.traits_schema[
            "options"
        ][selected_option]["data"][:-1]

    def __handle_alphanumeric_input(self, event, selected_option, selected_option_type):
        """Handle alphanumeric input for text, color, or integer fields."""
        if selected_option_type == "user_input_str":
            self.traits_schema["options"][selected_option]["data"] += event.unicode
        elif selected_option_type == "user_input_color":
            self.__handle_color_input(event, selected_option)
        elif selected_option_type == "user_input_int":
            self.__handle_int_input(event, selected_option)

    def __handle_color_input(self, event, selected_option):
        """Handle input for color (hex)."""
        data = self.traits_schema["options"][selected_option]["data"]
        if len(data) < 6 and re.match("[a-fA-F0-9]", event.unicode):
            self.traits_schema["options"][selected_option]["data"] = (
                data + event.unicode
            )

    def __handle_int_input(self, event, selected_option):
        """Handle input for integers."""
        self.traits_schema["options"][selected_option]["data"] += (
            event.unicode if event.unicode.isdigit() else ""
        )

    def __handle_tab_navigation(self, selected_option, selected_option_type):
        """Navigate between options using the TAB key."""
        selected_option_index = list(self.traits_schema["options"].keys()).index(
            selected_option
        )
        next_option = list(self.traits_schema["options"].keys())[
            (selected_option_index + 1) % len(self.traits_schema["options"])
        ]
        self.traits_schema["selected_option"] = next_option
        self.traits_schema["options"][selected_option]["selected"] = False
        self.traits_schema["options"][next_option]["selected"] = True

    def __handle_arrow_navigation(self, event, selected_option, selected_option_type):
        """Navigate through choices using left and right arrow keys."""
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

    def __rotate_pic_circle_border(self):
        self.pic_circle["border_angle"] += 1
        rotated_image = pygame.transform.rotate(
            self.pic_circle["border_image"], self.pic_circle["border_angle"]
        )
        self.pic_circle["border_rect"] = rotated_image.get_rect(
            center=self.pic_circle["rect"].center
        )
        return rotated_image

    def __rotate_pic_circle_organism(self):
        self.pic_circle["organism_angle"] += 1
        rotated_image = pygame.transform.rotate(
            self.pic_circle["organism_image"], self.pic_circle["organism_angle"]
        )
        self.pic_circle["organism_rect"] = rotated_image.get_rect(
            center=self.pic_circle["rect"].center
        )
        return rotated_image

    def __update_user_input(self, value, option_surface, input_type="str"):
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
