import time
import pygame
from pygame.sprite import Sprite
from gym.spaces import MultiDiscrete
import random
import numpy as np
from noise import pnoise2
import helper


class Creature(Sprite):
    def __init__(self, env, screen, radius=15, n=100, color=(151, 190, 90)):
        super().__init__()

        self.screen = screen
        self.env = env

        self.radius = radius
        self.n = n

        self.hunger = 2
        self.dead = False

        self.done = False
        self.color = color

        # Create a transparent surface for the creature
        surface_size = (2 * radius) + 4  # Total size of the surface
        self.image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)

        # Random position within screen bounds
        self.original_position = helper.get_edge_position(radius, screen)

        # Calculate center of the surface
        self.center = (surface_size // 2, surface_size // 2)

        # Draw the outer black circle and inner colored circle at the center
        self.draw_self(radius, color)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = self.original_position

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

    def reset(self):
        self.hunger = 2
        self.done = False
        self.original_position = helper.get_edge_position(self.radius, self.screen)
        self.rect.center = self.original_position

    def step(self):
        if not (self.dead or self.done):
            if self.hunger > 0:
                food_available = env.nearest_food(self.rect.center)
                if food_available:
                    if env.touching_food(self.rect.center):
                        self.eat()
                    else:
                        self.move_towards(food_available)

                else:
                    if self.hunger == 1:
                        self.move_towards(self.original_position)
                    else:
                        self.die()
            else:
                self.move_towards(self.original_position)

            if self.rect.center == self.original_position:
                self.progress()

    def reset(self):
        self.hunger = 2
        self.done = False
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
                radius=self.radius,
                n=self.n,
            )
        )

    def die(self):
        self.dead = True
        self.done = True
        self.draw_self(self.radius, (255, 0, 0))

    def eat(self):
        self.hunger -= 1

    def move_towards(self, target):
        # Calculate the angle between the creature and the target
        angle = np.arctan2(
            target[1] - self.rect.center[1], target[0] - self.rect.center[0]
        )

        # Calculate the new position of the creature
        new_x = self.rect.center[0] + np.cos(angle)
        new_y = self.rect.center[1] + np.sin(angle)

        # Update the position of the creature
        self.rect.center = (new_x, new_y)

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


class Nature:
    def __init__(self):
        self.background_color = (243, 247, 236)
        self.food_color = (232, 141, 103)
        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Walker")

        self.action_space = MultiDiscrete([3, 3])
        self.observation_space = None

        self.truncation = 1_000_000

        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()

        self.generate_creatures(n=1)
        self.foods = pygame.sprite.Group()
        self.children = pygame.sprite.Group()

        self.reset()

    def generate_creatures(self, radius=15, n=50):
        self.creatures = pygame.sprite.Group()
        for i in range(n):
            # food sprite group
            self.creatures.add(Creature(self, self.screen, radius=radius, n=n))

    def generate_food(self, radius=8, n=100):
        self.foods = pygame.sprite.Group()
        for i in range(n):
            # food sprite group
            self.foods.add(Food(self, self.screen, radius=radius, n=n))

    def nearest_food(self, position):
        nearest = None
        nearest_distance = float("inf")
        for food in self.foods:
            distance = np.linalg.norm(np.array(food.position) - np.array(position))
            if distance < nearest_distance:
                nearest = food.position
                nearest_distance = distance
        return nearest

    def touching_food(self, position):
        for food in self.foods:
            if food.rect.collidepoint(position):
                self.foods.remove(food)
                return True
        return False

    def step(self):
        self.time_alive += 1
        reward = 0

        for creature in self.creatures:
            creature.step()
        self.clock.tick(60)

        # done = False if any creature is not done else True
        self.done = all([creature.done for creature in self.creatures])

        if self.time_alive >= self.truncation:
            self.truncated = True
            self.done = True

        return (
            self.get_observation(),
            reward,
            self.done,
            self.truncated,
        )

    def reset(self):
        time.sleep(1)

        self.done = False
        self.truncated = False
        self.time_alive = 0
        self.generate_food(n=50)

        self.new_generation = pygame.sprite.Group()

        for creature in self.creatures:
            if not creature.dead:
                creature.reset()
                self.new_generation.add(creature)

        for creature in self.children:
            self.new_generation.add(creature)

        self.creatures = self.new_generation.copy()
        self.children = pygame.sprite.Group()
        self.new_generation = pygame.sprite.Group()
        print(len(self.creatures))

    def render(self):
        self.screen.fill(self.background_color)
        self.foods.draw(self.screen)  # Render all food items
        self.creatures.draw(self.screen)  # Render all creatures
        pygame.display.update()

    def get_observation(self):
        return None


env = Nature()

while True:
    env.reset()
    env.render()
    done = False
    truncated = False

    while not (done or truncated):
        observation, reward, done, truncated = env.step()
        env.render()
