import random
import numpy as np
import pygame
import agents
import neural

# Nearest Food Location (Distance)
# Nearest Food Direction (Angle)
# Nearest Home Location (Distance)
# Nearest Home Direction (Angle)
# Current Energy (Amount)
# Number of Agents Trying to Eat the Nearest Food (Count)
# Nearest Carnivorous Creature Location (Distance)
# Nearest Creature Location (Distance)
# Nearest Creature Direction (Angle)
# Target Food Speed (Speed)
# Distance to Nearest Predator (Distance)
# Distance to Nearest Safe Zone (Distance)
# Food Density (Count)
# Current Speed (Speed)
# Predator Count Nearby (Count)
# Current Energy Usage Rate (Rate)


class CreatureManager:

    def __init__(self, env, screen) -> None:
        self.creature_population = 0
        self.env = env
        self.screen = screen

    def register_creature(self, creature):
        self.creature_population += 1
        return self.generate_dna(creature)

    def get_brain(self, input_size=5, hidden_size=10, output_size=5):
        return neural.OrganismNN(
            input_size,
            hidden_size,
            output_size,
        )

    def get_creature_attributes(self, creature):
        if creature.parent == None:
            sensors = random.choices(list(SensorManager.sensors.keys()), k=5)
        return "".join(sensor for sensor in sensors)

    def generate_creatures(self, radius=5, n=50):
        creatures = pygame.sprite.Group()
        for _ in range(n):
            # food sprite group
            creatures.add(
                agents.Creature(
                    self.env,
                    self.screen,
                    self,
                    radius=radius,
                    n=n,
                )
            )

        return creatures

    def generate_id(self):
        number = self.creature_population
        base = 4  # Since Adenine, Thymine, Guanine, Cytosine
        dna_value = {0: "A", 1: "T", 2: "G", 3: "C"}
        result = []
        while number > 0:
            result.insert(0, number % base)
            number = number // base

        while len(result) < 6:
            # 6 because 6 digit numbers with base 4 can be used
            # to represent at least 4096 creatures
            result.insert(0, 0)

        return "".join(dna_value[digit] for digit in result)

    def get_parsed_dna(self, DNA):
        creature_sensors = [DNA[i : i + 5] for i in range(6, len(DNA), 5)]
        return [SensorManager.sensors[sensor] for sensor in creature_sensors]

    def generate_dna(self, creature):
        creature_id = self.generate_id()
        creature_attributes = self.get_creature_attributes(creature)
        return creature_id + creature_attributes


TOTAL_SENSORS = 17


