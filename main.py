import time

import numpy as np
import pygame
from gym.spaces import MultiDiscrete

import agents
import config
import helper
import manager

# from graphs import PopulationPlot
from config import Colors, Fonts, image_assets


class Nature:
    def __init__(self):

        pygame.font.init()
        self.buttons = {}

        self.clock = pygame.time.Clock()

        self.setup_screen()

        self.action_space = MultiDiscrete([3, 3])
        self.observation_space = None

        self.truncation = 1_000_000

        # self.graph_manager = PopulationPlot([1, 2], 200)

        self.creature_manager = manager.CreatureManager(
            env=self, env_window=self.env_window
        )

        self.creatures = self.creature_manager.generate_creatures(n=200)
        self.foods = pygame.sprite.Group()
        self.children = pygame.sprite.Group()

        self.time_steps = 0

        self.reset()

    def setup_screen(self):
        # Main Window
        self.setup_main_window()

        # Define constants
        self.scaling_factor = helper.get_scaling_factor(self.main_window)

        # Environment
        self.setup_env_window()

        # Define constants
        self.screen_width = self.env_window.get_width()
        self.screen_height = self.env_window.get_height()

        # Sidebar
        self.setup_sidebar()

        pygame.display.set_caption("DARWIN")

    def setup_sidebar(self):
        self.sidebar_image = pygame.image.load(image_assets + "/sidebar.svg")
        self.sidebar_window = pygame.Surface(
            (self.sidebar_image.get_width(), self.sidebar_image.get_height()),
            pygame.SRCALPHA,
        )
        self.sidebar_window.blit(self.sidebar_image, (0, 0))
        self.sidebar_window_rect = self.sidebar_window.get_rect()
        self.sidebar_window_rect.topright = (self.main_window.get_width() - 50, 50)

        sidebar_window_width = self.sidebar_window.get_width()
        sidebar_window_height = self.sidebar_window.get_height()

        button_configs = [
            {
                "name": "create_organism",
                "image": "/create_organism_button.svg",
                "position": (
                    sidebar_window_width // 2,
                    sidebar_window_height - 225,
                ),
            },
            {
                "name": "end_simulation",
                "image": "/end_simulation_button.svg",
                "position": (
                    sidebar_window_width // 2,
                    sidebar_window_height - 150,
                ),
            },
            {
                "name": "show_graphs",
                "image": "/show_graphs_button.svg",
                "position": (
                    sidebar_window_width // 2,
                    sidebar_window_height - 75,
                ),
            },
        ]

        # Load, position, and blit each button
        for config in button_configs:
            self.load_and_store_button(
                name=config["name"],
                screen=self.sidebar_window,
                image_name=config["image"],
                position=config.pop("position"),
            )

        # Draw the sidebar window onto the main window
        self.main_window.blit(self.sidebar_window, self.sidebar_window_rect)

    def load_and_store_button(self, screen, name, image_name, position):
        button_image = pygame.image.load(image_assets + image_name)
        button_rect = button_image.get_rect(center=position)
        # Blit button to the sidebar
        screen.blit(button_image, button_rect)
        # Store button's image and rect in a dictionary for later reference
        self.buttons[name] = {"image": button_image, "rect": button_rect}

    def setup_env_window(self):
        self.env_image = pygame.image.load(image_assets + "/dot_grid.svg")
        self.env_window = pygame.Surface(
            (self.env_image.get_width(), self.env_image.get_height()), pygame.SRCALPHA
        )
        self.env_window.blit(self.env_image, (0, 0))
        self.main_window.blit(self.env_window, (50, 100))

    def setup_main_window(self):
        self.main_window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.bg_image = pygame.image.load(image_assets + "/background.svg")
        self.main_window.blit(self.bg_image, (0, 0))
        y = self.main_window.get_height() - 75

        self.time_control_buttons = {
            "pause_time": {
                "name": "pause_time",
                "image": "/pause_time_button.svg",
                "clicked_image": "/pause_time_button_clicked.svg",
                "clicked": False,
                "position": (75, y),
            },
            "play_time": {
                "name": "play_time",
                "image": "/play_time_button.svg",
                "clicked_image": "/play_time_button_clicked.svg",
                "clicked": True,
                "position": (125, y),
            },
            "fast_forward_time": {
                "name": "fast_forward_time",
                "image": "/fast_forward_button.svg",
                "clicked_image": "/fast_forward_button_clicked.svg",
                "clicked": False,
                "position": (175, y),
            },
        }

        for _, button_data in self.time_control_buttons.items():
            default_button = pygame.image.load(image_assets + button_data.pop("image"))
            clicked_button = pygame.image.load(
                image_assets + button_data.pop("clicked_image")
            )
            button_rect = default_button.get_rect(center=button_data.pop("position"))

            button_data.update(
                {
                    "image": {
                        "default": default_button,
                        "clicked": clicked_button,
                    },
                    "rect": button_rect,
                }
            )

    def generate_food(self, n=100):
        self.foods = pygame.sprite.Group()
        for _ in range(n):
            # food sprite group
            self.foods.add(agents.Food(self, self.env_window, n=n))

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
                for button, button_data in self.time_control_buttons.items():
                    if button_data["rect"].collidepoint(event.pos):
                        button_data["clicked"] = True
                        for other_button in self.time_control_buttons:
                            if other_button != button:
                                self.time_control_buttons[other_button][
                                    "clicked"
                                ] = False
                        break

        if self.time_control_buttons["pause_time"]["clicked"]:
            return self.get_observation(), reward, self.done, self.truncated
        self.time_steps += 1

        creatures = self.creature_manager.creatures
        creature_data = {1: 0, 2: 0}

        # Batch all steps before rendering
        for creature in creatures:
            # time.sleep(0.01)
            creature.step()
            creature_data[creature.attrs["max_speed"]] += 1

        # self.graph_manager.update_population(self.time_steps, creature_data)
        # self.clock.tick(60)
        # self.done = all(creature.done for creature in creatures)
        self.truncated = len(creatures) == 0
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

        self.children = pygame.sprite.Group()
        self.new_generation = pygame.sprite.Group()

    def render(self):
        self.env_window.fill(Colors.bg_color)
        self.env_window.blit(self.env_image, (0, 0))

        self.foods.draw(self.env_window)  # Render all food items
        self.creatures.draw(self.env_window)  # Render all creatures
        self.main_window.blit(self.env_window, (50, 100))

        for _, button_data in self.time_control_buttons.items():
            if button_data["clicked"]:
                self.main_window.blit(
                    button_data["image"]["clicked"], button_data["rect"]
                )
            else:
                self.main_window.blit(
                    button_data["image"]["default"], button_data["rect"]
                )

        pygame.display.update()

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
