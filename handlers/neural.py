from abc import ABC, abstractmethod
import math
import random
from typing import Any
import uuid
import numpy as np

from enums import NeuronType


class ConnectionGene:
    def __init__(self, in_node, out_node, weight, enabled, innovation):
        self.in_node = in_node
        self.out_node = out_node
        self.weight = weight
        self.enabled = enabled
        self.innovation = innovation


class NodeGene:
    def __init__(self, node_id, node_type):
        self.node_id = node_id
        self.node_type = node_type

    def __eq__(self, value):
        return self.node_id == value.node_id and self.node_type == value.node_type

    def __hash__(self):
        return hash((self.node_id, self.node_type))


class Genome:
    def __init__(self, genome_data):
        self.node_genes = set()
        self.connection_genes = []
        self.fitness = 0
        self.adjusted_fitness = 0
        self.species = None
        self.id = uuid.uuid4()
        self.innovation_history = InnovationHistory()

        if genome_data:
            for sensor in genome_data["sensors"]:
                self.add_node_gene(node_type=NeuronType.SENSOR, node_id=sensor)
            for actuator in genome_data["actuators"]:
                self.add_node_gene(node_type=NeuronType.ACTUATOR, node_id=actuator)

            for n1, n2 in genome_data["connections"]:
                self.add_connection_gene(n1, n2, np.random.uniform(-1, 1))

    def add_connection_gene(self, in_node, out_node, weight):
        innovation = self.innovation_history.get_innovation(in_node, out_node)
        connection = ConnectionGene(in_node, out_node, weight, True, innovation)
        self.connection_genes.append(connection)

    def add_node_gene(self, node_type, node_id=None):
        _id = node_id or len(self.node_genes)
        node = NodeGene(_id, node_type)
        self.node_genes.add(node)
        return node

    def mutate(self):

        # Mutate connection weights with a probability of 80%
        for connection in self.connection_genes:
            if np.random.rand() < 0.8:
                connection.weight += np.random.uniform(-0.1, 0.1)
                connection.weight = np.clip(connection.weight, -1, 1)

        # Mutate add connection with a probability of 10%
        if np.random.rand() < 0.1:
            in_node = np.random.choice(self.node_genes)
            out_node = np.random.choice(self.node_genes)
            if in_node.node_id != out_node.node_id:
                self.add_connection_gene(
                    in_node.node_id, out_node.node_id, np.random.uniform(-1, 1)
                )

        # Mutate add node with a probability of 5%
        if np.random.rand() < 0.05:
            connection = np.random.choice(self.connection_genes)
            connection.enabled = False
            new_node = self.add_node_gene("hidden")
            self.add_connection_gene(
                connection.in_node,
                new_node,
                1,
            )
            self.add_connection_gene(
                len(self.node_genes) - 1,
                connection.out_node,
                connection.weight,
            )

    def crossover(self, parent1, parent2):
        child = Genome()
        child.species = self.species
        child.node_genes = parent1.node_genes.copy()
        child.connection_genes = parent1.connection_genes.copy()

        # Crossover connection genes
        for connection1 in parent1.connection_genes:
            matching = False
            for connection2 in parent2.connection_genes:
                if connection1.innovation == connection2.innovation:
                    matching = True
                    if np.random.rand() < 0.5:
                        child.connection_genes.append(connection2)
                    else:
                        child.connection_genes.append(connection1)
                    break
            if not matching:
                child.connection_genes.append(connection1)

        return child


class InnovationHistory:
    def __init__(self):
        self.innovation = 0
        self.innovation_map = {}

    def get_innovation(self, in_node, out_node):
        connection_key = (in_node, out_node)
        if connection_key in self.innovation_map:
            return self.innovation_map[connection_key]
        else:
            self.innovation += 1
            self.innovation_map[connection_key] = self.innovation
            return self.innovation


class NeuronManager:
    sensors = {
        "RNs": {
            "desc": "Generates random noise",
            "requires": [],
        },
        "FD": {
            "desc": "Distance to nearest food in vision",
            "requires": ["creature_pos", "nearest_food", "vision_radius"],
        },
        "FA": {
            "desc": "Angle to nearest food",
            "requires": ["creature_pos", "creature_angle", "nearest_food"],
        },
        "TSF": {
            "desc": "Time since last food",
            "requires": ["last_eaten_time", "current_time", "max_time"],
        },
        "CD": {
            "desc": "Current direction angle",
            "requires": ["creature_angle"],
        },
    }

    actuators = {
        "Chd": {
            "desc": "Set creature direction",
            "requires": ["new_angle"],
        },
        "Mv": {
            "desc": "Move in current direction",
            "requires": ["speed"],
        },
    }

    @classmethod
    def get_required_context(cls, *selected_sensors):
        """
        Returns a set of all required context fields based on selected sensors.
        """
        required_context = set()
        for sensor in selected_sensors:
            if sensor in cls.sensors:
                required_context.update(cls.sensors[sensor]["requires"])
        return required_context

    @classmethod
    def process_sensors(cls, context, *sensors):
        """
        Processes a single sensor by extracting required context and computing its value.
        """
        observations = []
        for sensor in sensors:
            if sensor not in cls.sensors:
                raise ValueError(f"Unknown sensor: {sensor}")
            else:
                sensor_method = getattr(cls, f"obs_{sensor}")
                observations.append(sensor_method(context))
        return observations

    # --- SENSOR FUNCTIONS ---

    @staticmethod
    def obs_RNs(context):
        return random.uniform(-1, 1)  # Random noise in range [-1, 1]

    @staticmethod
    def obs_FD(context):
        """
        Returns normalized distance to the nearest
        food source (0 = close, 1 = at vision range).
        """
        dx, dy = (
            context["food_pos"][0] - context["creature_pos"][0],
            context["food_pos"][1] - context["creature_pos"][1],
        )
        distance = math.sqrt(dx**2 + dy**2)
        return min(distance / context["vision_radius"], 1.0)  # Normalize to [0, 1]

    @staticmethod
    def obs_FA(context):
        """
        Returns the angle to the nearest
        food source relative to the creature's current direction.
        """
        dx, dy = (
            context["food_pos"][0] - context["creature_pos"][0],
            context["food_pos"][1] - context["creature_pos"][1],
        )
        angle_to_food = math.atan2(dy, dx)
        relative_angle = (angle_to_food - context["creature_angle"]) % (2 * math.pi)
        return (relative_angle / math.pi) - 1  # Normalize to [-1, 1]

    @staticmethod
    def obs_TSF(context):
        """Returns normalized time since last food intake (0 = just ate, 1 = starving)."""
        return min(
            (context["current_time"] - context["last_eaten_time"])
            / context["max_time"],
            1.0,
        )

    @staticmethod
    def obs_CD(context):
        """Returns the creature's current facing direction as a normalized value."""
        return (context["creature_angle"] / math.pi) - 1  # Normalize to [-1, 1]

    # --- ACTUATOR FUNCTIONS ---

    @staticmethod
    def act_Chd(context):
        """Sets the creature's direction based on the neural network output."""
        context["creature"].angle = (
            context["new_direction"] * math.pi
        )  # Convert back from normalized value

    @staticmethod
    def act_Mv(context):
        """Moves the creature in its current direction at the given speed."""
        context["creature"].x += context["speed"] * math.cos(context["creature"].angle)
        context["creature"].y += context["speed"] * math.sin(context["creature"].angle)
