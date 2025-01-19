import math
import random

import numpy as np
import pygame

import agents
from config import Colors, Fonts

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


class PlantManager:
    def __init__(self, context=None) -> None:
        self.env_surface = context["env_surface"]
        self.origins = np.array(
            [
                (
                    random.randrange(0, self.env_surface.get_width()),
                    random.randrange(0, self.env_surface.get_height()),
                )
                for _ in range(5)
            ]
        )
        self.radii = np.array([random.randint(50, 100) for _ in range(5)])
        self.plants = pygame.sprite.Group()

    def bulk_generate_plants_patch(self, n):
        cluster_points = self.get_random_coords(n)
        for _ in range(n):
            # Use single-layer Perlin noise for simplicity
            for x, y in cluster_points:
                self.plants.add(
                    agents.Plant(
                        self.env_surface,
                        pos=(x, y),
                    )
                )

        return self.plants

    def get_random_coords(self, n):
        for _ in range(n):
            origin_x, origin_y = random.choice(self.origins)
            radius = random.choice(self.radii)

            r = radius * math.sqrt(random.random())
            theta = random.uniform(0, 2 * math.pi)

            x = origin_x + int(r * math.cos(theta))
            y = origin_y + int(r * math.sin(theta))

            yield x, y

    def create_plant_patch(self):
        self.radii += 10
        cluster_points = self.get_random_coords(10)
        for x, y in cluster_points:
            self.plants.add(agents.Plant(self.env_surface, pos=(x, y)))

    def get_plants(self):
        return self.plants

    def remove_plant(self, plant):
        self.plants.remove(plant)


class Species:
    base = 4  # Since Adenine, Thymine, Guanine, Cytosine
    dna_value = {
        0: "A",
        1: "T",
        2: "G",
        3: "C",
    }

    situations = ["Food in Vicinity", "Nothing"]
    behaviours = ["Eat Food", "Roam Random"]

    def __init__(self, context=None) -> None:
        self.creature_population = 0
        self.surface = context["env_surface"]
        self.alive_count = 0
        self.dead_count = 0
        self.creatures = pygame.sprite.Group()

    def register_creature(self, creature):
        self.creature_population += 1
        return 1
        return self.generate_dna(creature)

    def generate_creatures(self, n, context):
        for _ in range(n):
            self.creatures.add(
                agents.Creature(
                    surface=self.surface,
                    context=context,
                )
            )

        return self.creatures

    def evaluate_creatures(self):
        for creature in self.creatures:
            creature.evaluate()

    def generate_id(self):
        number = self.creature_population
        result = []
        while number > 0:
            result.insert(0, number % self.base)
            number = number // self.base

        while len(result) < 6:
            # 6 because 6 digit numbers with base 4 can be used
            # to represent at least 4096 creatures
            result.insert(0, 0)

        return "".join(self.dna_value[digit] for digit in result)

    def get_parsed_dna(self, DNA):
        creature_sensors = [DNA[i : i + 5] for i in range(6, len(DNA), 5)]
        return [SensorManager.sensors[sensor] for sensor in creature_sensors]

    def get_creatures(self):
        return self.creatures


class Counter:
    def __init__(self):
        self.surface = pygame.Surface((100, 26), pygame.SRCALPHA)
        self.font = pygame.font.Font(Fonts.PixelifySans, 22)
        self.rect = self.surface.get_rect(topleft=(0, 0))

    def draw(self, value):
        # Render the counter value as text
        self.surface.fill(Colors.primary)

        text = self.font.render("{:,}".format(value), True, Colors.bg_color)
        self.surface.blit(text, self.rect)
