import contextlib
import os
import re

import numpy as np
import pygame

from config import Colors, Fonts, image_assets
from enums import EventType, MessagePacket, MessagePackets
import helper


class LaboratoryComponent:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface
        self.bg_image = pygame.image.load(
            os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
        )
        self.user_inputs = {}
        self.surface = pygame.Surface(size=(self.bg_image.get_size()))
        self.surface_x_offset = (
            self.main_surface.get_width() - self.surface.get_width()
        ) // 2
        self.surface_y_offset = (
            self.main_surface.get_height() - self.surface.get_height()
        ) // 2

        context.update(
            {
                "surface_x_offset": self.surface_x_offset,
                "surface_y_offset": self.surface_y_offset,
            }
        )

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
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the back button is clicked
            if self.back_button["absolute_rect"].collidepoint(event.pos):
                # Set the back button to its clicked image when the button is pressed
                self.back_button["current_image"] = self.back_button["clicked_image"]

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.back_button["absolute_rect"].collidepoint(event.pos):
                if self.curr_sub_component == "neural_lab":
                    # If in the "neural_lab", go back to "attrs_lab"
                    self.curr_sub_component = "attrs_lab"
                    self.back_button["current_image"] = self.back_button["image"]
                else:
                    # If not in "neural_lab", navigate to home
                    yield MessagePackets(MessagePacket(EventType.NAVIGATION, "home"))
            else:
                self.back_button["current_image"] = self.back_button["image"]

        # Handle the events for the current sub-component
        # Process the packet received from the sub-component handler
        if packet := self.sub_component_states.get(
            self.curr_sub_component,
        ).event_handler(event):
            if packet == MessagePacket(EventType.NAVIGATION, "neural_lab"):
                # Navigate to "neural_lab" sub-component and store its context
                self.curr_sub_component = "neural_lab"
                self.user_inputs = packet.context
            else:
                # Yield the packet as is
                yield MessagePackets(packet)

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
                50 + self.surface_x_offset,
                50 + self.surface_y_offset,
            )
        )


