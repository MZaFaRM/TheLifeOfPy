import math
import pygame
from pygame.sprite import Sprite
import helper
from manager import SensorManager
import numpy as np
import random
import noise


class Creature(Sprite):
    def __init__(
        self,
        env,
        screen,
        creature_manager,
        radius=5,
        color=(124, 245, 255),
        parent=None,
    ):
        super().__init__()

        self.attrs = {
            "color": color,
            "radius": radius,
            "border": {
                "color": (100, 57, 255),
                "thickness": 1,
            },
            "max_energy": 1000,
            "max_speed": random.randint(1, 7),
            "vision": {
                "radius": 40,
                "color": {
                    "found": (0, 255, 0, 25),
                    "looking": (0, 255, 255, 25),
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
            "speed": random.randint(1, 7),
            "alive": True,
            "time": 0,
            "time_alive": 0,
            "vision": "looking",  # looking, found
            "acceleration_factor": 0.1,
            "td": random.randint(0, 1000),  # for pnoise generation
            "energy": self.attrs["max_energy"],
        }

        self.noise = noise

        self.screen = screen
        self.env = env

        self.parent = parent
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
        self.rect.center = helper.get_random_position(screen)

        self.DNA = self.creature_manager.register_creature(self)

    def draw_self(self, vision_circle=False):

        if vision_circle:
            # Vision circle
            pygame.draw.circle(
                self.image,
                self.attrs["vision"]["color"][self.states["vision"]],
                self.center,
                self.attrs["radius"] + self.attrs["vision"]["radius"],
            )

        # Border
        pygame.draw.circle(
            self.image,
            self.attrs["border"]["color"] if self.states["alive"] else (0, 0, 0),
            self.center,
            self.attrs["radius"] + self.attrs["border"]["thickness"],
        )

        # Creature
        pygame.draw.circle(
            self.image,
            self.attrs["color"] if self.states["alive"] else (0, 0, 0),
            self.center,
            self.attrs["radius"],
        )

    def step(self):
        self.states["time"] += 1

        if not self.done:
            self.states["time_alive"] += 1
            self.states["energy"] -= 1

            self.states["vision"], found_object_rect = self.update_vision_state()
            self.states["angle"] = self.update_angle()

            self.update_speed()

            if self.states["energy"] <= 0:
                self.die()
                return

            if self.states["hunger"] > 0:
                if self.states["vision"] == "found":
                    if self.rect.center == found_object_rect.center:
                        self.eat()
                    else:
                        self.move_towards(found_object_rect.center)
                        pass

                else:
                    self.move_in_direction(self.states["angle"])
            else:
                self.move_in_direction(self.states["angle"])

        if not self.states["alive"]:
            if (self.states["time"] - self.states["time_alive"]) < 100:
                return

        self.draw_self()

    def update_speed(self):
        self.states["speed"] += self.states["acceleration_factor"]
        if (self.states["speed"] > self.attrs["max_speed"]) or (
            self.states["speed"] < 0.7
        ):
            self.states["acceleration_factor"] = -self.states["acceleration_factor"]

    def update_vision_state(self):
        if found_object := self.rect.collideobjects(
            [food.rect for food in self.env.foods], key=lambda o: o
        ):
            return "found", found_object
        else:
            return "looking", found_object

    def update_angle(self):
        angle = noise.snoise2(self.states["td"], 0) * 360
        self.states["td"] += 0.01
        return angle

    def reset(self):
        self.states["hunger"] = 2
        self.done = False
        self.states["energy"] = self.attrs["max_energy"]
        self.closest_edge = None
        self.original_position = helper.get_random_position(self.screen)
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
                self.screen,
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

    def move_towards(self, target):
        direction = np.array(target) - np.array(self.rect.center)
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm  # Normalize direction vector
        new_position = np.array(self.rect.center) + direction * (
            min(self.states["speed"], 1)
        )
        self.rect.center = new_position

        self.rect = helper.normalize_position(self.rect, self.env.screen)

    def move_in_direction(self, direction):
        direction = np.radians(direction)

        # Calculate the change in x and y coordinates
        dx = self.states["speed"] * np.cos(direction)
        dy = self.states["speed"] * np.sin(direction)

        # Update the current position
        new_position = (self.rect.center[0] + dx, self.rect.center[1] + dy)

        self.rect.center = new_position
        self.rect = helper.normalize_position(self.rect, self.env.screen)

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
    def __init__(self, env, screen, radius=4, n=200, color=(124, 176, 109)):
        super().__init__()

        self.screen = screen
        self.env = env

        self.radius = radius
        self.n = n

        # Create a transparent surface for the food
        self.image = pygame.Surface(((2 * radius), (2 * radius)), pygame.SRCALPHA)

        # Random position within screen bounds
        self.position = (
            random.randint(radius + 75, screen.get_width() - radius - 75),
            random.randint(radius + 75, screen.get_height() - radius - 75),
        )

        # Create the circle on the image surface (center of the surface)
        pygame.draw.circle(self.image, color, (radius, radius), radius)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def draw(self):
        # Blit the food image to the screen at its position
        self.screen.blit(self.image, self.rect.topleft)
