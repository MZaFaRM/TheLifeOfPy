from enum import Enum
import math
import random
import uuid
import noise
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
    def __init__(self, node_id, node_name, node_type):
        self._id = node_id
        self.name = node_name
        self.type = node_type

    def __eq__(self, value):
        return self._id == value.node_id and self.type == value.node_type

    def __hash__(self):
        return hash((self._id, self.type))


class Genome:
    def __init__(self, genome_data):
        self.node_genes = set()
        self.connection_genes = []
        self.fitness = 0
        self.adjusted_fitness = 0
        self.species = None
        self.id = uuid.uuid4()
        self.innovation_history = InnovationHistory()
        self.nodes = {}
        self.neuron_manager = genome_data.get("neuron_manager")

        if genome_data:
            for node_id, node_name, node_type in (
                genome_data[NeuronType.SENSOR]
                + genome_data[NeuronType.ACTUATOR]
                + genome_data[NeuronType.HIDDEN]
                + genome_data[NeuronType.BIAS]
            ):
                node = self.add_node_gene(node_id, node_name, node_type)
                self.nodes[node._id] = node

            for node_1, node_2 in genome_data["connections"]:
                self.add_connection_gene(
                    self.nodes[node_1[0]],
                    self.nodes[node_2[0]],
                    np.random.uniform(-1, 1),
                )

    def observe(self, critter):
        observations = []
        for neuron in self.nodes.values():
            if neuron.type == NeuronType.SENSOR:
                if neuron.name in self.neuron_manager.sensors:
                    sensor_method = getattr(self.neuron_manager, f"obs_{neuron.name}")
                    observations.append(sensor_method(critter))
                else:
                    raise ValueError(f"Unknown sensor: {neuron}")
        return observations

    def forward(self, inputs):
        activations = {}

        # Step 1: Initialize sensor nodes with input values
        sensor_nodes = [
            node for node in self.node_genes if node.type == NeuronType.SENSOR
        ]
        if len(inputs) != len(sensor_nodes):
            raise ValueError(
                f"Expected {len(sensor_nodes)} inputs, but got {len(inputs)}."
            )

        for node, value in zip(sensor_nodes, inputs):
            activations[node._id] = value

        # Step 2: Initialize hidden, output, and bias nodes
        for node in self.node_genes:
            if node.type != NeuronType.SENSOR:
                activations[node._id] = 0

        # Step 3: Initialize bias nodes with constant value (typically 1)
        for node in self.node_genes:
            if node.type == NeuronType.BIAS:
                activations[node._id] = 1  # Bias nodes have a fixed activation of 1

        # Step 4: Process connections in a feed-forward manner
        for connection in sorted(
            self.connection_genes, key=lambda c: c.in_node.name
        ):  # Sort for consistency
            if connection.enabled:
                # If either in_node or out_node is bias, process it like other neurons
                activations[connection.out_node._id] += (
                    activations[connection.in_node._id] * connection.weight
                )

        # Step 5: Apply activation function (sigmoid/tanh/ReLU) to hidden & output nodes
        def activation_function(x):
            return np.tanh(x)  # Normalize outputs to [-1, 1]

        for node in self.node_genes:
            if (
                node.type != NeuronType.SENSOR
            ):  # Apply activation only to non-input nodes
                activations[node._id] = activation_function(activations[node._id])

        # Step 6: Return output node activations
        output_nodes = [
            node for node in self.node_genes if node.type == NeuronType.ACTUATOR
        ]
        if output_nodes:
            return max(output_nodes, key=lambda node: activations[node._id])

    def step(self, output_node, critter):
        if output_node:
            if output_node.name in self.neuron_manager.actuators:
                actuator_method = getattr(
                    self.neuron_manager, f"act_{output_node.name}"
                )
                actuator_method(critter)
            else:
                raise ValueError(f"Unknown actuator: {output_node.name}")

    def add_connection_gene(self, in_node, out_node, weight):
        innovation = self.innovation_history.get_innovation(in_node._id, out_node._id)
        connection = ConnectionGene(in_node, out_node, weight, True, innovation)
        self.connection_genes.append(connection)

    def add_node_gene(self, node_id, node_name, node_type):
        node = NodeGene(node_id, node_name, node_type)
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
            if in_node._id != out_node._id:
                self.add_connection_gene(in_node, out_node, np.random.uniform(-1, 1))

        if np.random.rand() < 0.1:
            out_node = np.random.choice(
                [
                    n
                    for n in self.node_genes
                    if n.node_type in {NeuronType.HIDDEN, NeuronType.ACTUATOR}
                ]
            )
            self.add_connection_gene(
                self.bias_node_id, out_node, np.random.uniform(-1, 1)
            )

        # Mutate add node with a probability of 5%
        if np.random.rand() < 0.05:
            connection = np.random.choice(self.connection_genes)
            connection.enabled = False
            new_node = self.add_node_gene(NeuronType.HIDDEN)
            self.add_connection_gene(
                connection,
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


class Phenome:
    def __init__(self, phenome_data):
        self.radius = phenome_data.get("radius", 5)
        self.colors = {
            "alive": phenome_data.get("color", (124, 245, 255)),
            "dead": (0, 0, 0),
            "reproducing": (255, 255, 255),
        }
        self.border = {
            "color": phenome_data.get("color", (100, 57, 255)),
            "thickness": 2.5,
        }


class NeuronManager:
    sensors = {
        "RNs": {
            "desc": "Generates random noise",
        },
        "FD": {
            "desc": "Closeness to nearest food in vision",
        },
    }

    actuators = {
        "Mv": {
            "desc": "Move in current direction",
        },
        "Eat": {
            "desc": "Eat food if in range",
        },
    }

    def __init__(self, critters=None, plants=None):
        self.critters = critters or []
        self.plants = plants or []

    def update(self, critters, plants):
        self.critters = critters
        self.plants = plants

        self._update_nearest_food()
        self._precompute_trig_values()

    def _update_nearest_food(self):
        """Precompute nearest food for all critters to avoid redundant calculations."""
        self.nearest_food_map = {}

        for critter in self.critters:
            min_plant = None
            min_distance_sq = critter.vision["radius"] ** 2

            cx, cy = critter.rect.centerx, critter.rect.centery

            for plant in self.plants:
                dx = plant.rect.centerx - cx
                dy = plant.rect.centery - cy
                distance_sq = dx * dx + dy * dy

                if distance_sq < min_distance_sq:
                    min_distance_sq = distance_sq
                    min_plant = plant

            self.nearest_food_map[critter] = min_plant

    def _precompute_trig_values(self):
        """Precomputes sine and cosine for each critter to avoid redundant calculations."""
        self.trig_cache = {
            critter: (math.cos(critter.angle), math.sin(critter.angle))
            for critter in self.critters
        }

    # --- SENSOR FUNCTIONS ---

    def obs_RNs(self, critter):
        return random.uniform(-1, 1)

    def obs_FD(self, critter):
        """Returns normalized distance to the nearest food source using precomputed data."""
        if (food := self.nearest_food_map.get(critter)) is None:
            return 1.0  # No food found, return max distance

        dx = food.rect.centerx - critter.rect.centerx
        dy = food.rect.centery - critter.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        return min(distance / critter.vision["radius"], 1.0)

    # --- ACTUATOR FUNCTIONS ---

    def act_Mv(self, critter):
        """Moves the critter in its current direction with Perlin noise influence."""
        direction = noise.snoise2(((critter.seed + critter.age) / 1000) % 1000, 0)
        angle = (direction + 1) * math.pi
        critter.rect.x += math.cos(angle)
        critter.rect.y += math.sin(angle)

    def act_Eat(self, critter):
        """Eats the nearest food source if in range."""
        if (food := self.nearest_food_map.get(critter)) is not None:
            if critter.body.colliderect(food.rect):
                self.plants.remove(food)
                critter.energy += 500
                critter.fitness += 1
                self._update_nearest_food()  # Update nearest food for all critters
            else:
                # Move food 1d closer to critter
                dx = food.rect.centerx - critter.rect.centerx
                dy = food.rect.centery - critter.rect.centery
                distance_sq = dx * dx + dy * dy

                if distance_sq > 0:
                    distance = math.sqrt(distance_sq)
                    unit_vector = (dx / distance, dy / distance)

                    step = max(0.1, 1 - (distance / (critter.vision["radius"] * 2)))

                    food.rect.x -= step * unit_vector[0]
                    food.rect.y -= step * unit_vector[1]
