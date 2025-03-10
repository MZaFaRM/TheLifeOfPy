import math
import random
import uuid
import noise
import numpy as np

from enums import Attributes, NeuronType
import helper


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
                    self.nodes[node_1[0]], self.nodes[node_2[0]], node_1[3]
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

        # crossover connection genes
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
            "alive": phenome_data.get(Attributes.COLOR, (124, 245, 255)),
            "dead": (0, 0, 0),
            "reproducing": (255, 255, 255),
        }
        self.border = {
            Attributes.COLOR: phenome_data.get(Attributes.COLOR, (100, 57, 255)),
            "thickness": 2.5,
        }


class NeuronManager:
    # fmt: off
    sensors = {
        "RNs": {"desc": "Generates random noise; Output range [0 1]"},
        "FDi": {"desc": "Proximity to the nearest visible plant shrubs; 0 (on it) => 1 (farthest)"},
        "ADi": {"desc": "Proximity to nearest visible same-species critter: 0 (on it) => 1 (farthest)"},
        "ODi": {"desc": "Proximity to nearest visible other-species critter: 0 (on it) => 1 (farthest)"},
        "FAm": {"desc": "Density of plant shrubs in proximity: 0 (None) => 1 (More than 10)"},
        "AAm": {"desc": "Density of same-species critters in proximity: 0 (None) => 1 (More than 10)"},
        "OAm": {"desc": "Density of other-species critters in proximity: 0 (None) => 1 (More than 10)"},
        "CEn": {"desc": "Current energy level of the critter: 0 (empty) => 1 (full)"},
        "CAg": {"desc": "Current age of the critter: 0 (newborn) => 1 (old)"},
        "CFi": {"desc": "Current fitness of the critter: 0 (low) => 1 (high)"},
        "RSt": {"desc": "Reproduction state of the critter: 0 (not ready) => 0.5 (ready) => 1 (mating)"},
        "CSp": {"desc": "Current speed of the critter: 0 (stopped) => 1 (full speed)"},
        "DSt": {"desc": "Defense state of the critter: 0 (not activated) => 1 (activated)"},
    }
    # fmt: on

    actuators = {
        "Mv": {
            "desc": "Move in a random direction generated by an snoise function",
        },
        "Eat": {
            "desc": "Eat food if in range",
        },
    }

    def __init__(self, critters=None, plants=None):
        self.critters = critters or []
        self.plants = plants or []
        self.context = {}

    def update(self, critters, plants):
        self.critters = critters
        self.plants = plants

        self.critters_rect = [critter.rect for critter in self.critters]
        self.plants_rect = [plant.rect for plant in self.plants]

    # --- SENSOR FUNCTIONS ---

    def obs_RNs(self, critter):
        return random.uniform(0, 1)

    def obs_FDi(self, critter):
        """Returns normalized distance to the nearest food source, scaled to range 0 to 1."""
        colliding_food_indices = critter.body_rect.collidelistall(self.plants_rect)
        if not colliding_food_indices:
            return 1.0
        else:
            closest_food = min(
                self.plants,
                key=lambda plant: helper.distance_between_points(
                    critter.rect.center, plant.rect.center
                ),
            )
            self.context["closest_food"][critter.id] = closest_food
            min_distance = helper.distance_between_points(
                critter.rect.center, closest_food.rect.center
            )

            # Normalize to [0, 1]
            return min(min_distance / critter.vision["radius"], 1)

    def obs_ADi(self, critter):
        """Returns normalized distance to the nearest critter of the same species."""

    # --- ACTUATOR FUNCTIONS ---

    def act_Mv(self, critter):
        """Moves the critter in a random direction generated by an snoise function."""
        target_direction = noise.snoise2(
            ((critter.seed + critter.age) / 1000) % 1000, 0
        )
        target_angle = (target_direction + 1) * math.pi

        # Gradually change the angle instead of jumping
        critter.angle += (target_angle - critter.angle) * 0.1  # Smooth transition

        critter.rect.x += math.cos(critter.angle)
        critter.rect.y += math.sin(critter.angle)

    def act_Eat(self, critter):
        """Eats the nearest food source if in range."""
        if (food := self.context["closest_food"].get(critter.id)) is not None:
            if critter.body_rect.colliderect(food.rect):
                self.plants.remove(food)
                critter.energy = (critter.energy + 500) % critter.max_energy
                critter.fitness += 1
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
