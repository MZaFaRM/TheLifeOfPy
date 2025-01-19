import math
import pygame
from pygame.sprite import Sprite
import helper
from handlers.neural import Genome
import numpy as np
import random
import noise
from enums import Base
from uuid import uuid4


class Creature(Sprite):
    def __init__(self, surface, context):
        super().__init__()
        position = context.get("position", None)
        color = context.get("color", (124, 245, 255))
        parents = context.get("parents", None)
        initial_energy = context.get("initial_energy", None)

        self.attrs = {
            "id": uuid4(),
            "color": color,
            "radius": context.get("radius", 5),
            "mating_timeout": random.randint(150, 300),
            "genome" : Genome(context.get("genome")),
            "colors": {
                "alive": color,
                "dead": (0, 0, 0),
                "reproducing": (255, 255, 255),
            },
            "border": {
                "color": (100, 57, 255),
                "thickness": 2.5,
            },
            "max_energy": 500,
            "max_speed": random.randint(1, 2),
            "vision": {
                "radius": 40,
                "color": {
                    Base.found: (0, 255, 0, 25),
                    Base.looking: (0, 255, 255, 25),
                },
            },
        }

        colors = [
            "#f94144",
            "#f3722c",
            "#f8961e",
            "#f9c74f",
            "#90be6d",
            "#43aa8b",
            "#577590",
        ]

        self.attrs["color"] = colors[self.attrs["max_speed"] - 1]

        self.states = {
            "angle": 0,  # degrees
            "hunger": 2,
            "speed": random.randint(1, 2),
            "alive": True,
            "time": 0,
            "time_alive": 0,
            "mating": {
                "state": Base.not_ready,
                "mate": None,
                "timeout": self.attrs["mating_timeout"],
            },
            "vision": {
                "food": {
                    "state": Base.looking,
                    "rect": None,
                },
                "mate": {
                    "state": Base.looking,
                    "mate": None,
                },
            },
            "acceleration_factor": 0.1,
            "td": random.randint(0, 1000),  # for pnoise generation
            "energy": (
                self.attrs["max_energy"] if not initial_energy else initial_energy
            ),
        }

        self.env_surface = surface
        self.noise = noise

        self.parents = parents

        self.done = False
        self.color = self.attrs["color"]

        # Create a transparent surface for the creature
        # +4 for radius
        surface_size = (
            (2 * self.attrs["radius"])
            + self.attrs["border"]["thickness"]
            + (2 * self.attrs["vision"]["radius"])
        )
        self.image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

        # Calculate center of the surface
        self.center = (surface_size // 2, surface_size // 2)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = position or helper.get_random_position(surface)

    def evaluate(self):
        return 1

    def draw(self, surface, vision_circle=False):
        if not self.states["alive"]:
            return

        if vision_circle:
            # Vision circle
            pygame.draw.circle(
                self.image,
                self.attrs["vision"]["color"][self.states["vision"]["food"]["state"]],
                self.center,
                self.attrs["radius"] + self.attrs["vision"]["radius"],
            )

        color = (0, 0, 0)
        if not self.states["alive"]:
            color = (0, 0, 0)
        elif self.states["mating"]["state"] == Base.mating:
            color = (255, 255, 255)
        elif self.states["mating"]["state"] == Base.ready:
            color = (0, 0, 255)

        # Border
        pygame.draw.circle(
            self.image,
            color,
            self.center,
            self.attrs["radius"] + self.attrs["border"]["thickness"],
        )

        color = self.attrs["color"]
        if not self.states["alive"]:
            color = (0, 0, 0)

        # Creature
        pygame.draw.circle(
            self.image,
            color,
            self.center,
            self.attrs["radius"],
        )

        surface.blit(self.image, self.rect.topleft)

    def step(self):
        self.states["time"] += 1
        return

        if not self.done:
            self.states["time_alive"] += 1
            self.states["energy"] -= 1
            self.states["mating"]["timeout"] -= 1

            if self.states["mating"]["timeout"] <= 0:
                if (self.states["energy"] >= 50) and (
                    self.states["mating"]["state"] != Base.mating
                ):
                    self.states["mating"]["state"] = Base.ready
                    # if random.random() < 0.6:
                    #     pass

            self.update_vision_state()
            self.states["angle"] = self.update_angle()

            if self.states["energy"] <= 0:
                self.die()
                return

        if not self.states["alive"]:
            if (self.states["time"] - self.states["time_alive"]) < 100:
                return

    def set_mate(self, mate):
        self.states["mating"]["state"] = Base.mating
        self.states["mating"]["mate"] = mate

    def remove_mate(self):
        self.states["mating"]["state"] = Base.not_ready
        self.states["mating"]["mate"] = None
        self.states["mating"]["timeout"] = self.attrs["mating_timeout"]

    def update_vision_state(self):
        if rect := self.rect.collideobjects(
            [food.rect for food in self.env.plant_manager.get_plants()],
            key=lambda rect: rect,
        ):
            self.states["vision"]["food"]["state"] = Base.found
            self.states["vision"]["food"]["rect"] = rect
        else:
            self.states["vision"]["food"]["state"] = Base.looking
            self.states["vision"]["food"]["rect"] = None

        other_creatures = [
            creature
            for creature in self.env.creatures
            if creature is not self
            and creature.states["mating"]["state"] == Base.ready
            and creature.states["alive"]
        ]

        if creature_index := self.rect.collidelistall(
            [creature.rect for creature in other_creatures]
        ):
            self.states["vision"]["mate"]["state"] = Base.found
            self.states["vision"]["mate"]["mate"] = other_creatures[creature_index[0]]

        else:
            self.states["vision"]["mate"]["state"] = Base.looking
            self.states["vision"]["mate"]["mate"] = None
        return

    def update_angle(self):
        angle = noise.snoise2(self.states["td"], 0) * 360
        self.states["td"] += 0.01
        return angle

    def reset(self):
        self.states["hunger"] = 2
        self.done = False
        self.states["energy"] = self.attrs["max_energy"]
        self.closest_edge = None
        self.original_position = helper.get_random_position(self.env_window)
        self.rect.center = self.original_position

    def progress(self):
        if not self.done:
            if self.states["hunger"] == 0:
                self.reproduce()
            elif self.states["hunger"] == 1:
                pass
            else:
                self.die()
            self.done = True

    def reproduce(self):
        self.env.children.add(
            Creature(
                self.env,
                self.env_window,
                self.creature_manager,
                radius=self.attrs["radius"],
            )
        )

    def die(self):
        self.states["alive"] = False
        self.done = True

    def eat(self):
        self.states["hunger"] -= 1
        self.states["energy"] += self.attrs["max_energy"] // 2
        self.env.remove_food(self.rect.center)

    def move_towards(self, target, speed=None):
        speed = speed or self.states["speed"]
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
        dx = self.states["speed"] * np.cos(direction)
        dy = self.states["speed"] * np.sin(direction)

        # Update the current position
        new_position = (self.rect.center[0] + dx, self.rect.center[1] + dy)

        self.rect.center = new_position
        self.rect = helper.normalize_position(self.rect, self.env_window)

    def get_observation(self):
        if not hasattr(self, "parsed_dna"):
            self.parsed_dna = self.creature_manager.get_parsed_dna(self.DNA)

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

    def draw(self):
        # Blit the food image to the env_window at its position
        self.env_window.blit(self.image, self.rect.topleft)
