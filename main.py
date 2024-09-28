import pygame
from pygame.sprite import Sprite
from gym.spaces import MultiDiscrete
import random
import numpy as np
from noise import pnoise1 as noise


class Organism(Sprite):
    def __init__(self, env, screen, radius=5) -> None:
        self.screen = screen
        self.env = env
        self.image = pygame.Surface((2 * radius, 2 * radius), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (0, 0, 0, 2.5), (radius, radius), radius)
        self.rect = self.image.get_rect()
        self.rect.center = (400, 300)

    def step(self):
        np.random.normal(0, 1)
        if random.random() < 0.01:
            self.rect.x += random.randint(-100, 100)
            self.rect.y += random.randint(-100, 100)
        else:
            self.rect.x += random.randint(-1, 1)
            self.rect.y += random.randint(-1, 1)

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
        pygame.display.update()


class Nature:
    def __init__(self):
        self.screen = pygame.display.set_mode((800, 600))
        self.screen.fill((255, 255, 255))
        pygame.display.set_caption("Walker")

        self.action_space = MultiDiscrete([3, 3])
        self.observation_space = None
        self.creature = Organism(self, screen=self.screen)

        self.done = False
        self.truncated = False

        self.truncation = 1_000_000
        self.time = 0

    def reset(self):
        self.creature = Organism(self, screen=self.screen)
        self.done = False
        self.truncated = False
        self.time = 0
        return None

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

    def get_observation(self):
        return None


env = Nature()
done = False
truncated = False

while not done:
    action = env.action_space.sample()
    observation, reward, done, truncated = env.step()
    env.render()
