import pygame
from pygame.sprite import Sprite
from gym.spaces import MultiDiscrete
import random
import numpy as np
from noise import pnoise2
import helper


class Organism(Sprite):
    def __init__(
        self,
        env,
        screen,
        radius=15,
        border_thickness=2,
    ) -> None:
        self.screen = screen
        self.env = env

        # Set initial position to the center of the screen
        position = (screen.get_width() // 2, screen.get_height() // 2)

        self.image = pygame.Surface(
            ((2 * radius) + 5, (2 * radius) + 5), pygame.SRCALPHA
        )
        self.rect = self.image.get_rect()

        # Draw the border and filled circles
        pygame.draw.circle(
            self.image, (0, 0, 0, 255), self.rect.center, radius + border_thickness
        )
        pygame.draw.circle(self.image, (125, 125, 125, 255), self.rect.center, radius)

        self.rect.center = (
            position  # Set the center of the rect to the calculated position
        )

        self.maximum = 0
        self.minimum = 0

        self.tx = 0
        self.ty = 10000

    def step(self):
        test = pnoise2(self.tx, self.ty)
        # self.rect.centerx = helper.map_value(
        #     pnoise2(self.tx), -1, 1, 0, self.screen.get_width()
        # )
        # self.rect.centery = helper.map_value(
        #     pnoise2(self.ty), -1, 1, 0, self.screen.get_height()
        # )
        # self.maximum = max(self.maximum, pnoise1(self.tx))
        # self.minimum = min(self.minimum, pnoise1(self.tx))
        # print(self.maximum, self.minimum)

        self.tx += 0.01
        self.ty += 0.01

        reward = 0

        return (
            self.get_observation(),
            reward,
            self.env.done,
            self.env.truncated,
        )

    def get_observation(self):
        return None

    # def set_model(self, model):
    #     self.model = model

    def render(self):
        # self.image.fill(
        #     (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
        # )
        self.screen.blit(self.image, self.rect)


class Nature:
    def __init__(self):
        self.screen = pygame.display.set_mode((1600, 800))
        pygame.display.set_caption("Walker")

        self.action_space = MultiDiscrete([3, 3])
        self.observation_space = None
        self.creature = Organism(self, screen=self.screen)

        self.done = False
        self.truncated = False

        self.truncation = 1_000_000
        self.time = 0

        self.screen_width = self.screen.get_width()
        self.screen_height = self.screen.get_height()
        self.generate_terrain_map()

    def reset(self):
        self.generate_terrain_map()
        self.creature = Organism(self, screen=self.screen)
        self.done = False
        self.truncated = False
        self.time = 0
        return None

    def generate_terrain_map(self):
        # Generate the noise-based grass map
        grass_ratio, sky_ratio = 0.4, 0.6
        grass = pygame.Surface((self.screen_width, self.screen_height * grass_ratio))
        helper.create_gradient(grass, (207, 201, 38), (46, 207, 38))
        self.screen.blit(
            grass,
            (
                (self.screen_width - grass.get_width()) // 2,
                self.screen_height - grass.get_height(),
            ),
        )

        sky = pygame.Surface((self.screen_width, self.screen_height * sky_ratio))
        helper.create_gradient(sky, (87, 103, 165), (140, 143, 180))
        self.screen.blit(
            sky,
            (
                (self.screen_width - sky.get_width()) // 2,
                0,
            ),
        )

    def step(self):
        self.creature.step()
        self.time += 1
        reward = 0

        if self.time >= self.truncation:
            self.truncated = True
            self.done = True

        return (
            self.get_observation(),
            reward,
            self.done,
            self.truncated,
        )

    def render(self):
        self.creature.render()
        pygame.display.update()

    def get_observation(self):
        return None


env = Nature()
done = False
truncated = False
env.render()

while not done:
    action = env.action_space.sample()
    observation, reward, done, truncated = env.step()
    env.render()
