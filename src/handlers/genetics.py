import math
import random
import uuid
import noise
import numpy as np
import pygame

from src.config import ENV_OFFSET_X, ENV_OFFSET_Y
from src.enums import Attributes, Defence, NeuronType, MatingState
from collections import defaultdict
import src.helper as helper


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
        sensor_nodes = [node for node in self.node_genes if node.type == NeuronType.SENSOR]
        if len(inputs) != len(sensor_nodes):
            raise ValueError(f"Expected {len(sensor_nodes)} inputs, but got {len(inputs)}.")

        for node, value in zip(sensor_nodes, inputs):
            activations[node._id] = value

        # Step 2: Initialize other nodes to zero
        for node in self.node_genes:
            if node.type != NeuronType.SENSOR:
                activations[node._id] = 0

        # Step 3: Initialize bias nodes
        for node in self.node_genes:
            if node.type == NeuronType.BIAS:
                activations[node._id] = 1  # Bias nodes always have activation 1

        # Step 4: Identify tree roots (nodes that are not targeted by any connection)
        child_nodes = {conn.out_node._id for conn in self.connection_genes if conn.enabled}
        root_nodes = {node._id for node in self.node_genes if node._id not in child_nodes}

        # Step 5: Group connections by their respective trees
        tree_connections = defaultdict(list)
        for connection in self.connection_genes:
            if connection.enabled:
                tree_connections[connection.out_node._id].append(connection)

        # Step 6: Process each tree independently
        def propagate_tree(root_id):
            queue = [root_id]
            visited = set()

            while queue:
                node_id = queue.pop(0)
                visited.add(node_id)

                for connection in tree_connections[node_id]:
                    if connection.in_node._id in visited:
                        activations[connection.out_node._id] += (
                            activations[connection.in_node._id] * connection.weight
                        )
                        queue.append(connection.out_node._id)

        for root_id in root_nodes:
            propagate_tree(root_id)

        # Step 7: Apply activation function to non-sensor nodes
        def activation_function(x):
            return x  # Replace with a non-linear activation if needed

        for node in self.node_genes:
            if node.type != NeuronType.SENSOR:
                activations[node._id] = activation_function(activations[node._id])

        # Step 8: Find the best action per tree
        output_nodes = [node for node in self.node_genes if node.type == NeuronType.ACTUATOR]
        tree_best_actions = defaultdict(list)

        for node in output_nodes:
            tree_id = next((root for root in root_nodes if node._id in tree_connections), node._id)
            tree_best_actions[tree_id].append((node, activations[node._id]))

        # Step 9: Return the best actuator(s) from each tree
        result = []
        for tree_id, actions in tree_best_actions.items():
            max_activation = max(actions, key=lambda x: x[1])[1]
            result.extend(node for node, activation in actions if activation == max_activation)

        return result

    def step(self, output_nodes, critter):
        if output_nodes:
            for output_node in output_nodes:
                if output_node.name in self.neuron_manager.actuators:
                    actuator_method = getattr(
                        self.neuron_manager, f"act_{output_node.name}"
                    )
                    actuator_method(critter)
                else:
                    raise ValueError(f"Unknown actuator: {output_node.name}")
        self.fitness = critter.fitness

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

    def crossover(self, other_parent):
        """Performs crossover between this genome and another parent's genome, returning genome data."""

        other_parent_genome = other_parent.genome
        # Determine fitter parent
        if self.fitness > other_parent_genome.fitness:
            fitter, weaker = self, other_parent_genome
        elif self.fitness < other_parent_genome.fitness:
            fitter, weaker = other_parent_genome, self
        else:
            if np.random.rand() < 0.5:
                fitter, weaker = self, other_parent_genome
            else:
                fitter, weaker = other_parent_genome, self

        # Create new genome structure
        child_genome_data = {
            NeuronType.SENSOR: [],
            NeuronType.ACTUATOR: [],
            NeuronType.HIDDEN: [],
            NeuronType.BIAS: [],
            "connections": [],
            "neuron_manager": self.neuron_manager,
        }

        # Inherit node genes (union of both parents' nodes)
        all_nodes = {node._id: node for node in fitter.node_genes}
        for node in weaker.node_genes:
            if node._id not in all_nodes:
                all_nodes[node._id] = node

        # Add node genes to the child genome
        for node in all_nodes.values():
            child_genome_data[node.type].append((node._id, node.name, node.type))

        # Inherit connection genes
        connection_map = {}

        # Collect all connection innovations from both parents
        for conn in fitter.connection_genes:
            connection_map[conn.innovation] = (conn, None)
        for conn in weaker.connection_genes:
            if conn.innovation in connection_map:
                connection_map[conn.innovation] = (
                    connection_map[conn.innovation][0],
                    conn,
                )
            else:
                connection_map[conn.innovation] = (None, conn)

        # Select connections for the child
        for innovation, (fit_conn, weak_conn) in connection_map.items():
            if fit_conn and weak_conn:
                inherited_conn = (
                    fit_conn if np.random.rand() < 0.5 else weak_conn
                )  # Pick randomly
            else:
                inherited_conn = fit_conn or weak_conn  # Take from fitter parent

            # Add to child genome
            if (
                inherited_conn.enabled or np.random.rand() < 0.75
            ):  # 75% chance to inherit disabled genes
                child_genome_data["connections"].append(
                    (
                        (
                            inherited_conn.in_node._id,
                            inherited_conn.in_node.name,
                            inherited_conn.in_node.type,
                            inherited_conn.weight,
                        ),
                        (
                            inherited_conn.out_node._id,
                            inherited_conn.out_node.name,
                            inherited_conn.out_node.type,
                        ),
                    )
                )

        return child_genome_data


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
        "MSa" : {"desc": "Returns whether the send mating signal is accepted or not; -1 (No) => 1 (Yes)"},
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
        "AvS" : {"desc": "Move away from the nearest same-species critter, if found."},
        "AvO" : {"desc": "Move away from the nearest other-species critter, if found."},
        "AvA" : {"desc": "Move away from the nearest any-species critter, if found."},
        "AvF" : {"desc": "Move away from the nearest food source, if found."},
        "AvM" : {"desc": "Move away from the mouse pointer, if found."},
        "SMS" : {"desc": "Send a mating signal to same-species nearby critter, if found."},
        "Mte" : {"desc": "Mate; if mate found"},
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

        self._update_context(
            id=critter.id,
            key="mouse",
            time=critter.time,
            data=mouse_rect,
        )

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

    def obs_MSa(self, critter):
        """Returns whether the send mating signal is accepted or not."""
        other = critter.outgoing_mate_request or critter.mate
        if other is None:
            return -1.0
        elif other.mate.id == critter.id:
            return 1.0
        else:
            return -1.0

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
        if food := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_food"
        ):
            if critter.body_rect.colliderect(food.rect):
                self.plants.remove(food)
                critter.energy += 500
                critter.fitness += 1
            else:
                new_x, new_y = self._get_movement_step(critter, food, pull=True)
                food.rect.x, food.rect.y = new_x, new_y

    def act_MvS(self, critter):
        """Moves towards the nearest same-species critter, if found."""
        if other := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_same_critter"
        ):
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_MvO(self, critter):
        """Moves towards the nearest other-species critter, if found."""
        if other := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_other_critter"
        ):
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_MvA(self, critter):
        """Moves towards the nearest any-species critter, if found."""
        if other := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_any_critter"
        ):
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_MvF(self, critter):
        """Moves towards the nearest food source, if found."""
        if food := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_food"
        ):
            if food.rect.center != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, food)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_MvM(self, critter):
        """Moves towards the mouse pointer, if found."""
        if mouse_rect := self._lookup_context(
            id=critter.id, time=critter.time, key="mouse"
        ):
            if mouse_rect != critter.rect.center:
                new_x, new_y = self._get_movement_step(critter, mouse_rect)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_ADe(self, critter):
        """Activates defense mechanism when triggered, deactivates otherwise."""
        setattr(critter, "defense_active", True)
        if critter.defense_mechanism == "Swordling":
            collision_indices = critter.interaction_rect.collidelistall(
                [other.interaction_rect for other in self.critters]
            )
            if collision_indices:
                for i in collision_indices:
                    other = self.critters[i]
                    if other.id == critter.id:
                        continue
                    elif other.defense_active and other.defense_mechanism in [
                        Defence.SHIELDLING,
                        Defence.CAMOUFLING,
                    ]:
                        continue
                    else:
                        other.energy = 0
                        critter.fitness += 1

    def act_DDe(self, critter):
        """Deactivates defense mechanism when triggered."""
        setattr(critter, "defense_active", False)

    def act_AvS(self, critter):
        """Move away from the nearest same-species critter, if found."""
        if other := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_same_critter"
        ):
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_avoidance_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_AvO(self, critter):
        """Move away from the nearest other-species critter, if found."""
        if other := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_other_critter"
        ):
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_avoidance_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_AvA(self, critter):
        """Move away from the nearest any-species critter, if found."""
        if other := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_any_critter"
        ):
            if other.rect.center != critter.rect.center:
                new_x, new_y = self._get_avoidance_step(critter, other)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_AvF(self, critter):
        """Move away from the nearest food source, if found."""
        if food := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_food"
        ):
            if food.rect.center != critter.rect.center:
                new_x, new_y = self._get_avoidance_step(critter, food)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_AvM(self, critter):
        """Move away from the mouse pointer, if found."""
        if mouse_rect := self._lookup_context(
            id=critter.id, time=critter.time, key="mouse"
        ):
            if mouse_rect != critter.rect.center:
                new_x, new_y = self._get_avoidance_step(critter, mouse_rect)
                critter.rect.x, critter.rect.y = new_x, new_y

    def act_SMS(self, critter):
        """Send a mating signal to a nearby critter, of the same species"""
        if other := self._lookup_context(
            id=critter.id, time=critter.time, key="closest_same_critter"
        ):
            if (
                other.mating_state == MatingState.READY
                and critter.mating_state == MatingState.READY
            ):
                other.incoming_mate_request = critter

    def act_Mte(self, critter):
        """Mate; if mate found"""
        if critter.mating_state == MatingState.MATING:
            critter.crossover()
            critter.mate.remove_mate()
            critter.remove_mate()
            critter.fitness += 1

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

        self._update_context(
            id=critter.id,
            key=context_key,
            time=critter.time,
            data=closest_obj,
        )

        min_distance = helper.distance_between_points(
            critter.rect.center, closest_obj.rect.center
        )

        # Normalize to [-1, 1]
        return (min(min_distance / (critter.rect.width // 2), 1) * 2) - 1

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

        self._update_context(
            id=critter.id,
            key=context_key,
            time=critter.time,
            data=len(filtered_objects),
        )

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

    def _get_avoidance_step(self, mover, target, step_size=1):
        target_rect = target if isinstance(target, pygame.Rect) else target.rect
        dx = mover.rect.centerx - target_rect.centerx
        dy = mover.rect.centery - target_rect.centery

        distance_sq = dx * dx + dy * dy

        if distance_sq < 1:  # If very close, move in a random direction
            angle = random.uniform(0, 2 * math.pi)
            return mover.rect.x + step_size * math.cos(
                angle
            ), mover.rect.y + step_size * math.sin(angle)

        distance = math.sqrt(distance_sq)
        unit_vector = (dx / distance, dy / distance)  # Flip direction to move away

        new_x = mover.rect.x + step_size * unit_vector[0]
        new_y = mover.rect.y + step_size * unit_vector[1]

        return new_x, new_y

    def _update_context(self, id, key, time, data):
        """Helper function to update self.context without overwriting existing data."""
        if id not in self.context:
            self.context[id] = {}
        self.context[id].update({key: {"time": time, "data": data}})

    def _lookup_context(self, id, time, key):
        """lookup and return data from context"""
        instance = self.context.get(id, {}).get(key)
        if instance is not None:
            if instance["time"] == time:
                return instance["data"]
        return None