class NeuralLab:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface
        self.selected_sensor = None
        self.selected_actuator = None

        self.surface_x_offset = context.get("surface_x_offset", 0)
        self.surface_y_offset = context.get("surface_y_offset", 0)

        surface = self._setup_surface()

        self.surface = surface
        self.body_font = pygame.font.Font(Fonts.PixelifySansMedium, 21)

        self._configure_sensors(
            sensors=[
                {
                    "name": "Nil",
                    "description": "A basic sensory organ with minimal input detection.",
                },
                {
                    "name": "Dfd",
                    "description": "A directional detector helping the creature sense movement patterns.",
                },
                {
                    "name": "Bfs",
                    "description": "A biochemical sensor for detecting pheromones and chemical traces.",
                },
                {
                    "name": "Cfl",
                    "description": "A current flow sensor for detecting changes in nearby fluid dynamics.",
                },
                {
                    "name": "Dia",
                    "description": "A light-sensitive organ for basic image formation and light detection.",
                },
                {
                    "name": "Fwa",
                    "description": "A vibration sensor for detecting distant sound or surface vibrations.",
                },
                {
                    "name": "Car",
                    "description": "A scent-based sensor for identifying environmental chemicals and food sources.",
                },
                {
                    "name": "Nil",
                    "description": "A simple placeholder sensory organ with limited functionality.",
                },
            ]
        )

        self.__configure_actuators(
            actuators=[
                {
                    "name": "Psh",
                    "description": "A basic actuator for applying force to nearby objects.",
                },
                {
                    "name": "Grb",
                    "description": "An appendage allowing the creature to grasp and manipulate objects.",
                },
                {
                    "name": "Kck",
                    "description": "A leg-based actuator for powerful thrusts and rapid movement.",
                },
                {
                    "name": "Spn",
                    "description": "A rotational actuator for spinning parts of the body rapidly.",
                },
                {
                    "name": "Emt",
                    "description": "An actuator for releasing pheromones or other signals into the environment.",
                },
                {
                    "name": "Flx",
                    "description": "A muscle-like actuator for bending and contracting movements.",
                },
                {
                    "name": "Wve",
                    "description": "A fin or limb movement actuator designed for fluid locomotion.",
                },
                {
                    "name": "Nil",
                    "description": "A placeholder actuator with minimal interaction capabilities.",
                },
            ]
        )

        self._configure_neural_frame()
        self._configure_unleash_organism_click()

    def _configure_neural_frame(self):
        self.neural_frame_surface = pygame.image.load(
            os.path.join(image_assets, "laboratory", "neural_lab", "neural_frame.svg")
        )
        self.neural_frame_rect = self.neural_frame_surface.get_rect(
            center=(self.surface.get_width() // 2, 600)
        )

        # Position fetched from figma
        self.neural_network = {
            "scale_factor": 1.2,
            "sensor_info": {
                "default_bg": (221, 185, 103),
                "text_color": (0, 0, 0),
                "filled_bg": (219, 235, 137),
                "selected_bg": (0, 0, 0),
            },
            "actuator_info": {
                "default_bg": (152, 95, 153),
                "text_color": (0, 0, 0),
                "filled_bg": (192, 156, 255),
                "selected_bg": (0, 0, 0),
            },
            "connections": [],
            "lines": [],
            "selected_sensor": None,
            "selected_actuator": None,
            "sensors": [
                {
                    "name": "",
                    "surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "filled_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "selected_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "selected_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "position": {"center": (236, 134)},
                    "rect": pygame.rect.Rect(0, 0, 50, 50),
                    "selected": False,
                    "absolute_rect": pygame.rect.Rect(
                        self.surface_x_offset + self.neural_frame_rect.x + 236 - 25,
                        self.surface_y_offset + self.neural_frame_rect.y + 134 - 25,
                        50,
                        50,
                    ),
                },
                {
                    "name": "",
                    "surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "filled_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "selected_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "position": {"center": (236, 193)},
                    "rect": pygame.rect.Rect(0, 0, 50, 50),
                    "selected": False,
                    "absolute_rect": pygame.rect.Rect(
                        self.surface_x_offset + self.neural_frame_rect.x + 236 - 25,
                        self.surface_y_offset + self.neural_frame_rect.y + 193 - 25,
                        50,
                        50,
                    ),
                },
                {
                    "name": "",
                    "surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "filled_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "selected_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "position": {"center": (236, 252)},
                    "rect": pygame.rect.Rect(0, 0, 50, 50),
                    "selected": False,
                    "absolute_rect": pygame.rect.Rect(
                        self.surface_x_offset + self.neural_frame_rect.x + 236 - 25,
                        self.surface_y_offset + self.neural_frame_rect.y + 252 - 25,
                        50,
                        50,
                    ),
                },
            ],
            "actuators": [
                {
                    "name": "",
                    "surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "filled_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "selected_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "position": {"center": (436, 134)},
                    "rect": pygame.rect.Rect(0, 0, 50, 50),
                    "absolute_rect": pygame.rect.Rect(
                        self.surface_x_offset + self.neural_frame_rect.x + 436 - 25,
                        self.surface_y_offset + self.neural_frame_rect.y + 134 - 25,
                        50,
                        50,
                    ),
                },
                {
                    "name": "",
                    "surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "filled_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "selected_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "position": {"center": (436, 193)},
                    "rect": pygame.rect.Rect(0, 0, 50, 50),
                    "absolute_rect": pygame.rect.Rect(
                        self.surface_x_offset + self.neural_frame_rect.x + 436 - 25,
                        self.surface_y_offset + self.neural_frame_rect.y + 193 - 25,
                        50,
                        50,
                    ),
                },
                {
                    "name": "",
                    "surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "filled_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "selected_surface": pygame.Surface((50, 50), pygame.SRCALPHA),
                    "position": {"center": (436, 252)},
                    "rect": pygame.rect.Rect(0, 0, 50, 50),
                    "absolute_rect": pygame.rect.Rect(
                        self.surface_x_offset + self.neural_frame_rect.x + 436 - 25,
                        self.surface_y_offset + self.neural_frame_rect.y + 252 - 25,
                        50,
                        50,
                    ),
                },
            ],
        }
        neural_frame_surface = self.neural_frame_surface.copy()

        for sensor in self.neural_network["sensors"]:
            sensor["rect"] = sensor["surface"].get_rect(**sensor["position"])
            pygame.draw.circle(sensor["surface"], Colors.bg_color, (25, 25), 25)
            pygame.draw.circle(
                sensor["surface"],
                self.neural_network["sensor_info"]["default_bg"],
                (25, 25),
                22,
            )
            neural_frame_surface.blit(sensor["surface"], sensor["rect"])

            pygame.draw.circle(sensor["filled_surface"], Colors.bg_color, (25, 25), 25)
            pygame.draw.circle(
                sensor["filled_surface"],
                self.neural_network["sensor_info"]["filled_bg"],
                (25, 25),
                22,
            )

            pygame.draw.circle(
                sensor["selected_surface"], (255, 255, 255), (25, 25), 25
            )
            pygame.draw.circle(
                sensor["selected_surface"],
                self.neural_network["sensor_info"]["filled_bg"],
                (25, 25),
                22,
            )

        for actuator in self.neural_network["actuators"]:
            actuator["rect"] = actuator["surface"].get_rect(**actuator["position"])
            pygame.draw.circle(actuator["surface"], Colors.bg_color, (25, 25), 25)
            pygame.draw.circle(
                actuator["surface"],
                self.neural_network["actuator_info"]["default_bg"],
                (25, 25),
                22,
            )

            neural_frame_surface.blit(actuator["surface"], actuator["rect"])
            pygame.draw.circle(
                actuator["filled_surface"], Colors.bg_color, (25, 25), 25
            )
            pygame.draw.circle(
                actuator["filled_surface"],
                self.neural_network["actuator_info"]["filled_bg"],
                (25, 25),
                22,
            )

            pygame.draw.circle(
                actuator["selected_surface"], (255, 255, 255), (25, 25), 25
            )
            pygame.draw.circle(
                actuator["selected_surface"],
                self.neural_network["actuator_info"]["filled_bg"],
                (25, 25),
                22,
            )

        self.surface.blit(neural_frame_surface, self.neural_frame_rect)

    def _configure_unleash_organism_click(self):
        self.unleash_organism_button = {
            "current_image": None,
            "image": pygame.image.load(
                os.path.join(
                    image_assets,
                    "laboratory",
                    "neural_lab",
                    "unleash_organism_button.svg",
                )
            ),
            "clicked_image": pygame.image.load(
                os.path.join(
                    image_assets,
                    "laboratory",
                    "neural_lab",
                    "unleash_organism_button_clicked.svg",
                )
            ),
            "position": {"center": (self.surface.get_width() // 2, 875)},
            "rect": None,
            "absolute_rect": None,
        }
        self.unleash_organism_button["current_image"] = self.unleash_organism_button[
            "image"
        ]
        self.unleash_organism_button["rect"] = self.unleash_organism_button[
            "image"
        ].get_rect(**self.unleash_organism_button["position"])
        self.unleash_organism_button["absolute_rect"] = self.unleash_organism_button[
            "image"
        ].get_rect(
            topleft=(
                np.array(self.unleash_organism_button["rect"].topleft)
                + np.array(
                    (
                        self.surface_x_offset,
                        self.surface_y_offset,
                    )
                )
            )
        )

    def event_handler(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            return self._handle_mouse_down(event)
        elif event.type == pygame.MOUSEBUTTONUP:
            return self._handle_mouse_up(event)

    def _handle_mouse_down(self, event):
        self.__handle_sensor_click(event)
        self.__handle_actuator_click(event)
        self.__handle_unleash_organism_on_mouse_down(event)
        self.__handle_neuron_on_mouse_down(event)

    def __handle_neuron_on_mouse_down(self, event):
        for i in range(len(self.neural_network["sensors"])):
            if self.neural_network["sensors"][i]["absolute_rect"].collidepoint(
                event.pos
            ):
                if self.selected_sensor:
                    # sensor change, hence, trigger a deletion of the connections to this sensor
                    indices_to_remove = [
                        j
                        for j, conn in enumerate(self.neural_network["lines"])
                        if conn[0] == self.neural_network["sensors"][i]["rect"].center
                    ]

                    # Remove elements in reverse order to avoid shifting issues
                    for index in reversed(indices_to_remove):
                        self.neural_network["connections"].pop(index)
                        self.neural_network["lines"].pop(index)

                    # Then change the sensor name
                    self.neural_network["sensors"][i]["name"] = self.selected_sensor[
                        "name"
                    ]

                elif self.neural_network["sensors"][i]["name"]:
                    self.neural_network["selected_sensor"] = i
                break

        for i in range(len(self.neural_network["actuators"])):
            if self.neural_network["actuators"][i]["absolute_rect"].collidepoint(
                event.pos
            ):
                if self.selected_actuator:
                    # actuator change, hence, trigger a deletion of the all connections to this actuator
                    indices_to_remove = [
                        j
                        for j, conn in enumerate(self.neural_network["lines"])
                        if conn[1] == self.neural_network["actuators"][i]["rect"].center
                    ]

                    # Remove elements in reverse order to avoid shifting issues
                    for index in reversed(indices_to_remove):
                        self.neural_network["connections"].pop(index)
                        self.neural_network["lines"].pop(index)

                    # Then change the actuator name
                    self.neural_network["actuators"][i]["name"] = (
                        self.selected_actuator["name"]
                    )

                elif self.neural_network["actuators"][i]["name"]:
                    self.neural_network["selected_actuator"] = i
                break

        if (
            self.neural_network["selected_sensor"] is not None
            and self.neural_network["selected_actuator"] is not None
        ):
            sensor = self.neural_network["sensors"][
                self.neural_network["selected_sensor"]
            ]
            actuator = self.neural_network["actuators"][
                self.neural_network["selected_actuator"]
            ]
            self.neural_network["connections"].append(
                (
                    sensor["name"],
                    actuator["name"],
                )
            )
            self.neural_network["lines"].append(
                (
                    sensor["rect"].center,
                    actuator["rect"].center,
                )
            )
            self.neural_network["selected_sensor"] = None
            self.neural_network["selected_actuator"] = None

    def __handle_unleash_organism_on_mouse_down(self, event):
        if self.unleash_organism_button["absolute_rect"].collidepoint(event.pos):
            self.unleash_organism_button["current_image"] = (
                self.unleash_organism_button["clicked_image"]
            )

    def _handle_mouse_up(self, event):
        return next(
            filter(
                lambda packet: packet is not None,
                (
                    self.__reset_sensors_on_mouse_up(event),
                    self.__reset_actuators_on_mouse_up(event),
                    self.__handle_unleash_organism_on_mouse_up(event),
                ),
            ),
            None,
        )

    def __handle_unleash_organism_on_mouse_up(self, event):
        if self.unleash_organism_button["absolute_rect"].collidepoint(event.pos):
            return MessagePacket(EventType.NAVIGATION, "home")
        elif not self.unleash_organism_button["absolute_rect"].collidepoint(event.pos):
            self.unleash_organism_button["current_image"] = (
                self.unleash_organism_button["image"]
            )

    def __handle_sensor_click(self, event):
        for sensor in self.sensors:
            if sensor["absolute_rect"].collidepoint(event.pos):
                self.selected_sensor = sensor
                sensor["current_surface"] = sensor["clicked_surface"]
                self.__update_sensor_text(sensor_desc_text=sensor["description"])
                break

    def __handle_actuator_click(self, event):
        for actuator in self.actuators:
            if actuator["absolute_rect"].collidepoint(event.pos):
                self.selected_actuator = actuator
                actuator["current_surface"] = actuator["clicked_surface"]
                self.__update_actuator_text(actuator_desc_text=actuator["description"])
                break

    def __reset_sensors_on_mouse_up(self, event):
        if self.selected_sensor:
            for sensor in self.sensors:
                if sensor != self.selected_sensor:
                    sensor["current_surface"] = sensor["surface"]
            if not self.selected_sensor["absolute_rect"].collidepoint(event.pos):
                self.__update_sensor_text()
                self.selected_sensor["current_surface"] = self.selected_sensor[
                    "surface"
                ]
                self.selected_sensor = None

    def __reset_actuators_on_mouse_up(self, event):
        if self.selected_actuator:
            for actuator in self.actuators:
                if actuator != self.selected_actuator:
                    actuator["current_surface"] = actuator["surface"]
            if not self.selected_actuator["absolute_rect"].collidepoint(event.pos):
                self.__update_actuator_text()
                self.selected_actuator["current_surface"] = self.selected_actuator[
                    "surface"
                ]
                self.selected_actuator = None

    def update(self, context=None):

        for sensor in self.sensors:
            self.surface.blit(sensor["current_surface"], sensor["rect"])

        for actuator in self.actuators:
            self.surface.blit(actuator["current_surface"], actuator["rect"])

        self.surface.blit(self.sensor_desc["surface"], self.sensor_desc["rect"])
        self.surface.blit(self.actuator_desc["surface"], self.actuator_desc["rect"])
        self.surface.blit(
            self.unleash_organism_button["current_image"],
            self.unleash_organism_button["rect"],
        )

        neural_frame_surface = self.neural_frame_surface.copy()

        for line in self.neural_network["lines"]:
            pygame.draw.line(neural_frame_surface, Colors.primary, *line, 3)

        for sensor in self.neural_network["sensors"]:
            if sensor["name"]:
                sensor_surface = sensor["filled_surface"].copy()
                text = self.body_font.render(sensor["name"], True, Colors.bg_color)
                sensor_surface.blit(text, text.get_rect(center=(25, 25)))
            else:
                sensor_surface = sensor["surface"]

            neural_frame_surface.blit(sensor_surface, sensor["rect"])

        for actuator in self.neural_network["actuators"]:
            if actuator["name"]:
                actuator_surface = actuator["filled_surface"].copy()
                text = self.body_font.render(actuator["name"], True, Colors.bg_color)
                actuator_surface.blit(text, text.get_rect(center=(25, 25)))
            else:
                actuator_surface = actuator["surface"]

            neural_frame_surface.blit(actuator_surface, actuator["rect"])

        self.surface.blit(neural_frame_surface, self.neural_frame_rect)

    def _setup_surface(self):
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
        surface.blit(
            sensor_title,
            sensor_title.get_rect(
                topleft=(75, 400),
            ),
        )

        actuator_title = pygame.image.load(
            os.path.join(image_assets, "laboratory", "neural_lab", "actuator_title.svg")
        )
        surface.blit(
            actuator_title,
            actuator_title.get_rect(
                topright=(surface.get_width() - 75, 400),
            ),
        )
        return surface

    def _configure_sensors(self, sensors):
        sensors.extend(
            [
                {
                    "name": "",
                    "description": "Use this to remove added sensors.",
                }
            ]
        )
        self.sensor_desc = {
            "surface": pygame.Surface((450, 100)),
            "position": {"topleft": (75, 450)},
            "rect": None,
            "absolute_rect": None,
            "default_text": helper.split_text(
                "Sensors allow your creatures to experience the World. Select a sensor from the list below to view more details."
            ),
        }
        self.sensor_desc["rect"] = self.sensor_desc["surface"].get_rect(
            **self.sensor_desc["position"]
        )

        self.__update_sensor_text()

        num_sensors = len(sensors)
        self.sensors = []  # Use this list to store sensor data
        columns = [100 + (i * 65) for i in range(5)]  # x-coordinates for each column
        y_start = 600
        spacing = 60

        for i in range(num_sensors):
            column_index = i % 5
            x = columns[column_index]
            y = y_start + (i // 5) * spacing

            # Create a new surface for each sensor
            sensor_surface = pygame.Surface((50, 50))
            sensor_surface.fill(color=Colors.primary)
            pygame.draw.circle(sensor_surface, Colors.bg_color, (25, 25), 25)
            pygame.draw.circle(sensor_surface, Colors.primary, (25, 25), 22)

            # Render title text for each sensor
            text = self.body_font.render(sensors[i]["name"], True, Colors.bg_color)
            sensor_surface.blit(text, text.get_rect(center=(25, 25)))

            # Create a new surface for the clicked look for each sensor
            clicked_sensor_surface = pygame.Surface((50, 50))
            clicked_sensor_surface.fill(color=Colors.primary)
            pygame.draw.circle(clicked_sensor_surface, Colors.bg_color, (25, 25), 25)
            pygame.draw.circle(clicked_sensor_surface, Colors.bg_color, (25, 25), 22)

            # Render title text for the clicked sensor
            text = self.body_font.render(sensors[i]["name"], True, Colors.primary)
            clicked_sensor_surface.blit(text, text.get_rect(center=(25, 25)))

            # Add sensor data to the self.sensors list
            self.sensors.append(
                {
                    "name": sensors[i]["name"],
                    "description": helper.split_text(sensors[i]["description"]),
                    "selected": False,
                    "current_surface": sensor_surface,
                    "surface": sensor_surface,
                    "clicked_surface": clicked_sensor_surface,
                    "rect": sensor_surface.get_rect(center=(x, y)),
                    "absolute_rect": sensor_surface.get_rect(
                        topleft=(
                            x - 25 + self.surface_x_offset,
                            y - 25 + self.surface_y_offset,
                        )
                    ),
                }
            )

    def __update_sensor_text(
        self,
        sensor_desc_text: list = None,
    ):
        if not sensor_desc_text:
            sensor_desc_text = self.sensor_desc["default_text"]

        self.sensor_desc["surface"].fill(Colors.primary)

        text_y = 0
        for text in sensor_desc_text:
            text = self.body_font.render(text, True, Colors.bg_color, Colors.primary)
            self.sensor_desc["surface"].blit(text, text.get_rect(topleft=(0, text_y)))
            text_y += 25

    def __configure_actuators(self, actuators):
        actuators.extend(
            [
                {
                    "name": "",
                    "description": "Use this to remove added actuators",
                }
            ]
        )
        self.actuator_desc = {
            "surface": pygame.Surface((450, 100)),
            "position": {"topright": (self.surface.get_width() - 75, 450)},
            "rect": None,
            "default_text": helper.split_text(
                "Actuators allow your creatures to interact with the World. Select an actuator from the list below to view more details."
            ),
        }
        self.actuator_desc["rect"] = self.actuator_desc["surface"].get_rect(
            **self.actuator_desc["position"]
        )

        self.__update_actuator_text()

        num_actuators = len(actuators)
        self.actuators = []  # Use this list to store actuator data
        columns = [
            self.surface.get_width() - 100 - (i * 65) for i in range(5)
        ]  # x-coordinates for each column
        y_start = 600
        spacing = 60

        for i in range(num_actuators):
            column_index = i % 5
            x = columns[column_index]
            y = y_start + (i // 5) * spacing

            # Create a new surface for each actuator
            actuator_surface = pygame.Surface((50, 50))
            actuator_surface.fill(color=Colors.primary)
            pygame.draw.circle(actuator_surface, Colors.bg_color, (25, 25), 25)
            pygame.draw.circle(actuator_surface, Colors.primary, (25, 25), 22)

            # Render title text for each actuator
            text = self.body_font.render(actuators[i]["name"], True, Colors.bg_color)
            actuator_surface.blit(text, text.get_rect(center=(25, 25)))

            # Create a new surface for the clicked look for each actuator
            clicked_actuator_surface = pygame.Surface((50, 50))
            clicked_actuator_surface.fill(color=Colors.primary)
            pygame.draw.circle(clicked_actuator_surface, Colors.bg_color, (25, 25), 25)
            pygame.draw.circle(clicked_actuator_surface, Colors.bg_color, (25, 25), 22)

            # Render title text for the clicked actuator
            text = self.body_font.render(actuators[i]["name"], True, Colors.primary)
            clicked_actuator_surface.blit(text, text.get_rect(center=(25, 25)))

            # Add actuator data to the self.actuators list
            self.actuators.append(
                {
                    "name": actuators[i]["name"],
                    "selected": False,
                    "description": helper.split_text(actuators[i]["description"]),
                    "current_surface": actuator_surface,
                    "surface": actuator_surface,
                    "clicked_surface": clicked_actuator_surface,
                    "rect": actuator_surface.get_rect(center=(x, y)),
                    "absolute_rect": actuator_surface.get_rect(
                        topleft=(
                            x - 25 + self.surface_x_offset,
                            y - 25 + self.surface_y_offset,
                        )
                    ),
                }
            )

    def __update_actuator_text(
        self,
        actuator_desc_text: list = None,
    ):
        if not actuator_desc_text:
            actuator_desc_text = self.actuator_desc["default_text"]

        self.actuator_desc["surface"].fill(Colors.primary)

        text_y = 0
        for text in actuator_desc_text:
            text = self.body_font.render(text, True, Colors.bg_color, Colors.primary)
            self.actuator_desc["surface"].blit(text, text.get_rect(topleft=(0, text_y)))
            text_y += 25


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
        self.surface_x_offset = context.get("surface_x_offset", 0)
        self.surface_y_offset = context.get("surface_y_offset", 0)

        self.attrs_lab_text = pygame.image.load(
            os.path.join(image_assets, "laboratory", "attrs_lab", "lab_intro_text.svg")
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
                return self.__navigate_to_neural_lab()

            # Handle interaction with traits options
            self.__handle_traits_options(event, selected_option)

        elif event.type == pygame.KEYDOWN:
            # Handle keyboard events (backspace, alphanumeric, navigation)
            self.__handle_keydown_event(event, selected_option, selected_option_type)

    def __get_user_input(self):
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
                x + 200 + self.surface_x_offset,
                y + self.surface_y_offset,
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
                    x + choice_x + self.surface_x_offset,
                    y + self.surface_y_offset,
                )
            )
            choice_x += choice["surface"].get_width() + 10

    def __configure_neural_network_button(self):
        self.neural_network_button = {
            "current_image": None,
            "image": pygame.image.load(
                os.path.join(
                    image_assets, "laboratory", "attrs_lab", "neural_network_button.svg"
                )
            ),
            "clicked_image": pygame.image.load(
                os.path.join(
                    image_assets,
                    "laboratory",
                    "attrs_lab",
                    "neural_network_button_clicked.svg",
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
                        self.surface_x_offset,
                        self.surface_y_offset,
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
                os.path.join(
                    image_assets, "laboratory", "attrs_lab", "pic_circle_border.svg"
                )
            ),
            "bg_image": pygame.image.load(
                os.path.join(
                    image_assets, "laboratory", "attrs_lab", "pic_circle_bg.svg"
                )
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
            context=self.__get_user_input(),
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
