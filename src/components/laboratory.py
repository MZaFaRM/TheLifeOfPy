import enum
import os
import re
import time
import uuid

import numpy as np
import pygame
import pygame.gfxdraw

from src.config import Colors, Fonts, InvalidConnection, image_assets
from src.enums import Attributes, Defence, EventType, MessagePacket, NeuronType, SurfDesc, Shapes
from src.handlers.genetics import NeuronManager
import src.helper as helper


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

        self.__create_back_button()

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
                    **self.user_inputs,
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

    def __create_back_button(self):
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
        self.neural_frame["selection"] = {"type": None, "value": None}
        self.neural_frame["connections"] = []
        self.neural_frame["errors"] = {}
        self.neural_frame["graph_desc"] = {
            "circle": {
                "radius": 25,
                Attributes.COLOR: {
                    NeuronType.SENSOR: (74, 227, 181, 175),
                    NeuronType.ACTUATOR: (0, 255, 127, 175),
                    NeuronType.HIDDEN: (0, 163, 108, 175),
                    NeuronType.BIAS: (0, 139, 139, 175),
                },
            },
            "line": {
                "thickness": 5,
                Attributes.COLOR: (23, 86, 67),
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
        elif event.type == pygame.KEYDOWN:
            return self._handle_keydown(event)

    def _handle_keydown(self, event):
        """Handles key press events related to neuron selection and editing."""
        selection = self.neural_frame["selection"]
        neuron_type = selection["type"]
        value = selection["value"]

        # Handle neuron deletion
        if event.key == pygame.K_DELETE:
            return self.__handle_neural_frame_deletion(event)

        # Deselect any selected neuron when Enter or Escape is pressed
        elif event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
            self.neural_frame["selection"] = {"type": None, "value": None}

        # Handle backspace key for connection neurons
        elif event.key == pygame.K_BACKSPACE:
            if neuron_type == NeuronType.CONN:
                value[2] = self._handle_backspace(value[2])

        # Handle numeric input for connection neurons
        elif re.match(r"[-+\.0-9]", event.unicode) and neuron_type == NeuronType.CONN:
            # Determine which value to modify
            value[2] = self._handle_numeric_input(event, value[2])

    def _handle_numeric_input(self, event, data):
        """Handles numeric input for connection values."""
        if event.unicode == "-":
            if data != "0":
                data = event.unicode + data.lstrip("-")
        elif event.unicode == "+":
            if data != "0":
                data = data.lstrip("+-")

        elif event.unicode == ".":
            if "." not in data:
                data += "."

        elif event.unicode.isdigit():
            if data in {"0", "-0", "+0"}:
                data = data[0] + event.unicode if data[0] in "+-" else event.unicode
            else:
                data += event.unicode
        return data

    def _handle_backspace(self, data):
        """Handles backspace deletion for connection values."""
        data = data[:-1] or "0"
        if data == "-":
            data = "0"
        return data

    def _handle_mouse_down(self, event):
        for res in (
            self.__handle_neuron_click(event),
            self.__handle_neural_frame_click(event),
            self.__handle_neural_node_creation(event),
            self.__handle_unleash_organism_on_mouse_down(event),
        ):
            if res:
                return res

    def __handle_neural_frame_deletion(self, event):
        if self.neural_frame["selection"]["value"]:
            selection = self.neural_frame["selection"]
            if selection["type"] == NeuronType.CONN:
                for connection in self.neural_frame["connections"]:
                    if (
                        connection[0]["id"] == selection["value"][0]["id"]
                        and connection[1]["id"] == selection["value"][1]["id"]
                    ):
                        self.neural_frame["connections"].remove(connection)
            else:
                for node in self.neural_frame["nodes"]:
                    if node["id"] == selection["value"]["id"]:
                        self.neural_frame["nodes"].remove(node)
                        for connection in self.neural_frame["connections"].copy():
                            if (
                                connection[0]["id"] == node["id"]
                                or connection[1]["id"] == node["id"]
                            ):
                                self.neural_frame["connections"].remove(connection)
            self.neural_frame["selection"] = {"type": None, "value": None}

    def __handle_neural_frame_click(self, event):
        selected_any = False
        if self.neural_frame["selection"]["type"] == NeuronType.CONN:
            self.neural_frame["selection"] = {"type": None, "value": None}
            return

        for node in self.neural_frame["nodes"]:
            if node[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
                selected_any = True
                if self.neural_frame["selection"]["value"]:
                    try:
                        self.__check_connection_validity(
                            self.neural_frame["selection"]["value"], node
                        )
                        # Add the connection, with default weight of 1
                        self.neural_frame["connections"].append(
                            [self.neural_frame["selection"]["value"], node, "1"]
                        )
                    except InvalidConnection as e:
                        self.neural_frame["errors"] = {
                            "connection": [
                                self.neural_frame["selection"]["value"],
                                node,
                            ],
                            "message": str(e),
                        }
                    self.neural_frame["selection"] = {"type": None, "value": None}

                else:
                    node[SurfDesc.CURRENT_SURFACE] = node[SurfDesc.CLICKED_SURFACE]
                    self.neural_frame["selection"].update(
                        {"type": node["type"], "value": node}
                    )
            else:
                node[SurfDesc.CURRENT_SURFACE] = node[SurfDesc.SURFACE]

        if not selected_any:
            self.neural_frame["selection"] = {"type": None, "value": None}

            pos = (
                event.pos[0] - self.surface_x_offset,
                event.pos[1] - self.surface_y_offset,
            )

            for connection in self.neural_frame["connections"]:
                if helper.is_point_on_line(
                    pos,
                    connection[0][SurfDesc.RECT].center,
                    connection[1][SurfDesc.RECT].center,
                    width=5,
                ):
                    self.neural_frame["selection"].update(
                        {"type": NeuronType.CONN, "value": connection}
                    )
                    break

    def __check_connection_validity(self, node_1, node_2):
        # Ensure both nodes exist
        if not node_1.get("id", None) or not node_2.get("id", None):
            raise InvalidConnection(
                "Invalid connection: One or more nodes do not exist"
            )

        # Prevent self-connections
        if node_1.get("id") == node_2.get("id"):
            raise InvalidConnection(
                "Invalid connection: Cannot connect a node to itself"
            )

        # Ensure nodes are not already connected
        for connection in self.neural_frame["connections"]:
            if (
                connection[0]["id"] == node_1["id"]
                and connection[1]["id"] == node_2["id"]
            ) or (
                connection[0]["id"] == node_2["id"]
                and connection[1]["id"] == node_1["id"]
            ):
                raise InvalidConnection(
                    "Invalid connection: Nodes are already connected"
                )

        # Enforce directional rules
        if node_1["type"] == NeuronType.SENSOR and node_2["type"] == NeuronType.SENSOR:
            raise InvalidConnection(
                "Invalid connection: Sensors cannot connect to other sensors"
            )

        if (
            node_1["type"] == NeuronType.ACTUATOR
            and node_2["type"] == NeuronType.ACTUATOR
        ):
            raise InvalidConnection(
                "Invalid connection: Actuators cannot connect to other actuators"
            )

        if node_2["type"] == NeuronType.SENSOR:
            raise InvalidConnection(
                "Invalid connection: Sensors cannot receive connections"
            )

        if node_1["type"] == NeuronType.ACTUATOR:
            raise InvalidConnection(
                "Invalid connection: Actuators cannot send connections"
            )

        # Prevent cycles if required (optional, depends on your structure)
        if self.__has_cycle(node_1, node_2):
            raise InvalidConnection("Invalid connection: Connection creates a cycle")

        return True

    def __has_cycle(self, node_1, node_2):
        # Create a directed adjacency list from the connections
        adjacency_list = {}
        for src, dst, weight in self.neural_frame["connections"]:
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
        if not self.selected_neuron or not self.neural_frame[
            SurfDesc.ABSOLUTE_RECT
        ].collidepoint(event.pos):
            return

        # Get the properties of the shape to draw
        shape = self.neural_frame["graph_desc"]["circle"]
        radius = shape["radius"]
        color = shape[Attributes.COLOR][self.selected_neuron["type"]]
        pos = (
            event.pos[0] - self.surface_x_offset,
            event.pos[1] - self.surface_y_offset,
        )

        # Create surfaces
        surface = pygame.Surface(((radius * 2) + 1, (radius * 2) + 1), pygame.SRCALPHA)
        pygame.draw.circle(surface, color, (radius, radius), radius)

        selected_surface = pygame.Surface(
            ((radius * 2) + 1, (radius * 2) + 1), pygame.SRCALPHA
        )
        pygame.draw.circle(selected_surface, (255, 255, 255), (radius, radius), radius)
        pygame.draw.circle(selected_surface, color, (radius, radius), radius - 5)

        # Define the new neuron properties
        new_neuron = {
            "id": uuid.uuid4(),
            "name": self.selected_neuron["name"],
            "type": self.selected_neuron["type"],
            SurfDesc.SURFACE: surface,
            SurfDesc.CURRENT_SURFACE: surface,
            SurfDesc.CLICKED_SURFACE: selected_surface,
            SurfDesc.RECT: surface.get_rect(center=pos),
            SurfDesc.ABSOLUTE_RECT: surface.get_rect(
                topleft=(
                    pos[0] + self.surface_x_offset - radius,
                    pos[1] + self.surface_y_offset - radius,
                ),
            ),
        }

        # Write name of the neuron on the surface
        text = self.body_font.render(
            self.selected_neuron["name"], True, Colors.bg_color
        )
        surface.blit(text, text.get_rect(center=(radius, radius)))
        selected_surface.blit(text, text.get_rect(center=(radius, radius)))

        # Add the new neuron to the frame and reset selection
        self.neural_frame["nodes"].append(new_neuron)
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
                    (conn[0]["id"], conn[0]["name"], conn[0]["type"], float(conn[2])),
                    (conn[1]["id"], conn[1]["name"], conn[1]["type"], float(conn[2])),
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

    def __get_connection_thickness(self, weight):
        """Returns the thickness of the connection line based on weight."""
        return (max(abs(int(float(weight))), 1) + 3) * 2

    def update(self, context=None):
        # Blit all sensors and actuators
        for item in self.sensors + self.actuators:
            self.surface.blit(item[SurfDesc.CURRENT_SURFACE], item[SurfDesc.RECT])

        self.surface.blit(
            self.hidden_neuron[SurfDesc.CURRENT_SURFACE],
            self.hidden_neuron[SurfDesc.RECT],
        )
        self.surface.blit(
            self.bias_neuron[SurfDesc.CURRENT_SURFACE], self.bias_neuron[SurfDesc.RECT]
        )
        self.surface.blit(
            self.sensor_desc[SurfDesc.SURFACE], self.sensor_desc[SurfDesc.RECT]
        )
        self.surface.blit(
            self.actuator_desc[SurfDesc.SURFACE], self.actuator_desc[SurfDesc.RECT]
        )
        self.surface.blit(
            self.unleash_organism_button[SurfDesc.CURRENT_SURFACE],
            self.unleash_organism_button[SurfDesc.RECT],
        )
        self.surface.blit(
            self.neural_frame[SurfDesc.SURFACE], self.neural_frame[SurfDesc.RECT]
        )

        get_connection_thickness = (
            lambda x: (max(abs(int(float(x))), 1) + 3) * 2
        )  # (Weight + 3) * 2
        for connection in self.neural_frame["connections"]:
            pygame.draw.line(
                self.surface,
                self.neural_frame["graph_desc"]["line"][Attributes.COLOR],
                connection[0][SurfDesc.RECT].center,
                connection[1][SurfDesc.RECT].center,
                self.__get_connection_thickness(connection[2]),
            )

        # Selection is connection node
        if self.neural_frame["selection"]["type"] == NeuronType.CONN:
            self.draw_connection_line(self.neural_frame["selection"]["value"])

        for node in self.neural_frame["nodes"]:
            self.surface.blit(node[SurfDesc.CURRENT_SURFACE], node[SurfDesc.RECT])

        if self.neural_frame["errors"]:
            error_surface, error_rect = self.__error_message_surface()
            self.surface.blit(error_surface, error_rect)

    def __error_message_surface(self):
        text_surface = self.help_screen[SurfDesc.SURFACE].copy()
        if self.neural_frame["errors"]:
            error = self.neural_frame["errors"]
            connection = error["connection"]
            message = helper.split_text(error["message"], 36)
            text_surface_connection = self.body_font.render(
                f"{connection[0]['name']} -> {connection[1]['name']}",
                True,
                Colors.primary,
            )
            text_surface.blit(
                text_surface_connection,
                text_surface_connection.get_rect(topleft=(30, 150)),
            )

            for i, line in enumerate(message):
                text_surface_message = self.body_font.render(line, True, Colors.primary)
                text_surface.blit(
                    text_surface_message,
                    text_surface_message.get_rect(topleft=(30, 180 + (i * 20))),
                )
        return text_surface, self.help_screen[SurfDesc.RECT]

    def draw_connection_line(self, connection):
        # Get the centers of the two connection points
        p1 = connection[0][SurfDesc.RECT].center
        p2 = connection[1][SurfDesc.RECT].center

        # Compute the midpoint
        mid_x = (p1[0] + p2[0]) // 2
        mid_y = (p1[1] + p2[1]) // 2

        # Draw the line
        pygame.draw.line(
            self.surface,
            Colors.primary,
            p1,
            p2,
            self.__get_connection_thickness(connection[2]),
        )

        # Draw the pentagon
        pygame.draw.circle(
            self.surface, color=Colors.primary, center=(mid_x, mid_y), radius=25
        )

        text = self.body_font.render(connection[2], Colors.bg_color, Colors.bg_color)
        self.surface.blit(text, text.get_rect(center=(mid_x - 0, mid_y)))

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
        ]

        for title, pos in titles:
            title_image = pygame.image.load(
                os.path.join(image_assets, "laboratory", "neural_lab", title)
            )
            surface.blit(title_image, title_image.get_rect(topleft=pos))

        self.help_screen = {}
        self.help_screen[SurfDesc.SURFACE] = pygame.image.load(
            os.path.join(image_assets, "laboratory", "neural_lab", "help_screen.svg")
        )
        self.help_screen[SurfDesc.RECT] = self.help_screen[SurfDesc.SURFACE].get_rect(
            topleft=(1304, 519)
        )
        surface.blit(
            self.help_screen[SurfDesc.SURFACE], self.help_screen[SurfDesc.RECT]
        )

        return surface

    def _configure_neurons(self, neuron_type: NeuronType, neurons: list = None):
        neurons = neurons or []

        # Set up description attributes
        if neuron_type == NeuronType.SENSOR:
            self.sensor_desc = {
                SurfDesc.SURFACE: pygame.Surface((450, 50)),
                "position": {"topleft": (62, 690)},
                SurfDesc.RECT: None,
                SurfDesc.ABSOLUTE_RECT: None,
                "default_text": helper.split_text(
                    "Select a sensor to view more information..."
                ),
            }
            desc = self.sensor_desc
        else:  # NeuronType.ACTUATOR
            self.actuator_desc = {
                SurfDesc.SURFACE: pygame.Surface((450, 50)),
                "position": {"topleft": (666, 690)},
                SurfDesc.RECT: None,
                SurfDesc.ABSOLUTE_RECT: None,
                "default_text": helper.split_text(
                    "Select an actuator to view more information..."
                ),
            }
            desc = self.actuator_desc

        desc[SurfDesc.RECT] = desc[SurfDesc.SURFACE].get_rect(**desc["position"])
        self.__update_neuron_text(neuron_type)

        # Set neuron layout parameters
        if neuron_type == NeuronType.SENSOR:
            x_start, x_max = 20, 600
            self.sensors = []
            neuron_list = self.sensors
        else:  # NeuronType.ACTUATOR
            x_start, x_max = 624, 1200
            self.actuators = []
            neuron_list = self.actuators

        # Neuron positioning variables
        x, y = x_start, 790
        x_offset, y_offset = 67, 67

        # Create neuron representations
        for neuron in neurons:
            neuron_surfaces = self._create_neuron_surfaces(neuron["name"])

            x += x_offset
            if x > x_max:
                y += y_offset
                x = x_start + x_offset

            neuron_list.append(
                {
                    "id": neuron["id"],
                    "name": neuron["name"],
                    "desc": helper.split_text(neuron["desc"]),
                    SurfDesc.CURRENT_SURFACE: neuron_surfaces["normal"],
                    SurfDesc.SURFACE: neuron_surfaces["normal"],
                    SurfDesc.CLICKED_SURFACE: neuron_surfaces["clicked"],
                    SurfDesc.RECT: neuron_surfaces["normal"].get_rect(center=(x, y)),
                    SurfDesc.ABSOLUTE_RECT: neuron_surfaces["normal"].get_rect(
                        topleft=(
                            x - 25 + self.surface_x_offset,
                            y - 25 + self.surface_y_offset,
                        ),
                    ),
                }
            )

    def _create_neuron_surfaces(self, text):
        """Creates normal and clicked neuron surfaces."""
        normal = pygame.Surface((55, 55))
        normal.fill(Colors.primary)
        pygame.gfxdraw.aacircle(normal, 25, 25, 25, Colors.bg_color)

        text_render = self.body_font.render(text, True, Colors.bg_color)
        normal.blit(text_render, text_render.get_rect(center=(25, 25)))

        clicked = pygame.Surface((55, 55))
        clicked.fill(Colors.primary)
        pygame.draw.circle(clicked, Colors.bg_color, (25, 25), 25)

        text_render = self.body_font.render(text, True, Colors.primary)
        clicked.blit(text_render, text_render.get_rect(center=(25, 25)))

        return {"normal": normal, "clicked": clicked}

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

        self.__create_dp_circle()

        self.__create_user_input_section()
        self.__create_neural_network_button()

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
                    option, value, value[SurfDesc.SURFACE], input_type="int"
                )
            elif value["type"] == "user_input_str":
                self.__update_user_input(
                    option, value, value[SurfDesc.SURFACE], input_type="str"
                )
            elif value["type"] == "user_input_color":
                data = self.__update_user_input(
                    option, value, value[SurfDesc.SURFACE], input_type=Attributes.COLOR
                )
                self.pic_circle[Attributes.COLOR] = helper.hex_to_rgb(
                    data.replace("-", "0")
                )
                self.pic_circle["update"] = True

        if self.pic_circle["update"]:
            self.__draw_critter()
            self.pic_circle["update"] = False

    def event_handler(self, event):
        if event.type in [pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP]:
            # Handle the button click events
            if self.__handle_neural_network_button(event):
                return self.__navigate_to_neural_lab()

            if event.type == pygame.MOUSEBUTTONDOWN:
                # Handle interaction with traits options
                self.__handle_traits_options(event)

        elif event.type == pygame.KEYDOWN:
            selected_option = self.traits_schema["selected_option"]
            selected_option_type = self.traits_schema["selected_option_type"]
            # Handle keyboard events (backspace, alphanumeric, navigation)
            self.__handle_keydown_event(event, selected_option, selected_option_type)

    def __get_user_input(self):
        trait_options = self.traits_schema["options"]
        get_choice = lambda option: next(
            choice["value"]
            for choice in trait_options[option]["choices"]
            if choice["selected"]
        )
        get_data = lambda option: trait_options[option]["data"]

        return {
            Attributes.BASE_POPULATION: int(get_data(self.INITIAL_POPULATION)),
            Attributes.SPECIES: get_data(self.SPECIES),
            Attributes.DEFENSE_MECHANISM: get_choice(self.DEFENSE_MECHANISM),
            Attributes.DOMAIN: get_choice(self.DOMAIN),
            Attributes.VISION_RADIUS: int(get_data(self.VISION_RADIUS)),
            Attributes.SIZE: int(get_data(self.SIZE)),
            Attributes.AGE_OF_MATURITY: int(get_data(self.AGE_OF_MATURITY)),
            Attributes.COLOR: helper.hex_to_rgb(get_data(self.COLOR)),
            Attributes.MAX_SPEED: int(get_data(self.MAX_SPEED)),
            Attributes.MAX_LIFESPAN: int(get_data(self.MAX_LIFESPAN)),
            Attributes.MAX_ENERGY: int(get_data(self.MAX_ENERGY)),
        }

    def __create_user_input_section(self):
        self.traits_schema = self.__create_traits_schema()
        self.__create_user_input_surfaces()

    def __create_traits_schema(self):
        self.INITIAL_POPULATION = "Initial Population: "
        self.SPECIES = "Species: "
        self.DEFENSE_MECHANISM = "Defense Mechanism: "
        self.AGE_OF_MATURITY = "Age of Maturity: "
        self.DOMAIN = "Domain: "
        self.VISION_RADIUS = "Vision Radius: "
        self.SIZE = "Size: "
        self.COLOR = "Color: "
        self.MAX_SPEED = "Max Speed: "
        self.MAX_ENERGY = "Max Energy: "
        self.MAX_LIFESPAN = "Max Lifespan: "

        return {
            "font": pygame.font.Font(Fonts.PixelifySansMedium, 21),
            "text_color": pygame.Color(0, 0, 0),
            "bg_color": pygame.Color(74, 227, 181),
            "yIncrement": 34,
            "highlight_width": 25,
            "selected_option": self.INITIAL_POPULATION,
            "selected_option_type": "user_input_int",
            "options": {
                self.INITIAL_POPULATION: {
                    "type": "user_input_int",
                    "data": "10",
                    "max" : 1000,
                },
                self.SPECIES: {
                    "type": "user_input_str",
                    "data": helper.generate_species_name(),
                },
                self.DEFENSE_MECHANISM: {
                    "choices": [
                        {"value": Defence.NONE, "selected": True},
                        {"value": Defence.SWORDLING, "selected": False},
                        {"value": Defence.SHIELDLING, "selected": False},
                        {"value": Defence.CAMOUFLING, "selected": False},
                    ],
                    "type": "single_choice_list",
                },
                self.DOMAIN: {
                    "choices": [
                        {"value": Shapes.SQUARE, "selected": True},
                        {"value": Shapes.CIRCLE, "selected": False},
                        {"value": Shapes.TRIANGLE, "selected": False},
                        {"value": Shapes.PENTAGON, "selected": False},
                    ],
                    "type": "single_choice_list",
                },
                self.VISION_RADIUS: {
                    "type": "user_input_int",
                    "data": "40",
                    "max" : 100,
                },
                self.AGE_OF_MATURITY: {
                    "type": "user_input_int",
                    "data": "200",
                },
                self.SIZE: {
                    "type": "user_input_int",
                    "data": "10",
                    "max" : 100,
                },
                self.COLOR: {
                    "type": "user_input_color",
                    "data": helper.get_random_color()[1:],
                },
                self.MAX_SPEED: {
                    "type": "user_input_int",
                    "data": "1",
                },
                self.MAX_LIFESPAN: {
                    "type": "user_input_int",
                    "data": "100000",
                },
                self.MAX_ENERGY: {
                    "type": "user_input_int",
                    "data": "1000",
                },
            },
        }

    def __create_user_input_surfaces(self):
        x, y = 75, 400
        for option, value in self.traits_schema["options"].items():
            option_surface = self.__create_option_surface(option)
            self.__create_option_rhs(option, value, option_surface, x, y)
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

    def __create_option_rhs(self, option, value, option_surface, x, y):
        if value["type"] == "user_input_int":
            self.__create_user_input(
                option, value, option_surface, x, y, input_type="int"
            )
        elif value["type"] == "user_input_str":
            self.__create_user_input(
                option, value, option_surface, x, y, input_type="str"
            )
        elif value["type"] == "user_input_color":
            self.__create_user_input(
                option, value, option_surface, x, y, input_type=Attributes.COLOR
            )
        elif value["type"] == "single_choice_list":
            self.__create_single_choice_list(option, value, option_surface, x, y)

    def __create_user_input(
        self, option, value, option_surface, x, y, input_type="str"
    ):
        # Get the data to display based on the input type
        data = value["data"]
        if input_type == "int":
            data = "{:,}".format(int(value["data"]))  # Format integer with commas
        elif input_type == Attributes.COLOR:
            data = "#" + data  # Format color as hex

        # Add a blinking cursor if the input is selected
        if (
            self.traits_schema["selected_option"] == option
            and (self.time // 20) % 2 == 0
        ):
            data += "_"

        # Render the text with the appropriate colors
        text = self.traits_schema["font"].render(
            data,
            True,
            self.traits_schema["bg_color"],
            self.traits_schema["text_color"],
        )

        # Create a surface for the text and blit the text onto it
        text_surface = pygame.Surface(
            (
                text.get_width() + 15,
                self.traits_schema["highlight_width"],
            )
        )

        # Update the absolute for the input field
        value[SurfDesc.ABSOLUTE_RECT] = text_surface.get_rect(
            topleft=(
                x + 200 + self.surface_x_offset,
                y + self.surface_y_offset,
            )
        ).inflate(1500, 0)

    def __create_single_choice_list(self, option, value, option_surface, x, y):
        choice_x = 200
        for choice in value["choices"]:
            for state, color in [
                (SurfDesc.SURFACE, self.traits_schema["bg_color"]),
                ("surface_selected", self.traits_schema["text_color"]),
            ]:
                data = choice["value"]
                if hasattr(choice["value"], "value"):
                    data = choice["value"].value

                text = self.traits_schema["font"].render(
                    data,
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
            
            rect_x = x + 50 + choice_x
            rect_y = y
            choice[SurfDesc.RECT] = choice[SurfDesc.SURFACE].get_rect(
                topleft=(rect_x, rect_y)
            )
            choice[SurfDesc.ABSOLUTE_RECT] = choice[SurfDesc.SURFACE].get_rect(
                topleft=(
                    rect_x + self.surface_x_offset,
                    rect_y + self.surface_y_offset,
                )
            )
            choice_x += choice[SurfDesc.SURFACE].get_width() + 10

    def __create_neural_network_button(self):
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

    def __create_dp_circle(self):
        self.pic_circle = {
            SurfDesc.CURRENT_SURFACE: None,
            SurfDesc.SURFACE: pygame.Surface((250, 250), pygame.SRCALPHA),
            "defense": "None",
            "shape": Shapes.SQUARE,
            "organism_angle": 0,
            "border_angle": 0,
            "update": True,
            Attributes.COLOR: (125, 255, 255),
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
        self.pic_circle["organism_rect"] = self.pic_circle[SurfDesc.SURFACE].get_rect(
            **self.pic_circle["position"]
        )

        self.pic_circle[SurfDesc.CURRENT_SURFACE] = self.pic_circle[
            SurfDesc.SURFACE
        ].copy()

    def __draw_critter(self):
        shape = self.pic_circle["shape"]
        color = self.pic_circle[Attributes.COLOR]
        defense = self.pic_circle["defense"]

        self.pic_circle[SurfDesc.CURRENT_SURFACE] = surface = self.pic_circle[
            SurfDesc.SURFACE
        ].copy()
        rect = pygame.Rect(0, 0, 50, 50)
        rect.center = (surface.get_width() // 2, surface.get_height() // 2)

        if defense == Defence.SWORDLING:
            square_1 = helper.get_square_points(rect.inflate(75, 75))
            square_2 = helper.get_square_points(rect.inflate(75, 75), 45)
            pygame.draw.polygon(surface, (125, 28, 74, 180), square_1)
            pygame.draw.polygon(surface, (125, 28, 74, 180), square_2)
        elif defense == Defence.SHIELDLING:
            border_rect = pygame.Rect(0, 0, 75, 75)
            border_rect.center = (surface.get_width() // 2, surface.get_height() // 2)
            pygame.draw.rect(surface, (255, 255, 255), border_rect, 5)
        elif defense == Defence.CAMOUFLING:
            color = (color[0], color[1], color[2], int(0.5 * 255))

        if shape == Shapes.CIRCLE:
            pygame.draw.circle(surface, color, rect.center, rect.width // 2)
        elif shape == Shapes.SQUARE:
            pygame.draw.rect(surface, color, rect)
        elif shape == Shapes.TRIANGLE:
            pygame.draw.polygon(surface, color, helper.get_triangle_points(rect))
        elif shape == Shapes.PENTAGON:
            pygame.draw.polygon(surface, color, helper.get_pentagon_points(rect))

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

    def __handle_traits_options(self, event):
        """Handle interactions with traits options."""
        self.traits_schema.update(
            {
                "selected_option": None,
                "selected_option_type": None,
            }
        )

        for option, value in self.traits_schema["options"].items():
            if value["type"] == "single_choice_list":
                if self.__handle_single_choice_list(event, option, value):
                    break
            elif value["type"] in [
                "user_input_int",
                "user_input_str",
                "user_input_color",
            ]:
                self.__handle_user_input(event, value, option)

    def __handle_single_choice_list(self, event, option, value):
        """Handle single choice list interaction."""
        selected_choice = None
        for choice in value["choices"]:
            if choice[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos):
                if event.type == pygame.MOUSEBUTTONDOWN:
                    selected_choice = choice["value"]
                    break

        if selected_choice:
            self.traits_schema["selected_option"] = option
            if option == self.DOMAIN:
                self.pic_circle["shape"] = selected_choice
                self.pic_circle["update"] = True
            elif option == self.DEFENSE_MECHANISM:
                self.pic_circle["defense"] = selected_choice
                self.pic_circle["update"] = True

            for choice in value["choices"]:
                choice["selected"] = choice["value"] == selected_choice

    def __handle_user_input(self, event, value, option):
        """Handle user input (text, color, integer)."""
        if (
            value[SurfDesc.ABSOLUTE_RECT].collidepoint(event.pos)
            and event.type == pygame.MOUSEBUTTONDOWN
        ):
            self.traits_schema.update(
                {
                    "selected_option": option,
                    "selected_option_type": value["type"],
                }
            )
            return True
        return False

    def __handle_keydown_event(self, event, selected_option, selected_option_type):
        """Handle keydown events for user input and navigation."""
        if event.key == pygame.K_BACKSPACE:
            self.__handle_backspace(selected_option, selected_option_type)
        elif re.match(r"[a-zA-Z0-9 ]", event.unicode):
            self.__handle_alphanumeric_input(
                event, selected_option, selected_option_type
            )
        elif event.key == pygame.K_TAB:
            self.__handle_tab_navigation(selected_option, selected_option_type)
        elif event.key in [pygame.K_LEFT, pygame.K_RIGHT]:
            self.__handle_arrow_navigation(event, selected_option, selected_option_type)

    def __handle_backspace(self, selected_option, selected_option_type):
        """Handle backspace for input fields."""
        if selected_option_type == "user_input_str":
            self.traits_schema["options"][selected_option]["data"] = self.traits_schema[
                "options"
            ][selected_option]["data"][:-1]
        elif selected_option_type == "user_input_int":
            self.traits_schema["options"][selected_option]["data"] = (
                self.traits_schema["options"][selected_option]["data"][:-1] or "0"
            )
        elif selected_option_type == "user_input_color":
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
        if len(data) < 6 and re.match(r"[a-fA-F0-9]", event.unicode):
            self.traits_schema["options"][selected_option]["data"] = (
                data + event.unicode
            )

    def __handle_int_input(self, event, selected_option):
        """Handle input for integers."""
        if self.traits_schema["options"][selected_option].get("max"):
            # Ensure the input does not exceed the maximum value
            max_value = self.traits_schema["options"][selected_option]["max"]
            if int(self.traits_schema["options"][selected_option]["data"] + event.unicode) > max_value:
                return

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
        self.traits_schema.update(
            {
                "selected_option": next_option,
                "selected_option_type": self.traits_schema["options"][next_option][
                    "type"
                ],
            }
        )

    def __handle_arrow_navigation(self, event, selected_option, selected_option_type):
        """Navigate through choices using left and right arrow keys."""
        if selected_option_type == "single_choice_list":
            # Find the index of the currently selected choice
            selected_index = self.traits_schema["options"][selected_option][
                "choices"
            ].index(
                next(
                    choice
                    for choice in self.traits_schema["options"][selected_option][
                        "choices"
                    ]
                    if choice["selected"]
                )
            )

            if event.key == pygame.K_LEFT:
                new_index = (selected_index - 1) % len(
                    self.traits_schema["options"][selected_option]["choices"]
                )
            else:
                new_index = (selected_index + 1) % len(
                    self.traits_schema["options"][selected_option]["choices"]
                )

            self.traits_schema["options"][selected_option]["choices"][selected_index][
                "selected"
            ] = False
            self.traits_schema["options"][selected_option]["choices"][new_index][
                "selected"
            ] = True

            if selected_option == self.DOMAIN:
                self.pic_circle["update"] = True
                self.pic_circle["shape"] = self.traits_schema["options"][
                    selected_option
                ]["choices"][new_index]["value"]
            elif selected_option == self.DEFENSE_MECHANISM:
                self.pic_circle["update"] = True
                self.pic_circle["defense"] = self.traits_schema["options"][
                    selected_option
                ]["choices"][new_index]["value"]

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
            self.pic_circle[SurfDesc.CURRENT_SURFACE], self.pic_circle["organism_angle"]
        )
        self.pic_circle["organism_rect"] = rotated_image.get_rect(
            center=self.pic_circle[SurfDesc.RECT].center
        )
        return rotated_image

    def __update_user_input(self, option, value, option_surface, input_type="str"):
        data = value["data"]
        if input_type == "int":
            data = "{:,}".format(int(value["data"] or 0))
        elif input_type == Attributes.COLOR:
            data = "#" + data.ljust(6, "-").upper()

        if (
            self.traits_schema["selected_option"] == option
            and (self.time // 20) % 2 == 0
        ):
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
        option_surface.blit(text_surface, (250, 0))
        return data.strip("_")
