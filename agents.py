import pygame
from pygame.sprite import Sprite
import helper
from manager import SensorManager
import numpy as np
import random


class Creature(Sprite):
    def __init__(
        self,
        env,
        screen,
        creature_manager,
        radius=5,
        n=100,
        color=(151, 190, 90),
        parent=None,
        genes="",
    ):
        super().__init__()

        self.screen = screen
        self.env = env
        self.time_alive = 0

        self.parent = parent

        self.radius = radius
        self.n = n

        self.creature_manager = creature_manager

        self.brain = self.creature_manager.get_brain()

        self.energy = self.max_energy = 250

        self.hunger = 2
        self.dead = False

        self.done = False
        self.color = color

        # Create a transparent surface for the creature
        surface_size = (2 * radius) + 4  # Total size of the surface
        self.image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

        # Random position within screen bounds
        self.closest_edge = None

        # Calculate center of the surface
        self.center = (surface_size // 2, surface_size // 2)

        # Draw the outer black circle and inner colored circle at the center
        self.draw_self(radius, color)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = helper.get_edge_position(radius, screen)

        self.DNA = self.creature_manager.register_creature(self)

    def set_closest_edge(self, position):
        if self.closest_edge:
            return self.closest_edge

        left = 0
        up = 0
        right = self.env.screen_width - 0
        down = self.env.screen_height - 0

        x, y = position

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
            self.closest_edge = (x, up)
        elif closest_edge == "down":
            self.closest_edge = (x, down)
        elif closest_edge == "left":
            self.closest_edge = (left, y)
        elif closest_edge == "right":
            self.closest_edge = (right, y)

        return self.closest_edge

    def draw_self(self, radius, color, border_thickness=2, border_color=(0, 0, 0)):
        pygame.draw.circle(
            self.image,
            border_color,
            self.center,
            radius + border_thickness,
        )
        pygame.draw.circle(
            self.image,
            color,
            self.center,
            radius,
        )

    def step(self):
        if not (self.dead or self.done):
            self.time_alive = 1
            observation = self.get_observation()
            action = self.brain.get_best_action(observation)

            if action == 0:
                self.rect.centerx += 10
            elif action == 1:
                self.rect.centerx -= 10
            elif action == 2:
                self.rect.centery += 10
            elif action == 3:
                self.rect.centery -= 10

            if self.env.touching_food(self.rect.center):
                self.eat()

            self.energy -= 1
            if self.energy < 0:
                self.done = True
                self.die()
            return
        else:
            pass
        
        return

        if not (self.dead or self.done):
            self.energy -= 1

            if self.energy <= 0:
                self.die()
                return

            if self.hunger > 0:
                food_available = self.env.nearest_food(self.rect.center)
                if food_available is not None:
                    if self.env.touching_food(self.rect.center):
                        self.eat()
                    else:
                        self.move_in_direction(SensorManager.obs_Nfd(self.env, self))
                        pass

                else:
                    if self.hunger == 1:
                        self.move_in_direction(SensorManager.obs_Nfd(self.env, self))
                    else:
                        self.die()
                        return
            else:
                self.move_towards(self.set_closest_edge(self.rect.center))

            if self.rect.center == self.closest_edge:
                self.progress()

    def reset(self):
        self.hunger = 2
        self.done = False
        self.energy = self.max_energy
        self.closest_edge = None
        self.original_position = helper.get_edge_position(self.radius, self.screen)
        self.rect.center = self.original_position
        self.draw_self(self.radius, self.color)

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
        self.draw_self(self.radius, (128, 0, 128))
        self.env.children.add(
            Creature(
                self.env,
                self.screen,
                self.creature_manager,
                radius=self.radius,
                n=self.n,
            )
        )

    def die(self):
        self.dead = True
        self.done = True
        self.draw_self(self.radius, (255, 0, 0))

    def eat(self):
        print(self, "ate")
        self.hunger -= 1
        self.energy += 125

    def move_towards(self, target, speed=1.0):
        direction = np.array(target) - np.array(self.rect.center)
        norm = np.linalg.norm(direction)
        if norm > 0:
            direction = direction / norm  # Normalize direction vector
        new_position = np.array(self.rect.center) + direction * speed
        self.rect.center = new_position

    def move_in_direction(self, target, speed=1.0):
        # direction = np.array(target) - np.array(self.rect.center)
        # Step 1: Convert degrees to radians
        direction_radians = np.radians(target)

        # Step 2: Calculate the change in x and y coordinates
        dx = speed * np.cos(direction_radians) * speed
        dy = speed * np.sin(direction_radians) * speed

        # Step 3: Update the current position
        new_position = (self.rect.center[0] + dx, self.rect.center[1] + dy)

        self.rect.center = new_position

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

    def render(self):
        # Blit the food image to the screen at its position
        self.screen.blit(self.image, self.rect.topleft)


class Food(Sprite):
    def __init__(self, env, screen, radius=8, n=100, color=(232, 141, 103)):
        super().__init__()

        self.screen = screen
        self.env = env

        self.radius = radius
        self.n = n

        # Create a transparent surface for the food
        self.image = pygame.Surface(
            ((2 * radius) + 5, (2 * radius) + 5), pygame.SRCALPHA
        )

        # Random position within screen bounds
        self.position = (
            random.randint(radius + 75, screen.get_width() - radius - 75),
            random.randint(radius + 75, screen.get_height() - radius - 75),
        )

        # Create the circle on the image surface (center of the surface)
        pygame.draw.circle(self.image, color, (radius + 2, radius + 2), radius)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def draw(self):
        # Blit the food image to the screen at its position
        self.screen.blit(self.image, self.rect.topleft)
