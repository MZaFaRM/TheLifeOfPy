import random
from enum import Enum
from uuid import uuid4

import noise
import numpy as np
import pygame
from pygame.sprite import Sprite

import helper
from enums import Attributes, Base, Shapes, SurfDesc
from handlers.genetics import Genome


class MatingState(Enum):
    NOT_READY = 0
    READY = 1
    MATING = 2


class Critter(Sprite):
    def __init__(self, surface, context):
        self.id = uuid4()
        super().__init__()

        position = context.get("position", None)
        parents = context.get("parents", None)
        initial_energy = context.get("initial_energy", None)

        color = context.get(Attributes.COLOR, (124, 245, 255))
        # self.phenome = Phenome(context.get("phenome"))
        self.species = context.get("species", None)
        self.color = color
        self.size = context.get(Attributes.SIZE, 5)
        self.mating_timeout = random.randint(150, 300)
        self.genome = Genome(context.get("genome"))
        self.max_energy = context.get(Attributes.MAX_ENERGY, 1000)
        self.speed = context.get(Attributes.SPEED, 1)
        self.fitness = 0
        self.seed = random.randint(0, 1000000)
        self.domain = context.get(Attributes.DOMAIN, "circle")

        self.colors = {
            "alive": color,
            "dead": (0, 0, 0),
            "reproducing": (255, 255, 255),
        }

        self.border = {
            Attributes.COLOR: (100, 57, 255),
            "thickness": 2.5,
        }

        self.vision = {
            "radius": context.get(Attributes.VISION_RADIUS, 40),
            Attributes.COLOR: {
                Base.found: (0, 255, 0, 25),
                Base.looking: (0, 255, 255, 25),
            },
            "food": {"state": Base.looking, SurfDesc.RECT: None},
            "mate": {"state": Base.looking, "mate": None},
        }

        self.angle = 0  # degrees
        self.rotation = 0  # degrees
        self.hunger = 2
        self.alive = True
        self.time = 0
        self.age = 0
        self.max_lifespan = context.get(Attributes.MAX_LIFESPAN, 1000)
        self.acceleration_factor = 0.1
        self.td = random.randint(0, 1000)  # for pnoise generation
        self.energy = initial_energy if initial_energy else self.max_energy

        self.mating_state = MatingState.NOT_READY

        self.env_surface = surface
        self.noise = noise

        self.parents = parents

        self.done = False

        surface_size = (
            self.size + self.border["thickness"] + (2 * self.vision["radius"])
        )
        self.image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

        # Calculate center of the surface
        self.center = (surface_size // 2, surface_size // 2)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = position or helper.get_random_position(surface)
        self.clickable_body = self.rect.inflate(
            -2 * self.vision["radius"] - 10,
            -2 * self.vision["radius"] - 10,
        )
        self.body_rect = self.rect.inflate(
            -2 * self.vision["radius"] + 10,
            -2 * self.vision["radius"] + 10,
        )

    def draw(self, surface):
        if not self.alive:
            return

        if self.time > 1:
            return surface.blit(self.image, self.rect)

        color = self.color

        rect = pygame.Rect(0, 0, self.size, self.size)
        rect.center = self.center

        # Critter
        if self.domain == Shapes.CIRCLE:
            pygame.draw.circle(self.image, color, self.center, self.size // 2)
        elif self.domain == Shapes.SQUARE:
            pygame.draw.rect(self.image, color, rect)
        elif self.domain == Shapes.TRIANGLE:
            pygame.draw.polygon(self.image, color, helper.get_triangle_points(rect))
        elif self.domain == Shapes.PENTAGON:
            pygame.draw.polygon(self.image, color, helper.get_pentagon_points(rect))

        # if defense == "Swordling":
        #     pygame.draw.circle(
        #         surface, (217, 217, 217, int(0.5 * 255)), rect.center, 75
        #     )
        # elif defense == "Shieldling":
        #     border_rect = pygame.Rect(0, 0, 75, 75)
        #     border_rect.center = (surface.get_width() // 2, surface.get_height() // 2)
        #     pygame.draw.rect(surface, (255, 255, 255), border_rect, 5)
        # elif defense == "Camoufling":
        #     color = (color[0], color[1], color[2], int(0.5 * 255))

        surface.blit(self.image, self.rect)

    def step(self):
        self.time += 1
        self.age += 1

        if not self.done:
            self.energy -= 1

            # if (self.age / self.expected_lifespan) > 0.25:
            #     self.mating_state = MatingState.READY

            if self.energy <= 0 or self.age >= self.max_lifespan:
                self.die()
                return

            obs = self.genome.observe(self)
            output = self.genome.forward(obs)
            self.genome.step(output, self)

            self.update_rect()

            return
            self.age += 1
            self.mating["timeout"] -= 1

            if self.mating["timeout"] <= 0:
                if (self.energy >= 50) and (self.mating["state"] != Base.mating):
                    self.mating["state"] = Base.ready
                    # if random.random() < 0.6:
                    #     pass

            self.update_vision_state()
            self.angle = self.update_angle()

        if not self.alive:
            if (self.time - self.age) < 100:
                return

    def update_rect(self):
        self.rect.centerx %= self.env_surface.get_width()
        self.rect.centery %= self.env_surface.get_height()

        self.body_rect.center = self.rect.center
        self.clickable_body.center = self.rect.center

    def set_mate(self, mate):
        self.mating["state"] = Base.mating
        self.mating["mate"] = mate

    def remove_mate(self):
        self.mating["state"] = Base.not_ready
        self.mating["mate"] = None
        self.mating["timeout"] = self.mating_timeout

    def update_vision_state(self):
        if rect := self.rect.collideobjects(
            [food.rect for food in self.env.plant_manager.get_plants()],
            key=lambda rect: rect,
        ):
            self.vision["food"]["state"] = Base.found
            self.vision["food"][SurfDesc.RECT] = rect
        else:
            self.vision["food"]["state"] = Base.looking
            self.vision["food"][SurfDesc.RECT] = None

        other_critters = [
            critter
            for critter in self.env.critters
            if critter is not self
            and critter.mating["state"] == Base.ready
            and critter.alive
        ]

        if critter_index := self.rect.collidelistall(
            [critter.rect for critter in other_critters]
        ):
            self.vision["mate"]["state"] = Base.found
            self.vision["mate"]["mate"] = other_critters[critter_index[0]]

        else:
            self.vision["mate"]["state"] = Base.looking
            self.vision["mate"]["mate"] = None
        return

    def update_angle(self):
        angle = noise.snoise2(self.td, 0) * 360
        self.td += 0.01
        return angle

    def reset(self):
        self.hunger = 2
        self.done = False
        self.energy = self.max_energy
        self.closest_edge = None
        self.original_position = helper.get_random_position(self.env_window)
        self.rect.center = self.original_position

    def progress(self):
        if not self.done:
            if self.hunger == 0:
                self.reproduce()
            elif self.hunger == 1:
                pass
            else:
                self.die()
            self.done = True

    def reproduce(self):
        self.env.children.add(
            Critter(
                self.env,
                self.env_window,
                self.critter_manager,
            )
        )

    def die(self):
        self.alive = False
        self.done = True

    def eat(self):
        self.hunger -= 1
        self.energy += self.max_energy // 2
        self.env.remove_food(self.rect.center)

    def move_towards(self, target, speed=None):
        speed = speed or self.speed
        direction = np.array(target) - np.array(self.rect.center)
        distance_to_target = np.linalg.norm(direction)

        if distance_to_target <= speed:
            self.rect.center = target
        else:
            direction = direction / distance_to_target
            new_position = np.array(self.rect.center) + direction * speed
            self.rect.center = new_position

        # Normalize position to stay within env_window bounds
        self.rect = helper.normalize_position(self.rect, self.env_window)

    def move_in_direction(self, direction):
        direction = np.radians(direction)

        # Calculate the change in x and y coordinates
        dx = self.speed * np.cos(direction)
        dy = self.speed * np.sin(direction)

        # Update the current position
        new_position = (self.rect.center[0] + dx, self.rect.center[1] + dy)

        self.rect.center = new_position
        self.rect = helper.normalize_position(self.rect, self.env_window)

    def get_observation(self):
        if not hasattr(self, "parsed_dna"):
            self.parsed_dna = self.critter_manager.get_parsed_dna(self.DNA)

        observations = []
        # for sensor in self.parsed_dna:
        #     observation_func = getattr(SensorManager, f"obs_{sensor}", None)
        #     if observation_func is not None:
        #         observation = observation_func(self.env, self)
        #         observations.append(observation)
        #     else:
        #         # Handle the case where the sensor doesn't exist
        #         raise Exception(f"Error: No method for sensor {sensor}")
        return observations


class Plant(Sprite):
    def __init__(
        self,
        env_surface,
        pos=None,
        radius=4,
        n=200,
        color=(124, 176, 109),
    ):
        super().__init__()

        self.env_surface = env_surface

        self.radius = radius
        self.n = n

        # Create a transparent surface for the food
        self.image = pygame.Surface(((2 * radius), (2 * radius)), pygame.SRCALPHA)

        # Random position within env_window bounds
        self.position = pos or (
            random.randint(radius + 75, env_surface.get_width() - radius - 75),
            random.randint(radius + 75, env_surface.get_height() - radius - 75),
        )

        # Create the circle on the image surface (center of the surface)
        pygame.draw.circle(self.image, color, (radius, radius), radius)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def draw(self, surface):
        # Blit the food image to the env_window at its position
        surface.blit(self.image, self.rect.topleft)
