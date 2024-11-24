import time

import numpy as np
import pygame
from gym.spaces import MultiDiscrete

import agents
import config
import helper
from layouts.environment import EnvLayout
from layouts.sidebar import SidebarLayout
import manager
from manager import Counter

# from graphs import PopulationPlot
from config import Colors, Fonts, image_assets

from layouts.main import MainLayout


class Nature:
    def __init__(self):

        pygame.font.init()

        self.clock = pygame.time.Clock()

        self.time_steps = 0
        self.done = False
        self.truncated = False

        self.setup_screen()

        self.action_space = MultiDiscrete([3, 3])
        self.observation_space = None

        self.truncation = 1_000_000

        # self.graph_manager = PopulationPlot([1, 2], 200)

        self.creature_manager = manager.CreatureManager(
            env=self, env_window=self.env_layout.surface
        )
        self.creatures = self.creature_manager.generate_creatures(n=200)
        self.foods = self.generate_food(n=100)

    def setup_screen(self):
        # Main Window
        self.time_control_buttons = {
            "pause_time": {
                "name": "pause_time",
                "image": "/pause_time_button.svg",
                "clicked_image": "/pause_time_button_clicked.svg",
                "clicked": False,
                "x_position": 75,
            },
            "play_time": {
                "name": "play_time",
                "image": "/play_time_button.svg",
                "clicked_image": "/play_time_button_clicked.svg",
                "clicked": True,
                "x_position": 125,
            },
            "fast_forward_time": {
                "name": "fast_forward_time",
                "image": "/fast_forward_button.svg",
                "clicked_image": "/fast_forward_button_clicked.svg",
                "clicked": False,
                "x_position": 175,
            },
        }
        self.main_layout = MainLayout(buttons=self.time_control_buttons)

        # Environment
        self.env_layout = EnvLayout(
            main_layout=self.main_layout,
        )

        # Define constants
        self.screen_width = self.env_layout.surface.get_width()
        self.screen_height = self.env_layout.surface.get_height()

        # Sidebar
        self.sidebar_layout = SidebarLayout(main_layout=self.main_layout)

        pygame.display.set_caption("DARWIN")

    def generate_food(self, n=100):
        foods = pygame.sprite.Group()
        for _ in range(n):
            # food sprite group
            foods.add(agents.Food(self, self.env_layout.surface, n=n))
        return foods

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

    def remove_food(self, position):
        for food in self.foods:
            if food.rect.collidepoint(position):
                self.foods.remove(food)
                return True
        return False

    def step(self):
        reward = 0

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                self.done = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.main_layout.handle_button_click(event)

        if self.time_control_buttons["pause_time"]["clicked"]:
            return self.get_observation(), reward, self.done, self.truncated
        self.time_steps += 1

        creatures = self.creature_manager.creatures

        # Batch all steps before rendering
        for creature in creatures:
            creature.step()

        # self.graph_manager.update_population(self.time_steps, creature_data)
        self.clock.tick(1000)
        # self.done = all(creature.done for creature in creatures)
        self.truncated = len(creatures) == 0
        return self.get_observation(), reward, self.done, self.truncated

    def reset(self):
        return

    def render(self):
        self.env_layout.update(self.foods, self.creatures)
        self.main_layout.surface.blit(self.env_layout.surface, (50, 100))
        self.main_layout.update()
        pygame.display.flip()

    def get_observation(self):
        return None


try:
    env = Nature()

    # while True:
    env.reset()
    env.render()
    done = False
    truncated = False

    while not (done or truncated):
        observation, reward, done, truncated = env.step()
        env.render()

        # if truncated:
        #     break
except KeyboardInterrupt:
    pygame.quit()
    quit()
except Exception as e:
    raise e
