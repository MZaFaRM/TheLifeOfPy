import math
import random
import uuid
import noise
import numpy as np
import pygame

from config import ENV_OFFSET_X, ENV_OFFSET_Y
from enums import Attributes, NeuronType, MatingState
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

        # Step 5: Activation function (sigmoid) for hidden and output nodes
        def activation_function(x):
            return x

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
        "RNs": {"desc": "Generates random noise; Output range [-1 1]"},
        "FDi": {"desc": "Proximity to the nearest visible plant shrubs; -1 (on it) => 1 (farthest)"},
        "ADi": {"desc": "Proximity to nearest visible same-species critter: -1 (on it) => 1 (farthest)"},
        "ODi": {"desc": "Proximity to nearest visible other-species critter: -1 (on it) => 1 (farthest)"},
        "CDi": {"desc": "Proximity to nearest visible any-species critter: -1 (on it) => 1 (farthest)"},
        "MsD": {"desc": "Proximity to mouse pointer, if in visibility: -1 (on it) => 1 (farthest)"},
        "FAm": {"desc": "Density of plant shrubs in proximity: -1 (None) => 1 (More than 10)"},
        "AAm": {"desc": "Density of same-species critters in proximity: -1 (None) => 1 (More than 10)"},
        "OAm": {"desc": "Density of other-species critters in proximity: -1 (None) => 1 (More than 10)"},
        "CAm": {"desc": "Density of any-species critters in proximity: -1 (None) => 1 (More than 10)"},
        "CEn": {"desc": "Current energy level of the critter: -1 (empty) => 1 (full)"},
        "CAg": {"desc": "Current age of the critter: -1 (newborn) => 1 (old)"},
        "CFi": {"desc": "Current fitness of the critter, compared to average: -1 (low) => 1 (high)"},
        "RSt": {"desc": "Reproduction state of the critter: -1 (not ready) => 0 (ready) => 1 (mating)"},
        "CMs": {"desc": "Current movement state of the critter: -1 (idle) => 1 (moving)"},
        "DSt": {"desc": "Defense state of the critter: -1 (not activated) => 1 (activated)"},
    }

    actuators = {
        "Mv": {"desc": "Move in a random direction generated by an snoise function"},
        "Eat": {"desc": "Eat food if food found"},
        "MvS": {"desc": "Move towards the nearest same-species critter, if found."},
        "MvO": {"desc": "Move towards the nearest other-species critter, if found."},
        "MvA": {"desc": "Move towards the nearest any-species critter, if found."},
        "MvF": {"desc": "Move towards the nearest food source, if found"},    
        "MvM": {"desc": "Move towards the mouse pointer, if found"},
        "ADe" : {"desc": "Activates defense mechanism when triggered"},
        "DDe" : {"desc": "Deactivates defense mechanism when triggered"},
        "Mte" : {"desc": "Mate if a critter of same species is found & ready to mate"},
        
        
    }
    # fmt: on

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
        return random.uniform(-1, 1)

    def obs_FDi(self, critter):
        """Returns normalized distance to the nearest food source, scaled to range -1 to 1."""
        return self._get_normalized_nearest_distance(
            critter=critter,
            objects=self.plants,
            context_key="closest_food",
        )

    def obs_ADi(self, critter):
        """Returns normalized distance to the nearest critter of the same species."""
        return self._get_normalized_nearest_distance(
            critter=critter,
            objects=self.critters,
            context_key="closest_same_critter",
            filter_fn=(
                lambda other: other.species == critter.species
                and other.id != critter.id
            ),
        )

    def obs_ODi(self, critter):
        """Returns normalized distance to the nearest critter of a different species."""
        return self._get_normalized_nearest_distance(
            critter=critter,
            objects=self.critters,
            context_key="closest_other_critter",
            filter_fn=(
                lambda other: other.species != critter.species
                and other.id != critter.id
            ),
        )

    def obs_CDi(self, critter):
        """Returns normalized distance to the nearest critter of any species."""
        return self._get_normalized_nearest_distance(
            critter=critter,
            objects=self.critters,
            context_key="closest_any_critter",
            filter_fn=lambda other: other.id != critter.id,
        )

    def obs_MsD(self, critter):
        """Proximity to mouse pointer, if in visibility."""
        x, y = pygame.mouse.get_pos()
        mouse_pos = (x - ENV_OFFSET_X, y - ENV_OFFSET_Y)
        if not critter.rect.collidepoint(mouse_pos):
            return 1.0

        mouse_rect = pygame.Rect(0, 0, 1, 1)
        mouse_rect.center = mouse_pos

        self.context["mouse"] = {
            "time": critter.time,
            "mouse_rect": mouse_rect,
        }

        distance = helper.distance_between_points(critter.rect.center, mouse_rect)
        data = (distance / (critter.vision["radius"] * 2)) * 2 - 1
        return data

    def obs_FAm(self, critter):
        """Returns normalized density of food sources in the critter's vision range."""
        return self._get_normalized_density(
            critter=critter,
            objects=self.plants,
            context_key="food_density",
        )

    def obs_AAm(self, critter):
        """Returns normalized density of same-species critters in the critter's vision range."""
        return self._get_normalized_density(
            critter=critter,
            objects=self.critters,
            context_key="same_critter_density",
            filter_fn=lambda other: other.species == critter.species,
        )

    def obs_OAm(self, critter):
        """Returns normalized density of other-species critters in the critter's vision range."""
        return self._get_normalized_density(
            critter=critter,
            objects=self.critters,
            context_key="other_critter_density",
            filter_fn=lambda other: other.species != critter.species,
        )

    def obs_CAm(self, critter):
        """Returns normalized density of any-species critters in the critter's vision range."""
        return self._get_normalized_density(
            critter=critter,
            objects=self.critters,
            context_key="any_critter_density",
        )

    def obs_CEn(self, critter):
        """Returns normalized energy level of the critter."""
        return (critter.energy / critter.max_energy) * 2 - 1

    def obs_CAg(self, critter):
        """Returns normalized age of the critter."""
        return (critter.age / critter.max_lifespan) * 2 - 1

    def obs_CFi(self, critter):
        """Current fitness of the critter, compared to average."""
        fitness_sum = sum(c.fitness for c in self.critters)
        average_fitness = fitness_sum / len(self.critters)
        if average_fitness == 0:
            return 1.0
        else:
            return (critter.fitness / average_fitness) * 2 - 1

    def obs_RSt(self, critter):
        """Reproduction state of the critter."""
        if critter.mating_state == MatingState.NOT_READY:
            return -1.0
        elif critter.mating_state == MatingState.READY:
            return 0.0
        elif critter.mating_state == MatingState.MATING:
            return 1.0

    def obs_CSp(self, critter):
        """Current movement state of the critter."""
        if critter.previous_position == critter.rect.center:
            return -1.0
        else:
            return 1.0

    def obs_DSt(self, critter):
        """Defense state of the critter."""
        return critter.defense_active

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
        if (
            food_data := self.context.get("closest_food", {}).get(critter.id)
        ) is not None:
            if food_data["time"] != critter.time:
                return

            food = food_data["food"]
            if critter.body_rect.colliderect(food.rect):
                self.plants.remove(food)
                critter.energy += 500
                critter.fitness += 1
            else:
                new_x, new_y = self._get_movement_step(critter, food, pull=True)
                food.rect.x, food.rect.y = new_x, new_y

    def act_MvS(self, critter):
        """Moves towards the nearest same-species critter, if found."""
        if (
            critter_data := self.context.get("closest_same_critter", {}).get(critter.id)
        ) is not None:
            if critter_data["time"] != critter.time:
                return

            other = critter_data["critter"]
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_MvO(self, critter):
        """Moves towards the nearest other-species critter, if found."""
        if (
            critter_data := self.context.get("closest_other_critter", {}).get(
                critter.id
            )
        ) is not None:
            if critter_data["time"] != critter.time:
                return

            other = critter_data["critter"]
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_MvA(self, critter):
        """Moves towards the nearest any-species critter, if found."""
        if (
            critter_data := self.context.get("closest_any_critter", {}).get(critter.id)
        ) is not None:
            if critter_data["time"] != critter.time:
                return

            other = critter_data["critter"]
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_MvF(self, critter):
        """Moves towards the nearest food source, if found."""
        if (
            food_data := self.context.get("closest_food", {}).get(critter.id)
        ) is not None:
            if food_data["time"] != critter.time:
                return

            food = food_data["food"]
            if food.rect.center != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, food)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_MvM(self, critter):
        """Moves towards the mouse pointer, if found."""
        if (mouse_data := self.context.get("mouse", {})) is not None:
            if mouse_data["time"] != critter.time:
                return

            mouse_rect = mouse_data["mouse_rect"]
            if mouse_rect != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, mouse_rect)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_ADe(self, critter):
        """Activates defense mechanism when triggered, deactivates otherwise."""
        setattr(critter, "defense_active", True)
        if critter.defense_mechanism == "Swordling":
            collision_indices = critter.defense_rect.collidelistall(
                [other.rect for other in self.critters]
            )
            if collision_indices:
                for i in collision_indices:
                    other = self.critters[i]
                    if other.id == critter.id:
                        continue
                    elif other.defense_active and other.defense_mechanism in [
                        "Shieldling",
                        "Camouflaging",
                    ]:
                        continue
                    else:
                        other.die()

    def act_DDe(self, critter):
        """Deactivates defense mechanism when triggered."""
        setattr(critter, "defense_active", False)

    # --- HELPER FUNCTIONS ---
    def _get_normalized_nearest_distance(
        self, critter, objects, context_key, filter_fn=None
    ):
        """Returns normalized distance to the nearest object in 'objects', scaled to [-1, 1].
        Optionally filters objects using 'filter_fn'.
        """
        colliding_indices = critter.rect.collidelistall([obj.rect for obj in objects])

        if not colliding_indices or (
            len(colliding_indices) == 1
            and getattr(objects[colliding_indices[0]], "id", None) == critter.id
        ):
            return 1.0

        filtered_objects = [
            objects[i]
            for i in colliding_indices
            if not filter_fn or filter_fn(objects[i])
        ]

        if not filtered_objects:
            return 1.0

        closest_obj = min(
            filtered_objects,
            key=lambda obj: helper.distance_between_points(
                critter.rect.center, obj.rect.center
            ),
        )

        self.context[context_key] = {
            critter.id: {
                "time": critter.time,
                context_key.split("_")[-1]: closest_obj,
            }
        }

        min_distance = helper.distance_between_points(
            critter.rect.center, closest_obj.rect.center
        )

        # Normalize to [-1, 1]
        data = (min(min_distance / (critter.rect.width // 2), 1) * 2) - 1
        if data < 0:
            pass
        return data

    def _get_normalized_density(self, critter, objects, context_key, filter_fn=None):
        """Returns normalized density of objects in 'objects' within critter's vision range."""
        colliding_indices = critter.rect.collidelistall([obj.rect for obj in objects])

        if not colliding_indices:
            return -1.0

        filtered_objects = [
            objects[i]
            for i in colliding_indices
            if not filter_fn or filter_fn(objects[i])
        ]

        if not filtered_objects:
            return -1.0

        self.context[context_key] = {
            critter.id: {
                "time": critter.time,
                context_key.split("_")[-1]: len(filtered_objects),
            }
        }

        # Normalize to [-1, 1]
        return (min(len(filtered_objects) / 10, 1) * 2) - 1

    def _get_movement_step(self, mover, target, step_size=1, pull=False):
        target_rect = target if isinstance(target, pygame.Rect) else target.rect
        dx = target_rect.centerx - mover.rect.centerx
        dy = target_rect.centery - mover.rect.centery

        distance_sq = dx * dx + dy * dy

        if distance_sq < 1:  # If very close, don't move
            return mover.rect.x, mover.rect.y

        distance = math.sqrt(distance_sq)
        unit_vector = (dx / distance, dy / distance)

        step = max(0.2, 1 - (distance / (mover.rect.width))) if pull else step_size

        new_x = (
            target_rect.x - step * unit_vector[0]
            if pull
            else mover.rect.x + step * unit_vector[0]
        )
        new_y = (
            target_rect.y - step * unit_vector[1]
            if pull
            else mover.rect.y + step * unit_vector[1]
        )

        return new_x, new_y
