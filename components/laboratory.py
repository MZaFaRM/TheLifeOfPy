import contextlib
import os
import random
import re
import uuid

import numpy as np
import pygame
import pygame.gfxdraw

from config import Colors, Fonts, image_assets
from enums import EventType, MessagePacket, NeuronType, SurfDesc
from handlers.genetics import NeuronManager
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

        self.curr_sub_comp = "attrs_lab"
        self.sub_comp_states = {
            "attrs_lab": AttributesLab(main_surface, context),
            "neural_lab": NeuralLab(main_surface, context),
        }

    def update(self, context=None):
        self.surface.blit(self.bg_image, (0, 0))
        self.surface.blit(
            self.back_button[SurfDesc.CURRENT_SURFACE], self.back_button[SurfDesc.RECT]
        )
        sub_component = self.sub_comp_states[self.curr_sub_comp]
        sub_component.update(context)
        self.surface.blit(sub_component.surface, (0, 0))

    def event_handler(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the back button is clicked
            if self.back_button[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
                # Set the back button to its clicked image when the button is pressed
                self.back_button[SurfDesc.CURRENT_SURFACE] = self.back_button[
                    SurfDesc.CLICKED_SURFACE
                ]

        elif event.type == pygame.MOUSEBUTTONUP:
            if self.back_button[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
                if self.curr_sub_comp == "neural_lab":
                    # If in the "neural_lab", go back to "attrs_lab"
                    self.curr_sub_comp = "attrs_lab"
                    self.back_button[SurfDesc.CURRENT_SURFACE] = self.back_button[
                        SurfDesc.SURFACE
                    ]
                else:
                    # If not in "neural_lab", navigate to home
                    return MessagePacket(EventType.NAVIGATION, "home")
            else:
                self.back_button[SurfDesc.CURRENT_SURFACE] = self.back_button[
                    SurfDesc.SURFACE
                ]

        # Handle the events for the current sub-component
        # Process the packet received from the sub-component handler
        if packet := self.sub_comp_states.get(
            self.curr_sub_comp,
        ).event_handler(event):
            if packet == MessagePacket(EventType.NAVIGATION, "neural_lab"):
                # Navigate to "neural_lab" sub-component and store its context
                self.user_inputs.update(packet.context.get(EventType.GENESIS, {}))
                self.curr_sub_comp = "neural_lab"

            elif packet == MessagePacket(EventType.NAVIGATION, "home"):
                user_input = {
                    "base_pop": self.user_inputs.get("base_pop", 0),
                    "genome": packet.context.get(EventType.GENESIS, {}),
                }

                return MessagePacket(
                    EventType.NAVIGATION,
                    "home",
                    context={EventType.GENESIS: user_input},
                )
            else:
                # return the packet as is
                return packet

    def __configure_back_button(self):
        self.back_button = {
            SurfDesc.CURRENT_SURFACE: None,
            "position": {"topleft": (50, 50)},
            SurfDesc.ABSOLUTE_RECT: None,
            SurfDesc.SURFACE: pygame.image.load(
                os.path.join(image_assets, "laboratory", "back_button.svg")
            ),
            SurfDesc.CLICKED_SURFACE: pygame.image.load(
                os.path.join(image_assets, "laboratory", "back_button_clicked.svg")
            ),
        }

        self.back_button[SurfDesc.RECT] = self.back_button[SurfDesc.SURFACE].get_rect(
            **self.back_button["position"]
        )
        self.back_button[SurfDesc.CURRENT_SURFACE] = self.back_button[SurfDesc.SURFACE]

        self.back_button[SurfDesc.ABSOLUTE_RECT] = self.back_button[
            SurfDesc.SURFACE
        ].get_rect(
            topleft=(
                50 + self.surface_x_offset,
                50 + self.surface_y_offset,
            )
        )


class NeuralLab:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface

        self.surface_x_offset = context.get("surface_x_offset", 0)
        self.surface_y_offset = context.get("surface_y_offset", 0)

        surface = self._setup_surface()

        self.surface = surface
        self.body_font = pygame.font.Font(Fonts.PixelifySansMedium, 21)

        self.selected_neuron = {}

        sensors = NeuronManager.sensors.items()
        sensors = [
            {"id": uuid.uuid4(), "name": key, "desc": value["desc"]}
            for key, value in sensors
        ]
        self._configure_neurons(neuron_type=NeuronType.SENSOR, neurons=sensors)

        actuators = NeuronManager.actuators.items()
        actuators = [
            {"id": uuid.uuid4(), "name": key, "desc": value["desc"]}
            for key, value in actuators
        ]
        self._configure_neurons(neuron_type=NeuronType.ACTUATOR, neurons=actuators)

        self._configure_hidden_neuron()
        self._configure_bias_neuron()

        self._configure_neural_frame()
        self._configure_unleash_organism_button()

        self.neural_nodes = {
            NeuronType.SENSOR: self.sensors,
            NeuronType.ACTUATOR: self.actuators,
            NeuronType.HIDDEN: [self.hidden_neuron],
            NeuronType.BIAS: [self.bias_neuron],
        }

    def _configure_neural_frame(self):
        self.neural_frame = {}

        self.neural_frame[SurfDesc.SURFACE] = pygame.image.load(
            os.path.join(image_assets, "laboratory", "neural_lab", "neural_frame.svg")
        )
        self.neural_frame[SurfDesc.RECT] = self.neural_frame[SurfDesc.SURFACE].get_rect(
            topleft=(62, 204)
        )
        self.neural_frame[SurfDesc.ABSOLUTE_RECT] = self.neural_frame[
            SurfDesc.SURFACE
        ].get_rect(
            topleft=(
                62 + self.surface_x_offset,
                204 + self.surface_y_offset,
            )
        )
        self.neural_frame["reset"] = self.neural_frame[SurfDesc.SURFACE].copy()
        self.neural_frame["nodes"] = []
        self.neural_frame["selection"] = None
        self.neural_frame["connections"] = []
        self.neural_frame["graph_desc"] = {
            "circle": {
                "radius": 25,
                "color": {
                    NeuronType.SENSOR: (74, 227, 181),
                    NeuronType.ACTUATOR: (0, 255, 127),
                    NeuronType.HIDDEN: (0, 163, 108),
                    NeuronType.BIAS: (0, 139, 139),
                },
            },
            "line": {
                "thickness": 5,
                "color": (23, 86, 67),
            },
        }
        self.surface.blit(
            self.neural_frame[SurfDesc.SURFACE], self.neural_frame[SurfDesc.RECT]
        )

    def _configure_unleash_organism_button(self):
        self.unleash_organism_button = {
            SurfDesc.CURRENT_SURFACE: None,
            SurfDesc.SURFACE: pygame.image.load(
                os.path.join(
                    image_assets,
                    "laboratory",
                    "neural_lab",
                    "unleash_organism_button.svg",
                )
            ),
            SurfDesc.CLICKED_SURFACE: pygame.image.load(
                os.path.join(
                    image_assets,
                    "laboratory",
                    "neural_lab",
                    "unleash_organism_button_clicked.svg",
                )
            ),
            "position": {"topleft": (1304, 843)},
            SurfDesc.RECT: None,
            SurfDesc.ABSOLUTE_RECT: None,
        }
        self.unleash_organism_button[SurfDesc.CURRENT_SURFACE] = (
            self.unleash_organism_button[SurfDesc.SURFACE]
        )
        self.unleash_organism_button[SurfDesc.RECT] = self.unleash_organism_button[
            SurfDesc.SURFACE
        ].get_rect(**self.unleash_organism_button["position"])
        self.unleash_organism_button[
            SurfDesc.ABSOLUTE_RECT
        ] = self.unleash_organism_button[SurfDesc.SURFACE].get_rect(
            topleft=(
                np.array(self.unleash_organism_button[SurfDesc.RECT].topleft)
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
        elif getattr(event, "key", None) == pygame.K_DELETE:
            return self.__handle_neural_frame_deletion(event)

    def _handle_mouse_down(self, event):
        response = None
        for res in (
            self.__handle_neuron_click(event),
            self.__handle_neural_node_click(event),
            self.__handle_neural_node_creation(event),
            self.__handle_unleash_organism_on_mouse_down(event),
        ):
            if res:
                response = res
        return response

    def __handle_neural_frame_deletion(self, event):
        if self.neural_frame["selection"]:
            for node in self.neural_frame["nodes"]:
                if node["id"] == self.neural_frame["selection"]["id"]:
                    self.neural_frame["nodes"].remove(node)
                    for connection in self.neural_frame["connections"].copy():
                        if (
                            connection[0]["id"] == node["id"]
                            or connection[1]["id"] == node["id"]
                        ):
                            self.neural_frame["connections"].remove(connection)
            self.neural_frame["selection"] = None

    def __handle_neural_node_click(self, event):
        selected_any = False
        for node in self.neural_frame["nodes"]:
            if node[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
                selected_any = True
                if self.neural_frame["selection"]:
                    if self.__valid_connection(self.neural_frame["selection"], node):
                        self.neural_frame["connections"].append(
                            (self.neural_frame["selection"], node)
                        )
                    else:
                        print(f"Invalid Connection: {self.neural_frame['selection']["name"]} -> {node["name"]}")
                    self.neural_frame["selection"] = None
                    
                else:
                    node[SurfDesc.CURRENT_SURFACE] = node[SurfDesc.CLICKED_SURFACE]
                    self.neural_frame["selection"] = node
            else:
                node[SurfDesc.CURRENT_SURFACE] = node[SurfDesc.SURFACE]

        if not selected_any:
            self.neural_frame["selection"] = None

    def __valid_connection(self, node_1, node_2):
        # Ensure both nodes exist
        if not node_1.get("id", None) or not node_2.get("id", None):
            return False

        # Prevent self-connections
        if node_1.get("id") == node_2.get("id"):
            return False

        # Ensure nodes are not already connected
        for connection in self.neural_frame["connections"]:
            if (
                connection[0]["id"] == node_1["id"]
                and connection[1]["id"] == node_2["id"]
            ) or (
                connection[0]["id"] == node_2["id"]
                and connection[1]["id"] == node_1["id"]
            ):
                return False

        # Enforce directional rules
        if node_1["type"] == NeuronType.SENSOR and node_2["type"] == NeuronType.SENSOR:
            return False  # Sensors should not connect to other sensors

        if (
            node_1["type"] == NeuronType.ACTUATOR
            and node_2["type"] == NeuronType.ACTUATOR
        ):
            return False  # Actuators should not connect to other actuators

        if node_2["type"] == NeuronType.SENSOR:
            return False  # No connections should go *into* a sensor

        if node_1["type"] == NeuronType.ACTUATOR:
            return False  # No connections should come *out of* an actuator

        # Prevent cycles if required (optional, depends on your structure)
        if self.__has_cycle(node_1, node_2):
            return False

        return True

    def __has_cycle(self, node_1, node_2):
        # Create a directed adjacency list from the connections
        adjacency_list = {}
        for src, dst in self.neural_frame["connections"]:
            adjacency_list.setdefault(src["id"], []).append(dst["id"])

        # Temporarily add the new connection
        adjacency_list.setdefault(node_1["id"], []).append(node_2["id"])

        # Perform DFS to check if node_2 can reach node_1 (forming a cycle)
        visited = set()

        def dfs(node):
            if node in visited:
                return True  # Cycle detected
            visited.add(node)
            for neighbor in adjacency_list.get(node, []):
                if dfs(neighbor):
                    return True
            visited.remove(node)  # Backtrack
            return False

        has_cycle = dfs(node_2["id"])  # Start DFS from node_2
        return has_cycle

    def __handle_neural_node_creation(self, event):
        # Check if the selected neuron is within the neural frame
        if self.selected_neuron and self.neural_frame[
            SurfDesc.ABSOLUTE_RECT
        ].collidepoint(event.pos):
            # Get the properties of the shape to draw
            shape = self.neural_frame["graph_desc"]["circle"]
            radius = shape["radius"]
            color = shape["color"][self.selected_neuron["type"]]
            pos = (
                event.pos[0] - self.surface_x_offset,
                event.pos[1] - self.surface_y_offset,
            )

            # Create a new surface and draw the circle
            surface = pygame.Surface(
                ((radius * 2) + 1, (radius * 2) + 1), pygame.SRCALPHA
            )
            pygame.draw.circle(surface, color, (radius, radius), radius)

            # Create a selected surface with a white border and text
            selected_surface = pygame.Surface(
                ((radius * 2) + 1, (radius * 2) + 1), pygame.SRCALPHA
            )
            pygame.draw.circle(
                selected_surface, (255, 255, 255), (radius, radius), radius
            )
            pygame.draw.circle(selected_surface, color, (radius, radius), radius - 5)

            if self.selected_neuron["type"] not in [NeuronType.HIDDEN, NeuronType.BIAS]:
                text = self.body_font.render(
                    self.selected_neuron["name"], True, Colors.bg_color
                )
                surface.blit(text, text.get_rect(center=(radius, radius)))
                selected_surface.blit(text, text.get_rect(center=(radius, radius)))

            if self.selected_neuron["type"] in [NeuronType.HIDDEN, NeuronType.BIAS]:
                _id = uuid.uuid4()
            else:
                _id = self.selected_neuron.get("id")

            # Define the new neuron properties and add it to the frame
            new_neuron = {
                "id": _id,
                "name": self.selected_neuron["name"],
                "type": self.selected_neuron["type"],
                SurfDesc.SURFACE: surface,
                SurfDesc.CURRENT_SURFACE: surface,
                SurfDesc.CLICKED_SURFACE: selected_surface,
                SurfDesc.RECT: surface.get_rect(center=(pos[0], pos[1])),
                SurfDesc.ABSOLUTE_RECT: surface.get_rect(
                    topleft=(
                        pos[0] + self.surface_x_offset - radius,
                        pos[1] + self.surface_y_offset - radius,
                    )
                ),
            }
            self.neural_frame["nodes"].extend([new_neuron])

            # Reset selected neuron after adding
            self.selected_neuron = {}

    def __handle_unleash_organism_on_mouse_down(self, event):
        if self.unleash_organism_button[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
            self.unleash_organism_button[SurfDesc.CURRENT_SURFACE] = (
                self.unleash_organism_button[SurfDesc.CLICKED_SURFACE]
            )

    def __get_user_input(self):
        sensors = []
        actuators = []
        hidden = []
        bias = []
        connections = []

        for node in self.neural_frame["nodes"]:
            if node["type"] == NeuronType.SENSOR:
                sensors.append((node["id"], node["name"], NeuronType.SENSOR))
            elif node["type"] == NeuronType.ACTUATOR:
                actuators.append((node["id"], node["name"], NeuronType.ACTUATOR))
            elif node["type"] == NeuronType.HIDDEN:
                hidden.append((node["id"], node["name"], NeuronType.HIDDEN))
            elif node["type"] == NeuronType.BIAS:
                bias.append((node["id"], node["name"], NeuronType.BIAS))

        for conn in self.neural_frame["connections"]:
            connections.append(
                (
                    (conn[0]["id"], conn[0]["name"], conn[0]["type"]),
                    (conn[1]["id"], conn[1]["name"], conn[1]["type"]),
                )
            )

        return {
            NeuronType.SENSOR: sensors,
            NeuronType.ACTUATOR: actuators,
            NeuronType.HIDDEN: hidden,
            NeuronType.BIAS: bias,
            "connections": connections,
        }

    def _handle_mouse_up(self, event):
        return next(
            filter(
                lambda packet: packet is not None,
                (
                    self.__reset_neurons_on_mouse_up(event),
                    self.__handle_unleash_organism_on_mouse_up(event),
                ),
            ),
            None,
        )

    def __handle_unleash_organism_on_mouse_up(self, event):
        if self.unleash_organism_button[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
            return MessagePacket(
                EventType.NAVIGATION,
                "home",
                context={EventType.GENESIS: self.__get_user_input()},
            )
        elif not self.unleash_organism_button[SurfDesc.ABSOLUTE_RECT].collidepoint(
            event.pos
        ):
            self.unleash_organism_button[SurfDesc.CURRENT_SURFACE] = (
                self.unleash_organism_button[SurfDesc.SURFACE]
            )

    def __handle_neuron_click(self, event):
        for neuron_type, neurons in self.neural_nodes.items():
            for neuron in neurons:
                if neuron[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
                    self.selected_neuron = neuron
                    self.selected_neuron["type"] = neuron_type
                    neuron[SurfDesc.CURRENT_SURFACE] = neuron[SurfDesc.CLICKED_SURFACE]
                    if neuron_type not in [NeuronType.HIDDEN, NeuronType.BIAS]:
                        self.__update_neuron_text(
                            neuron_type=neuron_type, neuron_desc_text=neuron["desc"]
                        )
                    return

    def __reset_neurons_on_mouse_up(self, event):
        # Iterate through neuron types and their neurons
        for neuron_type, neurons in self.neural_nodes.items():
            for neuron in neurons:
                # Reset unselected neurons' surface
                if neuron != self.selected_neuron:
                    neuron[SurfDesc.CURRENT_SURFACE] = neuron[SurfDesc.SURFACE]

            # If a neuron is selected, check if it was clicked
            if self.selected_neuron:
                if not self.selected_neuron[SurfDesc.ABSOLUTE_RECT].collidepoint(
                    event.pos
                ):
                    # Reset selected neuron's surface and update desc text
                    self.selected_neuron[SurfDesc.CURRENT_SURFACE] = (
                        self.selected_neuron[SurfDesc.SURFACE]
                    )
                    self.__update_neuron_text(neuron_type)
                    self.selected_neuron = {}
            else:
                # Update desc text when no neuron is selected
                self.__update_neuron_text(neuron_type)

    def update(self, context=None):
        # Blit all sensors and actuators
        for item in self.sensors + self.actuators:
            self.surface.blit(item[SurfDesc.CURRENT_SURFACE], item[SurfDesc.RECT])

        # Blit specific elements
        for element, desc in [
            (self.hidden_neuron, SurfDesc.CURRENT_SURFACE),
            (self.bias_neuron, SurfDesc.CURRENT_SURFACE),
            (self.sensor_desc, SurfDesc.SURFACE),
            (self.actuator_desc, SurfDesc.SURFACE),
            (self.unleash_organism_button, SurfDesc.CURRENT_SURFACE),
        ]:
            self.surface.blit(element[desc], element[SurfDesc.RECT])

        self.surface.blit(
            self.neural_frame[SurfDesc.SURFACE], self.neural_frame[SurfDesc.RECT]
        )
        for connection in self.neural_frame["connections"]:
            pygame.draw.line(
                self.surface,
                self.neural_frame["graph_desc"]["line"]["color"],
                connection[0][SurfDesc.RECT].center,
                connection[1][SurfDesc.RECT].center,
                self.neural_frame["graph_desc"]["line"]["thickness"],
            )
        for node in self.neural_frame["nodes"]:
            self.surface.blit(node[SurfDesc.CURRENT_SURFACE], node[SurfDesc.RECT])

    def _setup_surface(self):
        surface = pygame.Surface(
            size=pygame.image.load(
                os.path.join(image_assets, "laboratory", "laboratory_bg.svg")
            ).get_size(),
            flags=pygame.SRCALPHA,
        )

        titles = [
            ("sensor_title.svg", (62, 640)),
            ("actuator_title.svg", (666, 640)),
            ("hidden_neuron_title.svg", (1304, 206)),
            ("bias_neuron_title.svg", (1304, 363)),
            ("help_screen.svg", (1304, 519)),
        ]

        for title, pos in titles:
            title_image = pygame.image.load(
                os.path.join(image_assets, "laboratory", "neural_lab", title)
            )
            surface.blit(title_image, title_image.get_rect(topleft=pos))

        return surface

    def _configure_neurons(self, neuron_type: NeuronType, neurons: list):
        if neurons is None:
            neurons = []

        desc_attr = f"{neuron_type.value}_desc"
        setattr(
            self,
            desc_attr,
            {
                SurfDesc.SURFACE: pygame.Surface((450, 50)),
                "position": {
                    "topleft": (
                        (62, 690) if neuron_type == NeuronType.SENSOR else (666, 690)
                    )
                },
                SurfDesc.RECT: None,
                SurfDesc.ABSOLUTE_RECT: None,
                "default_text": helper.split_text(
                    f"Select a {neuron_type.value} to view more information..."
                ),
            },
        )

        desc = getattr(self, desc_attr)
        desc[SurfDesc.RECT] = desc[SurfDesc.SURFACE].get_rect(**desc["position"])
        self.__update_neuron_text(neuron_type)

        num_neurons = len(neurons)
        y_start, x_start = (790, 87) if neuron_type == NeuronType.SENSOR else (790, 691)
        y_offset, x_offset, x_max = (
            15,
            67,
            600 if neuron_type == NeuronType.SENSOR else 1200,
        )

        neuron_list_attr = f"{neuron_type.value}s"
        setattr(self, neuron_list_attr, [])

        for i in range(num_neurons):
            neuron_surface = pygame.Surface((55, 55))
            neuron_surface.fill(color=Colors.primary)
            pygame.gfxdraw.aacircle(neuron_surface, 25, 25, 25, Colors.bg_color)

            text = self.body_font.render(neurons[i]["name"], True, Colors.bg_color)
            neuron_surface.blit(text, text.get_rect(center=(25, 25)))

            clicked_neuron_surface = pygame.Surface((55, 55))
            clicked_neuron_surface.fill(color=Colors.primary)
            pygame.draw.circle(clicked_neuron_surface, Colors.bg_color, (25, 25), 25)

            text = self.body_font.render(neurons[i]["name"], True, Colors.primary)
            clicked_neuron_surface.blit(text, text.get_rect(center=(25, 25)))

            x = x_start + (x_offset * i)
            y = y_start if x < x_max else y_start + y_offset

            getattr(self, neuron_list_attr).append(
                {
                    "id": neurons[i]["id"],
                    "name": neurons[i]["name"],
                    "desc": helper.split_text(neurons[i]["desc"]),
                    SurfDesc.CURRENT_SURFACE: neuron_surface,
                    SurfDesc.SURFACE: neuron_surface,
                    SurfDesc.CLICKED_SURFACE: clicked_neuron_surface,
                    SurfDesc.RECT: neuron_surface.get_rect(center=(x, y)),
                    SurfDesc.ABSOLUTE_RECT: neuron_surface.get_rect(
                        topleft=(
                            x - 25 + self.surface_x_offset,
                            y - 25 + self.surface_y_offset,
                        ),
                    ),
                }
            )

    def _configure_hidden_neuron(self):
        x, y = 1700, 310

        neuron_surface = pygame.Surface((55, 55))
        neuron_surface.fill(color=Colors.primary)
        pygame.gfxdraw.aacircle(neuron_surface, 25, 25, 25, Colors.bg_color)

        text = self.body_font.render("H", True, Colors.bg_color)
        neuron_surface.blit(text, text.get_rect(center=(25, 25)))

        clicked_neuron_surface = pygame.Surface((55, 55))
        clicked_neuron_surface.fill(color=Colors.primary)
        pygame.draw.circle(clicked_neuron_surface, Colors.bg_color, (25, 25), 25)

        text = self.body_font.render("H", True, Colors.primary)
        clicked_neuron_surface.blit(text, text.get_rect(center=(25, 25)))

        self.hidden_neuron = {
            "name": "H",
            "desc": helper.split_text(
                "A hidden neuron connects input to output neurons."
            ),
            SurfDesc.CURRENT_SURFACE: neuron_surface,
            SurfDesc.SURFACE: neuron_surface,
            SurfDesc.CLICKED_SURFACE: clicked_neuron_surface,
            SurfDesc.RECT: neuron_surface.get_rect(center=(x, y)),
            SurfDesc.ABSOLUTE_RECT: neuron_surface.get_rect(
                topleft=(
                    x - 25 + self.surface_x_offset,
                    y - 25 + self.surface_y_offset,
                ),
            ),
        }

    def _configure_bias_neuron(self):
        x, y = 1700, 460

        neuron_surface = pygame.Surface((55, 55))
        neuron_surface.fill(color=Colors.primary)
        pygame.gfxdraw.aacircle(neuron_surface, 25, 25, 25, Colors.bg_color)

        text = self.body_font.render("B", True, Colors.bg_color)
        neuron_surface.blit(text, text.get_rect(center=(25, 25)))

        clicked_neuron_surface = pygame.Surface((55, 55))
        clicked_neuron_surface.fill(color=Colors.primary)
        pygame.draw.circle(clicked_neuron_surface, Colors.bg_color, (25, 25), 25)

        text = self.body_font.render("B", True, Colors.primary)
        clicked_neuron_surface.blit(text, text.get_rect(center=(25, 25)))

        self.bias_neuron = {
            "name": "B",
            "desc": helper.split_text(
                "Bias shifts the neuron's output to help it activate."
            ),
            SurfDesc.CURRENT_SURFACE: neuron_surface,
            SurfDesc.SURFACE: neuron_surface,
            SurfDesc.CLICKED_SURFACE: clicked_neuron_surface,
            SurfDesc.RECT: neuron_surface.get_rect(center=(x, y)),
            SurfDesc.ABSOLUTE_RECT: neuron_surface.get_rect(
                topleft=(
                    x - 25 + self.surface_x_offset,
                    y - 25 + self.surface_y_offset,
                ),
            ),
        }

    def __update_neuron_text(
        self, neuron_type: NeuronType, neuron_desc_text: list = None
    ):
        desc_attr = f"{neuron_type.value}_desc"
        desc = getattr(self, desc_attr, None)
        if not desc:
            return

        if not neuron_desc_text:
            neuron_desc_text = desc["default_text"]

        desc[SurfDesc.SURFACE].fill(Colors.primary)
        text_y = 0
        for text in neuron_desc_text:
            text = self.body_font.render(text, True, Colors.bg_color, Colors.primary)
            desc[SurfDesc.SURFACE].blit(text, text.get_rect(topleft=(0, text_y)))
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
        self.surface.blit(self.pic_circle["bg_image"], self.pic_circle[SurfDesc.RECT])
        self.surface.blit(
            self.__rotate_pic_circle_organism(), self.pic_circle["organism_rect"]
        )
        self.surface.blit(
            self.__rotate_pic_circle_border(), self.pic_circle["border_rect"]
        )
        self.surface.blit(
            self.neural_network_button[SurfDesc.CURRENT_SURFACE],
            self.neural_network_button[SurfDesc.RECT],
        )

        for option, value in self.traits_schema["options"].items():
            self.surface.blit(
                value[SurfDesc.SURFACE],
                value[SurfDesc.RECT],
            )

            if value["type"] == "single_choice_list":
                for choice in value["choices"]:
                    self.surface.blit(
                        (
                            choice["surface_selected"]
                            if choice["selected"]
                            else choice[SurfDesc.SURFACE]
                        ),
                        choice[SurfDesc.RECT],
                    )
            elif value["type"] == "user_input_int":
                self.__update_user_input(
                    value, value[SurfDesc.SURFACE], input_type="int"
                )
            elif value["type"] == "user_input_str":
                self.__update_user_input(
                    value, value[SurfDesc.SURFACE], input_type="str"
                )
            elif value["type"] == "user_input_color":
                self.__update_user_input(
                    value, value[SurfDesc.SURFACE], input_type="color"
                )

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
            "base_pop": int(
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
            self.traits_schema["options"][option][SurfDesc.SURFACE] = option_surface
            self.traits_schema["options"][option][SurfDesc.RECT] = (
                option_surface.get_rect(topleft=(x, y))
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
        value[SurfDesc.ABSOLUTE_RECT] = text_surface.get_rect(
            topleft=(
                x + 200 + self.surface_x_offset,
                y + self.surface_y_offset,
            )
        )

    def __configure_single_choice_list(self, value, option_surface, x, y):
        choice_x = 200
        for choice in value["choices"]:
            for state, color in [
                (SurfDesc.SURFACE, self.traits_schema["bg_color"]),
                ("surface_selected", self.traits_schema["text_color"]),
            ]:
                text = self.traits_schema["font"].render(
                    choice["value"],
                    True,
                    (
                        self.traits_schema["text_color"]
                        if state == SurfDesc.SURFACE
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

            choice[SurfDesc.RECT] = choice[SurfDesc.SURFACE].get_rect(
                topleft=(x + choice_x, y)
            )
            choice[SurfDesc.ABSOLUTE_RECT] = choice[SurfDesc.SURFACE].get_rect(
                topleft=(
                    x + choice_x + self.surface_x_offset,
                    y + self.surface_y_offset,
                )
            )
            choice_x += choice[SurfDesc.SURFACE].get_width() + 10

    def __configure_neural_network_button(self):
        self.neural_network_button = {
            SurfDesc.CURRENT_SURFACE: None,
            SurfDesc.SURFACE: pygame.image.load(
                os.path.join(
                    image_assets, "laboratory", "attrs_lab", "neural_network_button.svg"
                )
            ),
            SurfDesc.CLICKED_SURFACE: pygame.image.load(
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
        self.neural_network_button[SurfDesc.RECT] = self.neural_network_button.get(
            SurfDesc.SURFACE
        ).get_rect(**self.neural_network_button["position"])

        self.neural_network_button[
            SurfDesc.ABSOLUTE_RECT
        ] = self.neural_network_button.get(SurfDesc.SURFACE).get_rect(
            topleft=(
                np.array(self.neural_network_button[SurfDesc.RECT].topleft)
                + np.array(
                    (
                        self.surface_x_offset,
                        self.surface_y_offset,
                    )
                )
            )
        )

        self.neural_network_button[SurfDesc.CURRENT_SURFACE] = (
            self.neural_network_button.get(SurfDesc.SURFACE)
        )

    def __configure_dp_circle(self):
        self.pic_circle = {
            "organism_image": pygame.image.load(
                os.path.join(image_assets, "critters", "triangle.svg"),
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

        self.pic_circle[SurfDesc.RECT] = self.pic_circle["bg_image"].get_rect(
            **self.pic_circle["position"]
        )
        self.pic_circle["border_rect"] = self.pic_circle[SurfDesc.RECT]
        self.pic_circle["organism_rect"] = self.pic_circle["organism_image"].get_rect(
            **self.pic_circle["position"]
        )

    def __handle_neural_network_button(self, event):
        """Handle neural network button clicks."""
        if self.neural_network_button[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.neural_network_button[SurfDesc.CURRENT_SURFACE] = (
                    self.neural_network_button[SurfDesc.CLICKED_SURFACE]
                )
            elif event.type == pygame.MOUSEBUTTONUP:
                return True  # Proceed with navigation if clicked
        else:
            # Reset the button image when not clicked
            self.neural_network_button[SurfDesc.CURRENT_SURFACE] = (
                self.neural_network_button[SurfDesc.SURFACE]
            )
        return False

    def __navigate_to_neural_lab(self):
        """Return the navigation message for neural lab."""
        return MessagePacket(
            EventType.NAVIGATION,
            "neural_lab",
            context={EventType.GENESIS: self.__get_user_input()},
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
            if choice[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    selected_choice = choice["value"]

        if selected_choice:
            for choice in value["choices"]:
                choice["selected"] = choice["value"] == selected_choice

    def __handle_user_input(self, event, value, option):
        """Handle user input (text, color, integer)."""
        if value[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
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
            center=self.pic_circle[SurfDesc.RECT].center
        )
        return rotated_image

    def __rotate_pic_circle_organism(self):
        self.pic_circle["organism_angle"] += 1
        rotated_image = pygame.transform.rotate(
            self.pic_circle["organism_image"], self.pic_circle["organism_angle"]
        )
        self.pic_circle["organism_rect"] = rotated_image.get_rect(
            center=self.pic_circle[SurfDesc.RECT].center
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
