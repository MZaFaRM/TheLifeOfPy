import math
import pygame
from pygame.sprite import Sprite
import helper
from manager import SensorManager
import numpy as np
import random
import noise
from enums import Base
from uuid import uuid4


class Creature(Sprite):
    def __init__(
        self,
        env,
        env_window,
        creature_manager,
        radius=5,
        position=None,
        color=(124, 245, 255),
        parents=None,
    ):
        super().__init__()

        self.attrs = {
            "id": uuid4(),
            "color": color,
            "radius": radius,
            "mating_timeout": random.randint(150, 300),
            "colors": {
                "alive": color,
                "dead": (0, 0, 0),
                "reproducing": (255, 255, 255),
            },
            "border": {
                "color": (100, 57, 255),
                "thickness": 2.5,
            },
            "max_energy": 1000,
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
            "energy": self.attrs["max_energy"],
        }

        self.noise = noise

        self.env_window = env_window
        self.env = env

        self.parents = parents
        self.creature_manager = creature_manager

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

        # Draw the outer black circle and inner colored circle at the center
        self.draw_self()

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = position or helper.get_random_position(env_window)

        self.DNA = self.creature_manager.register_creature(self)

    def draw_self(self, vision_circle=False):

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

    def step(self):
        self.states["time"] += 1

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

            self.update_speed()

            if self.states["energy"] <= 0:
                self.die()
                return

            if self.states["mating"]["state"] == Base.mating:
                self.move_towards(self.states["mating"]["mate"].rect.center, speed=0.8)

                if self.rect.center == self.states["mating"]["mate"].rect.center:
                    self.creature_manager.add_creatures(
                        n=1,
                        parents=(self, self.states["mating"]["mate"]),
                        position=self.rect.center,
                    )

                    self.states["mating"]["mate"].remove_mate()
                    self.remove_mate()

            elif (
                # Check if the creature is ready to mate
                (self.states["mating"]["state"] == Base.ready)
                # Check if a mate is found
                and (self.states["vision"]["mate"]["state"] == Base.found)
                # Check if the mate is ready to mate
                and (
                    self.states["vision"]["mate"]["mate"].states["mating"]["state"]
                    == Base.ready
                )
            ):
                # Set the creature's mating state to mating
                self.set_mate(mate=self.states["vision"]["mate"]["mate"])
                # Set the mate's mating state to mating
                self.states["vision"]["mate"]["mate"].set_mate(mate=self)

                self.move_towards(self.states["mating"]["mate"].rect.center)

            elif self.states["hunger"] > 0:
                if self.states["vision"]["food"]["state"] == Base.found:
                    if self.rect.center == self.states["vision"]["food"]["rect"].center:
                        self.eat()
                    else:
                        self.move_towards(self.states["vision"]["food"]["rect"].center)
                        pass

                else:
                    self.move_in_direction(self.states["angle"])
            else:
                self.move_in_direction(self.states["angle"])

        if not self.states["alive"]:
            if (self.states["time"] - self.states["time_alive"]) < 100:
                return

        self.draw_self()

    def set_mate(self, mate):
        self.states["mating"]["state"] = Base.mating
        self.states["mating"]["mate"] = mate

    def remove_mate(self):
        self.states["mating"]["state"] = Base.not_ready
        self.states["mating"]["mate"] = None
        self.states["mating"]["timeout"] = self.attrs["mating_timeout"]

    def update_speed(self):
        self.states["speed"] += self.states["acceleration_factor"]
        if (self.states["speed"] > self.attrs["max_speed"]) or (
            self.states["speed"] < 0.7
        ):
            self.states["acceleration_factor"] = -self.states["acceleration_factor"]

    def update_vision_state(self):
        if rect := self.rect.collideobjects(
            [food.rect for food in self.env.foods], key=lambda rect: rect
        ):
            self.states["vision"]["food"]["state"] = Base.found
            self.states["vision"]["food"]["rect"] = rect
        else:
            self.states["vision"]["food"]["state"] = Base.looking
            self.states["vision"]["food"]["rect"] = None

        other_creatures = [
            creature
            for creature in self.env.creatures
            if creature is not self and creature.states["mating"]["state"] == Base.ready
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
        self.draw_self()

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
        self.draw_self()
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
        self.rect = helper.normalize_position(self.rect, self.env.env_window)

    def move_in_direction(self, direction):
        direction = np.radians(direction)

        # Calculate the change in x and y coordinates
        dx = self.states["speed"] * np.cos(direction)
        dy = self.states["speed"] * np.sin(direction)

        # Update the current position
        new_position = (self.rect.center[0] + dx, self.rect.center[1] + dy)

        self.rect.center = new_position
        self.rect = helper.normalize_position(self.rect, self.env.env_window)

    def get_observation(self):
        if not hasattr(self, "parsed_dna"):
            self.parsed_dna = self.creature_manager.get_parsed_dna(self.DNA)

        observations = []
        for sensor in self.parsed_dna:
            observation_func = getattr(SensorManager, f"obs_{sensor}", None)
            if observation_func is not None:
                observation = observation_func(self.env, self)
                observations.append(observation)
            else:
                # Handle the case where the sensor doesn't exist (optional)
                raise Exception(f"Error: No method for sensor {sensor}")
        return observations


class Food(Sprite):
    def __init__(self, env, env_window, radius=4, n=200, color=(124, 176, 109)):
        super().__init__()

        self.env_window = env_window
        self.env = env

        self.radius = radius
        self.n = n

        # Create a transparent surface for the food
        self.image = pygame.Surface(((2 * radius), (2 * radius)), pygame.SRCALPHA)

        # Random position within env_window bounds
        self.position = (
            random.randint(radius + 75, env_window.get_width() - radius - 75),
            random.randint(radius + 75, env_window.get_height() - radius - 75),
        )

        # Create the circle on the image surface (center of the surface)
        pygame.draw.circle(self.image, color, (radius, radius), radius)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def draw(self):
        # Blit the food image to the env_window at its position
        self.env_window.blit(self.image, self.rect.topleft)
