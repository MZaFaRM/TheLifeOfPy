import pygame

from config import Colors, image_assets
from manager import Counter


class MainLayout:
    def __init__(self, buttons):
        self.surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.bg_image = pygame.image.load(image_assets + "/background.svg")
        self.surface.blit(self.bg_image, (0, 0))
        y = self.surface.get_height() - 75

        self.time_control_buttons = buttons

        self.close_window_button = pygame.image.load(
            image_assets + "/close_window_button.svg"
        )
        self.close_window_button_rect = self.close_window_button.get_rect(
            topright=(self.surface.get_width(), 0)
        )

        for _, button_data in self.time_control_buttons.items():
            default_button = pygame.image.load(image_assets + button_data.pop("image"))
            clicked_button = pygame.image.load(
                image_assets + button_data.pop("clicked_image")
            )
            button_rect = default_button.get_rect(
                center=(button_data.pop("x_position"), y)
            )

            button_data.update(
                {
                    "image": {
                        "default": default_button,
                        "clicked": clicked_button,
                    },
                    "rect": button_rect,
                }
            )

    def handle_button_click(self, event):
        if self.close_window_button_rect.collidepoint(event.pos):
            pygame.quit()
            exit()

        for button, button_data in self.time_control_buttons.items():
            if button_data["rect"].collidepoint(event.pos):
                button_data["clicked"] = True
                for other_button in self.time_control_buttons:
                    if other_button != button:
                        self.time_control_buttons[other_button]["clicked"] = False
                break

    def update(self):
        self.surface.blit(self.close_window_button, self.close_window_button_rect)
        for button_data in self.time_control_buttons.values():
            if button_data["clicked"]:
                self.surface.blit(button_data["image"]["clicked"], button_data["rect"])
            else:
                self.surface.blit(button_data["image"]["default"], button_data["rect"])


class EnvLayout:
    def __init__(self, main_layout):
        self.main_layout = main_layout
        self.env_image = pygame.image.load(image_assets + "/dot_grid.svg")
        self.surface = pygame.Surface(
            (self.env_image.get_width(), self.env_image.get_height()), pygame.SRCALPHA
        )
        self.surface.blit(self.env_image, (0, 0))
        self.main_layout.surface.blit(self.surface, (50, 100))

    def update(self, foods, creatures):
        self.surface.fill(Colors.bg_color)
        self.surface.blit(self.env_image, (0, 0))

        foods.draw(self.surface)
        for creature in creatures:
            creature.draw(self.surface)


class SidebarLayout:
    def __init__(self, main_layout):
        self.main_layout = main_layout

        self.sidebar_image = pygame.image.load(image_assets + "/sidebar.svg")
        self.surface = pygame.Surface(
            (self.sidebar_image.get_width(), self.sidebar_image.get_height()),
            pygame.SRCALPHA,
        )
        self.surface.blit(self.sidebar_image, (0, 0))
        self.rect = self.surface.get_rect()
        self.rect.topright = (
            self.main_layout.surface.get_width() - 50,
            50,
        )

        self.alive_counter = Counter()
        self.dead_counter = Counter()

        sidebar_window_width = self.surface.get_width()
        sidebar_window_height = self.surface.get_height()

        self.buttons = {
            "create_organism": {
                "name": "create_organism",
                "image": "/create_organism_button.svg",
                "position": (
                    sidebar_window_width // 2,
                    sidebar_window_height - 225,
                ),
            },
            "end_simulation": {
                "name": "end_simulation",
                "image": "/end_simulation_button.svg",
                "position": (
                    sidebar_window_width // 2,
                    sidebar_window_height - 150,
                ),
            },
            "show_graphs": {
                "name": "show_graphs",
                "image": "/show_graphs_button.svg",
                "position": (
                    sidebar_window_width // 2,
                    sidebar_window_height - 75,
                ),
            },
        }

        # Load, position, and blit each button
        for button in self.buttons.values():
            self.load_and_store_button(
                name=button["name"],
                screen=self.surface,
                image_name=button["image"],
                position=button.pop("position"),
            )

        # Draw the sidebar window onto the main window
        self.main_layout.surface.blit(self.surface, self.rect)

    def load_and_store_button(self, screen, name, image_name, position):
        button_image = pygame.image.load(image_assets + image_name)
        button_rect = button_image.get_rect(center=position)
        # Blit button to the sidebar
        screen.blit(button_image, button_rect)
        # Store button's image and rect in a dictionary for later reference
        self.buttons[name].update({"image": button_image, "rect": button_rect})

    def update(self, creatures):
        alive = 0
        dead = 0
        for creature in creatures:
            if creature.states["alive"]:
                alive += 1
            else:
                dead += 1

        self.alive_counter.draw(value=alive)
        self.dead_counter.draw(value=dead)

        self.surface.blit(self.alive_counter.surface, (115, 325))
        self.surface.blit(self.dead_counter.surface, (290, 325))
