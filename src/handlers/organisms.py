from calendar import c
import math
import random
from re import A
import uuid

import numpy as np
import pygame

from src import helper
import src.agents as agents
from src.config import Colors, Fonts
from src.enums import Attributes, MatingState, SurfDesc


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

    def get_plant_count(self):
        return len(self.plants)

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
                    context=context.copy(),
                )
            )

        return self.critters

    def evaluate_critters(self):
        for critter in self.critters:
            critter.evaluate()

    def step(self, events):
        response = None
        for critter in self.critters.copy():
            response = critter.step(events) or response
            if not critter.alive:
                self.critters.remove(critter)
                self.dead_critters.append(critter)

            if critter.FETUS:
                self.critters.append(
                    agents.Critter(
                        surface=self.surface,
                        context=critter.FETUS.copy(),
                    )
                )
                critter.FETUS = None
        return response

    def get_critters(self, alive=True):
        if alive:
            return self.critters
        else:
            return self.dead_critters

    def get_critter_info(self, critter_id, all=True):
        critter = next((c for c in self.critters if c.id == critter_id), None)
        if critter:
            if all:
                return {
                    Attributes.ID: critter.id,
                    Attributes.SPECIES: critter.species,
                    Attributes.AGE: f"{critter.age:,}",
                    SurfDesc.SURFACE: critter.image,
                    Attributes.POPULATION: f"{self.get_species_count(critter.species):,}",
                    Attributes.ENERGY: f"{critter.energy:,}",
                    Attributes.POSITION: f"{critter.rect.center}",
                    Attributes.FITNESS: f"{critter.fitness:,}",
                    Attributes.DOMAIN: critter.domain.value,
                    Attributes.MATING_STATE: critter.mating_state.value,
                    Attributes.CHILDREN: f"{critter.children:,}",
                    Attributes.AGE_OF_MATURITY: f"{critter.age_of_maturity:,}",
                    Attributes.DEFENSE_MECHANISM: critter.defense_mechanism.value,
                    Attributes.VISION_RADIUS: f"{critter.vision["radius"]:,}",
                    Attributes.SIZE: f"{critter.size:,}",
                    Attributes.COLOR: helper.rgb_to_hex(critter.color),
                    Attributes.MAX_SPEED: f"{critter.max_speed:,}",
                    Attributes.MAX_ENERGY: f"{critter.max_energy:,}",
                    Attributes.MAX_LIFESPAN: f"{critter.max_lifespan:,}",
                }
            else:
                return {
                    Attributes.ID: critter.id,
                    Attributes.SPECIES: critter.species,
                    Attributes.POPULATION: f"{self.get_species_count(critter.species):,}",
                    Attributes.MATING_STATE: critter.mating_state.value,
                    Attributes.CHILDREN: f"{critter.children:,}",
                    Attributes.AGE: f"{critter.age:,}",
                    Attributes.ENERGY: f"{critter.energy:,}",
                    Attributes.POSITION: f"{critter.rect.center}",
                    Attributes.FITNESS: f"{critter.fitness:,}",
                }
        return None     

    def get_species_count(self, species):
        return sum(1 for s in self.critters if s.species == species)

    def get_critter_count(self):
        count = {"total": 0}
        fitness = {"total": 0}
        species_colors = {}  # Maps species → color

        for i in self.critters:
            # Species name and color
            species_name = i.species  # Get species name
            species_colors[species_name] = i.color  # Store species color

            # Population count
            count["total"] += 1
            count[species_name] = count.get(species_name, 0) + 1

            # fitness count
            fitness["total"] += i.fitness
            fitness[species_name] = fitness.get(species_name, 0) + i.fitness

        return count, fitness, species_colors


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
