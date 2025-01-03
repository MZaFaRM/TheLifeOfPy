from abc import ABC, abstractmethod
from typing import Any
import numpy as np


# Base Sensor Class
class Sensor(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def observation(self) -> Any:
        pass


# Base Actuator Class
class Actuator(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def execute(self, command: Any) -> None:
        pass


class SensorManager:
    sensors = {
        "AAAAA": "Nil",  # None Sensor
        # "AAAAA": "Nfl",  # Food in Vicinity (Distance)
        # "AAAAT": "Nfd",  # Nearest Food Direction (Angle)
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

    def obs_Nil(self, env, creature):
        return None

    def obs_Nfd(self, env, creature):
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

    def obs_Nhl(self, env, creature):
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

    def obs_Nhd(self, env, creature):
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

    def obs_Cey(self, env, creature):
        return creature.energy  # Return the current energy of the creature

    def obs_Nfc(self, env, creature):
        count = sum(
            1 for food in env.foods if food.rect.collidepoint(creature.rect.center)
        )
        return count  # Return the number of agents trying to eat the nearest food

    def obs_Nrl(self, env, creature):
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

    def obs_Ncl(self, env, creature):
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

    def obs_Ncd(self, env, creature):
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

    def obs_Tfs(self, env, creature):
        # Assuming you have a method to get food's speed (or set it as a constant for simplicity)
        target_food = env.nearest_food(creature.rect.center)
        if target_food:
            return target_food.speed  # Return speed of the nearest food
        return 0  # Default if no food found

    def obs_Dnp(self, env, creature):
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

    def obs_Age(self, creature):
        return creature.age  # Return current age

    def obs_Fdy(self, env, creature):
        return len(
            env.foods
        )  # Return food density as the count of food items in the environment

    def obs_Csd(self, creature):
        return creature.speed  # Return current speed

    def obs_Pcn(self, env, creature):
        return sum(
            1 for other in env.creatures if other.is_predator and other is not creature
        )  # Count predators nearby

    def obs_Eur(self, creature):
        return creature.energy_usage_rate  # Return current energy usage rate

    def obs_Nfs(self, env, creature):
        # Assuming you have a method to get the size of the nearest food
        nearest_food = env.nearest_food(creature.rect.center)
        return (
            nearest_food.size if nearest_food else 0
        )  # Return size or zero if no food found

    def obs_Nft(self, env, creature):
        # Assuming you have a way to determine food type
        nearest_food = env.nearest_food(creature.rect.center)
        return (
            nearest_food.food_type if nearest_food else 0
        )  # Return type or zero if no food found
