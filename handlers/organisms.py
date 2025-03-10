import math
import random
import uuid

import numpy as np
import pygame

import agents
from config import Colors, Fonts
from enums import Attributes


class Forest:
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
        self.plants = []

    def bulk_generate_plants_patch(self, n):
        cluster_points = self.get_random_coords(n)
        for _ in range(n):
            # Use single-layer Perlin noise for simplicity
            for x, y in cluster_points:
                self.plants.append(
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
            self.plants.append(agents.Plant(self.env_surface, pos=(x, y)))

    def get_plants(self):
        return self.plants

    def remove_plant(self, plant):
        self.plants.remove(plant)


class Species:
    def __init__(self, context=None) -> None:
        self.neuron_manager = context["neuron_manager"]
        self.critter_population = 0
        self.surface = context["env_surface"]
        self.critters = []
        self.dead_critters = []

    def create_species(self, n, context):
        context["genome"]["neuron_manager"] = self.neuron_manager
        for _ in range(n):
            self.critters.append(
                agents.Critter(
                    surface=self.surface,
                    context=context,
                )
            )

        return self.critters

    def evaluate_critters(self):
        for critter in self.critters:
            critter.evaluate()

    def step(self, events):
        for critter in self.critters.copy():
            critter.step()
            if not critter.alive:
                self.critters.remove(critter)
                self.dead_critters.append(critter)

    def get_critters(self, alive=True):
        if alive:
            return self.critters
        else:
            return self.dead_critters

    def crossover(self):
        pass


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
