import random

import noise
import numpy as np
import pygame
from noise import pnoise1, pnoise2, snoise2

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
        self.scale = 1000
        self.dx = random.uniform(0, 100)
        self.dy = random.uniform(0, 100)
        self.dz = random.uniform(0, 100)
        self.perlin_frequency = 0.02
        self.plants = pygame.sprite.Group()

    def bulk_generate_plants_patch(self, n=100):
        for _ in range(n):
            # Use single-layer Perlin noise for simplicity
            cluster_points = self.get_coords_from_noise()
            for x, y in cluster_points:
                self.plants.add(
                    agents.Plant(
                        self.env_surface,
                        pos=(x, y),
                    )
                )

        return self.plants

    def get_coords_from_noise(self):
        # Increment dx and dy for smooth noise
        self.dx += self.perlin_frequency
        self.dy += self.perlin_frequency

        x_noise = snoise2(self.dx, self.dy)
        y_noise = snoise2(self.dx + 100, self.dy + 100)

        # Scale and normalize noise values to environment dimensions
        center_x = int(((x_noise + 1) / 2) * (self.env_surface.get_width() - 75))
        center_y = int(((y_noise + 1) / 2) * (self.env_surface.get_height() - 75))

        cluster_points = []
        cluster_radius = 50
        for _ in range(5):
            offset_x = random.uniform(-cluster_radius, cluster_radius)
            offset_y = random.uniform(-cluster_radius, cluster_radius)
            cluster_x = max(
                0,
                min(
                    self.env_surface.get_width() - 75,
                    center_x + offset_x,
                ),
            )
            cluster_y = max(
                0,
                min(
                    self.env_surface.get_height() - 75,
                    center_y + offset_y,
                ),
            )
            cluster_points.append((int(cluster_x), int(cluster_y)))

        return cluster_points

    def create_plant_patch(self):
        cluster_points = self.get_coords_from_noise()
        for x, y in cluster_points:
            self.plants.add(agents.Plant(self.env_surface, pos=(x, y)))

    def get_plants(self):
        return self.plants

    def remove_plant(self, plant):
        self.plants.remove(plant)


class CreatureManager:
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

    def generate_creatures(self, n=50, *args, **kwargs):
        for _ in range(n):
            self.creatures.add(
                agents.Creature(
                    surface=self.surface,
                    sensors=None,
                    *args,
                    **kwargs,
                )
            )

        return self.creatures

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
