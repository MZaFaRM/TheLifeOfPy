import numpy as np
import pygame
from gym.spaces import MultiDiscrete

import agents
from layouts.environment import EnvLayout
from layouts.sidebar import SidebarLayout
import manager

# from graphs import PopulationPlot

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
            env=self,
            env_window=self.env_layout.surface,
        )
        self.plant_manager = manager.PlantManager(
            env=self,
            env_surface=self.env_layout.surface,
        )
        self.creatures = self.creature_manager.generate_creatures(n=100)
        self.plant_manager.bulk_generate_plants_patch(n=10)

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

        # Sidebar
        self.sidebar_layout = SidebarLayout(main_layout=self.main_layout)

        pygame.display.set_caption("DARWIN")

    def remove_food(self, position):
        for plant in self.plant_manager.get_plants():
            if plant.rect.collidepoint(position):
                self.plant_manager.remove_plant(plant)
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

        # Batch all steps before rendering
        for creature in self.creatures:
            creature.step()

        # self.graph_manager.update_population(self.time_steps, creature_data)
        self.clock.tick(1000)
        # self.done = all(creature.done for creature in creatures)
        self.truncated = False  # or len(self.creatures) == 0

        if self.time_steps % 100 == 0:
            self.plant_manager.create_plant_patch()

        return self.get_observation(), reward, self.done, self.truncated

    def reset(self):
        return

    def render(self):
        self.main_layout.surface.blit(self.main_layout.bg_image, (0, 0))
        self.sidebar_layout.update(self.creatures)
        self.main_layout.surface.blit(
            self.sidebar_layout.surface, self.sidebar_layout.rect
        )
        self.env_layout.update(self.plant_manager.get_plants(), self.creatures)
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
