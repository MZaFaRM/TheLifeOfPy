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
    def __init__(self, node_name, node_type):
        self.node_id = uuid.uuid4()
        self.node_name = node_name
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
        self.genome_data = genome_data or {}
        self.neuron_manager = genome_data.get("neuron_manager")

        if self.genome_data:
            sensors = {}
            actuators = {}

            for sensor_name in genome_data["sensors"]:
                node = self.add_node_gene(
                    node_type=NeuronType.SENSOR, node_name=sensor_name
                )
                sensors[sensor_name] = node
            for actuator_name in genome_data["actuators"]:
                node = self.add_node_gene(
                    node_type=NeuronType.ACTUATOR, node_name=actuator_name
                )
                actuators[actuator_name] = node

            for sensor_name, actuator_name in genome_data["connections"]:
                self.add_connection_gene(
                    sensors[sensor_name],
                    actuators[actuator_name],
                    np.random.uniform(-1, 1),
                )

    def observe(self, creature):
        observations = []
        for sensor_name in self.genome_data["sensors"]:
            if sensor_name in self.neuron_manager.sensors:
                sensor_method = getattr(self.neuron_manager, f"obs_{sensor_name}")
                observations.append(sensor_method(creature))
            else:
                raise ValueError(f"Unknown sensor: {sensor_name}")
        return observations

    def forward(self, inputs):
        activations = {}

        # Step 1: Initialize sensor nodes with input values
        sensor_nodes = [
            node for node in self.node_genes if node.node_type == NeuronType.SENSOR
        ]
        if len(inputs) != len(sensor_nodes):
            raise ValueError(
                f"Expected {len(sensor_nodes)} inputs, but got {len(inputs)}."
            )

        for node, value in zip(sensor_nodes, inputs):
            activations[node.node_id] = value

        # Step 2: Initialize hidden & output nodes to 0
        for node in self.node_genes:
            if node.node_type != NeuronType.SENSOR:
                activations[node.node_id] = 0

        # Step 3: Process connections in a feed-forward manner
        for connection in sorted(
            self.connection_genes, key=lambda c: c.in_node.node_name
        ):  # Sort for consistency
            if connection.enabled:
                activations[connection.out_node.node_id] += (
                    activations[connection.in_node.node_id] * connection.weight
                )

        # Step 4: Apply activation function (sigmoid/tanh/ReLU) to hidden & output nodes
        def activation_function(x):
            return np.tanh(x)  # Normalize outputs to [-1, 1]

        for node in self.node_genes:
            if (
                node.node_type != NeuronType.SENSOR
            ):  # Apply activation only to non-input nodes
                activations[node.node_id] = activation_function(
                    activations[node.node_id]
                )

        # Step 5: Return output node activations
        output_nodes = [
            node for node in self.node_genes if node.node_type == NeuronType.ACTUATOR
        ]

        return max(output_nodes, key=lambda node: activations[node.node_id]).node_name

    def step(self, actuator_name, creature):
        if actuator_method := getattr(
            self.neuron_manager, f"act_{actuator_name}", None
        ):
            actuator_method(creature)
        else:
            raise ValueError(f"Unknown actuator: {actuator_name}")

    def add_connection_gene(self, in_node, out_node, weight):
        innovation = self.innovation_history.get_innovation(
            in_node.node_id, out_node.node_id
        )
        connection = ConnectionGene(in_node, out_node, weight, True, innovation)
        self.connection_genes.append(connection)

    def add_node_gene(self, node_type, node_name=None):
        _id = node_name or len(self.node_genes)
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
            new_node = self.add_node_gene("hidden")
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
        # "TSF": {
        #     "desc": "Time since last food",
        # },
    }

    actuators = {
        "Mv": {
            "desc": "Move in current direction",
        },
        "Eat": {
            "desc": "Eat food if in range",
        },
    }

    def __init__(self, creatures=None, plants=None):
        self.creatures = creatures or []
        self.plants = plants or []

    def update(self, creatures, plants):
        self.creatures = creatures
        self.plants = plants

        self._update_nearest_food()
        self._precompute_trig_values()

    def _update_nearest_food(self):
        """Precompute nearest food for all creatures to avoid redundant calculations."""
        self.nearest_food_map = {}

        for creature in self.creatures:
            min_plant = None
            min_distance_sq = creature.vision["radius"] ** 2

            cx, cy = creature.rect.centerx, creature.rect.centery

            for plant in self.plants:
                dx = plant.rect.centerx - cx
                dy = plant.rect.centery - cy
                distance_sq = dx * dx + dy * dy

                if distance_sq < min_distance_sq:
                    min_distance_sq = distance_sq
                    min_plant = plant

            self.nearest_food_map[creature] = min_plant

    def _precompute_trig_values(self):
        """Precomputes sine and cosine for each creature to avoid redundant calculations."""
        self.trig_cache = {
            creature: (math.cos(creature.angle), math.sin(creature.angle))
            for creature in self.creatures
        }

    # --- SENSOR FUNCTIONS ---

    def obs_RNs(self, creature):
        return random.uniform(-1, 1)

    def obs_FD(self, creature):
        """Returns normalized distance to the nearest food source using precomputed data."""
        if (food := self.nearest_food_map.get(creature)) is None:
            return 1.0  # No food found, return max distance

        dx = food.rect.centerx - creature.rect.centerx
        dy = food.rect.centery - creature.rect.centery
        distance = math.sqrt(dx**2 + dy**2)
        return min(distance / creature.vision["radius"], 1.0)

    # def obs_TSF(self, creature):
    #     """Returns normalized time since last food intake."""
    #     return min(
    #         (self.current_time - creature.last_eaten_time) / creature.max_time, 1.0
    #     )

    # --- ACTUATOR FUNCTIONS ---

    def act_Mv(self, creature):
        """Moves the creature in its current direction with Perlin noise influence."""
        direction = noise.snoise2(((creature.seed + creature.age) / 1000) % 1000, 0)
        angle = (direction + 1) * math.pi
        creature.rect.x += math.cos(angle)
        creature.rect.y += math.sin(angle)

    def act_Eat(self, creature):
        """Eats the nearest food source if in range."""
        if (food := self.nearest_food_map.get(creature)) is not None:
            if creature.rect.center == food.rect.center:
                self.plants.remove(food)
                creature.energy += 500
                creature.fitness += 1
                self._update_nearest_food()  # Update nearest food for all creatures
            else:
                # Move food 1d closer to creature
                dx = food.rect.centerx - creature.rect.centerx
                dy = food.rect.centery - creature.rect.centery
                distance_sq = dx * dx + dy * dy

                if distance_sq > 0:
                    distance = math.sqrt(distance_sq)
                    unit_vector = (dx / distance, dy / distance)

                    step = max(0.1, 1 - (distance / (creature.vision["radius"] * 2)))

                    food.rect.x -= step * unit_vector[0]
                    food.rect.y -= step * unit_vector[1]
