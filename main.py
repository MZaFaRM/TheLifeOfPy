import time

import numpy as np
import pygame
from gym.spaces import MultiDiscrete

import agents
import manager


class Nature:
    def __init__(self):
        self.background_color = (0, 0, 0)
        self.clock = pygame.time.Clock()

        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        pygame.display.set_caption("Walker")

        self.action_space = MultiDiscrete([3, 3])
        self.observation_space = None

        self.truncation = 1_000_000

        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()

        self.creature_manager = manager.CreatureManager(env=self, screen=self.screen)

        self.creatures = self.creature_manager.generate_creatures(n=50)
        self.foods = pygame.sprite.Group()
        self.children = pygame.sprite.Group()

        self.reset()

    def generate_food(self, radius=5, n=100):
        self.foods = pygame.sprite.Group()
        for _ in range(n):
            # food sprite group
            self.foods.add(agents.Food(self, self.screen, radius=radius, n=n))

    def nearest_food(self, position):
        creature_pos = np.array(position)
        food_positions = np.array([food.position for food in env.foods])

        # Squared distances
        distances = np.sum((food_positions - creature_pos) ** 2, axis=1)

        # If there are no food objects
        if len(distances) == 0:
            # No food, so return infinite distance and no position
            return None

        # Find the index of the nearest food
        nearest_index = np.argmin(distances)

        # Return the nearest distance and its coordinates
        nearest_coordinates = food_positions[nearest_index]

        return nearest_coordinates

    def touching_food(self, position):
        for food in self.foods:
            if food.rect.collidepoint(position):
                self.foods.remove(food)
                return True
        return False

    def step(self):
        reward = 0

        # Batch all steps before rendering
        for creature in self.creatures:
            creature.step()

        self.clock.tick(60)
        self.done = all(creature.done for creature in self.creatures)
        self.truncated = len(self.creatures) == 0
        return self.get_observation(), reward, self.done, self.truncated

    def reset(self):
        time.sleep(1)

        self.done = False
        self.truncated = False
        self.generate_food(n=100)

        self.new_generation = pygame.sprite.Group()

        for creature in self.creatures:
            if creature.states["alive"]:
                creature.reset()
                self.new_generation.add(creature)
        # for creature in self.children:
        #     self.new_generation.add(creature)

        self.creatures = self.new_generation.copy()
        self.children = pygame.sprite.Group()
        self.new_generation = pygame.sprite.Group()

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

    # if truncated:
    #     break
