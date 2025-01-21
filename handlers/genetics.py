from enum import Enum
import math
import random
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
        self.genome_data = genome_data or {}
        self.neuron_manager = genome_data.get("neuron_manager")

        if self.genome_data:
            for sensor in genome_data["sensors"]:
                self.add_node_gene(node_type=NeuronType.SENSOR, node_id=sensor)
            for actuator in genome_data["actuators"]:
                self.add_node_gene(node_type=NeuronType.ACTUATOR, node_id=actuator)

            for n1, n2 in genome_data["connections"]:
                self.add_connection_gene(n1, n2, np.random.uniform(-1, 1))

    def observe(self, creature):
        observations = []
        for sensor in self.genome_data["sensors"]:
            if sensor in self.neuron_manager.sensors:
                sensor_method = getattr(self.neuron_manager, f"obs_{sensor}")
                observations.append(sensor_method(creature))
            else:
                raise ValueError(f"Unknown sensor: {sensor}")
        return observations

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
        # "TSF": {
        #     "desc": "Time since last food",
        #     "requires": ["last_eaten_time", "current_time", "max_time"],
        # },
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
    
    # class CreatureData(Enum):
    #     RandomNoise = "_random_noise"
    #     NearestFoodInVision = "_nearest_food_in_vision"
    #     AngleNearestFoodInVision = 
    #     LastEatenTime = "_last_eaten_time"
        
        

    def __init__(self, creatures=None, plants=None):
        self.creatures = creatures or []
        self.plants = plants or []

    def update(self, creatures, plants):
        self.creatures = creatures
        self.plants = plants

        self._update_nearest_food()
        self._precompute_trig_values()

    def get_required_context(self, *selected_sensors):
        """
        Returns a set of all required context fields based on selected sensors.
        """
        required_context = set()
        for sensor in selected_sensors:
            if sensor in self.sensors:
                required_context.update(self.sensors[sensor]["requires"])
        return required_context

    def process_sensors(self, context, *sensors):
        """
        Processes a single sensor by extracting required context and computing its value.
        """
        observations = []
        for sensor in sensors:
            if sensor not in self.sensors:
                raise ValueError(f"Unknown sensor: {sensor}")
            else:
                sensor_method = getattr(self, f"obs_{sensor}")
                observations.append(sensor_method(context))
        return observations

    def _update_nearest_food(self):
        """Precompute nearest food for all creatures to avoid redundant calculations."""
        self.nearest_food_map = {
            creature: min(
                self.plants,
                key=lambda plant: (
                    dx := plant.rect.centerx - creature.rect.centerx,
                    dy := plant.rect.centery - creature.rect.centery,
                    dx**2 + dy**2,
                )[-1],
                default=None,
            )
            for creature in self.creatures
        }

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

    def obs_FA(self, creature):
        """Returns the angle to the nearest food source relative to the creature's direction."""
        if (food := self.nearest_food_map.get(creature)) is None:
            return 0.0  # No food, return neutral angle

        dx = food.rect.centerx - creature.rect.centerx
        dy = food.rect.centery - creature.rect.centery
        angle_to_food = math.atan2(dy, dx)
        relative_angle = (angle_to_food - creature.angle) % (2 * math.pi)
        return (relative_angle / math.pi) - 1

    # def obs_TSF(self, creature):
    #     """Returns normalized time since last food intake."""
    #     return min(
    #         (self.current_time - creature.last_eaten_time) / creature.max_time, 1.0
    #     )

    def obs_CD(self, creature):
        """Returns the creature's current facing direction as a normalized value."""
        return (creature.angle / math.pi) - 1

    # --- ACTUATOR FUNCTIONS ---

    def act_Chd(self, creature, context):
        """Sets the creature's direction based on the neural network output."""
        creature.angle = context["direction"] * math.pi

    def act_Mv(self, creature, context):
        """Moves the creature in its current direction at the given speed."""
        creature.rect.x += context["speed"] * math.cos(creature.angle)
        creature.rect.y += context["speed"] * math.sin(creature.angle)