class SensorManager:
    sensors = {
        "AAAAA": "Nfl",  # Nearest Food Location (Distance)
        "AAAAT": "Nfd",  # Nearest Food Direction (Angle)
        # "AAATA": "Nhl",  # Nearest Home Location (Distance)
        # "AAATT": "Nhd",  # Nearest Home Direction (Angle)
        # "AATAA": "Cey",  # Current Energy (Amount)
        # "AATAT": "Nfc",  # Number of Agents Trying to Eat the Nearest Food (Count)
        # "AATTA": "Nrl",  # Nearest Carnivorous Creature Location (Distance)
        # "AATTT": "Ncl",  # Nearest Creature Location (Distance)
        # "ATAAA": "Ncd",  # Nearest Creature Direction (Angle)
        # "ATAAT": "Tfs",  # Target Food Speed (Speed)
        # "ATATA": "Dnp",  # Distance to Nearest Predator (Distance)
        # "ATATT": "Age",  # Current Age
        # "ATTAA": "Fdy",  # Food Density (Count)
        # "ATTAT": "Csd",  # Current Speed (Speed)
        # "ATTTA": "Pcn",  # Predator Count Nearby (Count)
        # "ATTTT": "Eur",  # Current Energy Usage Rate (Rate)
        # "TAAAA": "Nfs",  # Nearest Food Size
        # "TAAAT": "Nft",  # Nearest Food Type
    }

    @classmethod
    def obs_Nfl(cls, env, creature):
        creature_pos = np.array(creature.rect.center)
        food_positions = np.array([food.position for food in env.foods])

        # Squared distances
        distances = np.sum((food_positions - creature_pos) ** 2, axis=1)

        # If there are no food objects
        if len(distances) == 0:
            # No food, so -1
            return -1

        # Find the distance to the nearest food
        nearest_distance = np.min(distances) ** 0.5
        return nearest_distance if nearest_distance < 100 else -1

    @classmethod
    def obs_Nfd(cls, env, creature):
        creature_pos = np.array(creature.rect.center)
        food_positions = np.array([food.position for food in env.foods])

        # Squared distances
        distances = np.sum((food_positions - creature_pos) ** 2, axis=1)

        # If there are no food objects
        if len(distances) == 0:
            # No food, so -1
            return -1

        # Find the distance to the nearest food
        nearest_food = np.argmin(distances)

        if distances[nearest_food] ** 0.5 > 100:
            return -1

        co_ordinates = food_positions[nearest_food]

        direction = np.arctan2(
            co_ordinates[1] - creature.rect.center[1],
            co_ordinates[0] - creature.rect.center[0],
        )

        return np.degrees(direction) % 360  # Return the angle in degrees

    @classmethod
    def obs_Nhl(cls, env, creature):
        left = 0
        up = 0
        right = env.screen_width - 0
        down = env.screen_height - 0

        x, y = creature.rect.center

        distance_up = y - up
        distance_down = down - y
        distance_left = x - left
        distance_right = right - x

        distances = {
            "up": distance_up,
            "down": distance_down,
            "left": distance_left,
            "right": distance_right,
        }

        closest_edge = min(distances, key=distances.get)

        if closest_edge == "up":
            closest_edge = (x, up)
        elif closest_edge == "down":
            closest_edge = (x, down)
        elif closest_edge == "left":
            closest_edge = (left, y)
        elif closest_edge == "right":
            closest_edge = (right, y)

        return closest_edge

    @classmethod
    def obs_Nhd(cls, env, creature):
        # Similar to obs_Nhl, but return the angle
        left = 0
        up = 0
        right = env.screen_width - 0
        down = env.screen_height - 0

        x, y = creature.rect.center

        distance_up = y - up
        distance_down = down - y
        distance_left = x - left
        distance_right = right - x

        distances = {
            "up": distance_up,
            "down": distance_down,
            "left": distance_left,
            "right": distance_right,
        }

        closest_edge = min(distances, key=distances.get)

        if closest_edge == "up":
            closest_edge = (x, up)
        elif closest_edge == "down":
            closest_edge = (x, down)
        elif closest_edge == "left":
            closest_edge = (left, y)
        elif closest_edge == "right":
            closest_edge = (right, y)

        direction = np.arctan2(
            closest_edge[1] - creature.rect.center[1],
            closest_edge[0] - creature.rect.center[0],
        )
        return np.degrees(direction)

    @classmethod
    def obs_Cey(cls, env, creature):
        return creature.energy  # Return the current energy of the creature

    @classmethod
    def obs_Nfc(cls, env, creature):
        count = sum(
            1 for food in env.foods if food.rect.collidepoint(creature.rect.center)
        )
        return count  # Return the number of agents trying to eat the nearest food

    @classmethod
    def obs_Nrl(cls, env, creature):
        nearest = None
        nearest_distance = float("inf")
        for other in env.creatures:
            if (
                other is not creature and other.is_carnivorous
            ):  # Check if the creature is carnivorous
                distance = np.sum(
                    (np.array(other.rect.center) - np.array(creature.rect.center)) ** 2
                )
                if distance < nearest_distance:
                    nearest = other.rect.center
                    nearest_distance = distance
        return (
            nearest_distance if nearest else float("inf")
        )  # Return distance or infinity if no carnivore found

    @classmethod
    def obs_Ncl(cls, env, creature):
        nearest = None
        nearest_distance = float("inf")
        for other in env.creatures:
            if other is not creature:  # Ignore itself
                distance = np.sum(
                    (np.array(other.rect.center) - np.array(creature.rect.center)) ** 2
                )
                if distance < nearest_distance:
                    nearest = other.rect.center
                    nearest_distance = distance
        return (
            nearest_distance if nearest else float("inf")
        )  # Return distance or infinity if no creature found

    @classmethod
    def obs_Ncd(cls, env, creature):
        nearest = None
        nearest_distance = float("inf")
        for other in env.creatures:
            if other is not creature:  # Ignore itself
                distance = np.sum(
                    (np.array(other.rect.center) - np.array(creature.rect.center)) ** 2
                )
                if distance < nearest_distance:
                    nearest = other.rect.center
                    nearest_distance = distance
        if nearest:
            direction = np.arctan2(
                nearest[1] - creature.rect.center[1],
                nearest[0] - creature.rect.center[0],
            )
            return np.degrees(direction)  # Return the angle in degrees
        return 0  # Default angle if no creature found

    @classmethod
    def obs_Tfs(cls, env, creature):
        # Assuming you have a method to get food's speed (or set it as a constant for simplicity)
        target_food = env.nearest_food(creature.rect.center)
        if target_food:
            return target_food.speed  # Return speed of the nearest food
        return 0  # Default if no food found

    @classmethod
    def obs_Dnp(cls, env, creature):
        nearest_predator = None
        nearest_distance = float("inf")
        for other in env.creatures:
            if (
                other is not creature and other.is_predator
            ):  # Check if the creature is a predator
                distance = np.sum(
                    (np.array(other.rect.center) - np.array(creature.rect.center)) ** 2
                )
                if distance < nearest_distance:
                    nearest = other.rect.center
                    nearest_distance = distance
        return (
            nearest_distance if nearest else float("inf")
        )  # Return distance or infinity if no predator found

    @classmethod
    def obs_Age(cls, creature):
        return creature.age  # Return current age

    @classmethod
    def obs_Fdy(cls, env, creature):
        return len(
            env.foods
        )  # Return food density as the count of food items in the environment

    @classmethod
    def obs_Csd(cls, creature):
        return creature.speed  # Return current speed

    @classmethod
    def obs_Pcn(cls, env, creature):
        return sum(
            1 for other in env.creatures if other.is_predator and other is not creature
        )  # Count predators nearby

    @classmethod
    def obs_Eur(cls, creature):
        return creature.energy_usage_rate  # Return current energy usage rate

    @classmethod
    def obs_Nfs(cls, env, creature):
        # Assuming you have a method to get the size of the nearest food
        nearest_food = env.nearest_food(creature.rect.center)
        return (
            nearest_food.size if nearest_food else 0
        )  # Return size or zero if no food found

    @classmethod
    def obs_Nft(cls, env, creature):
        # Assuming you have a way to determine food type
        nearest_food = env.nearest_food(creature.rect.center)
        return (
            nearest_food.food_type if nearest_food else 0
        )  # Return type or zero if no food found
