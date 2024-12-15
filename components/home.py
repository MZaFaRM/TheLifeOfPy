import pygame

from config import Colors, image_assets
from handlers.organisms import Counter


class HomeComponent:
    def __init__(self, context=None):
        self.context = context
        screen_width, screen_height = pygame.display.get_surface().get_size()
        self.surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
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

        self.close_window_button = pygame.image.load(
            image_assets + "/close_window_button.svg"
        )
        self.close_window_button_rect = self.close_window_button.get_rect(
            topright=(screen_width, 0)
        )

        y = screen_height - 75
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

    def event_handler(self, events):
        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.close_window_button_rect.collidepoint(event.pos):
                    pygame.quit()
                    exit()

                for button, button_data in self.time_control_buttons.items():
                    if button_data["rect"].collidepoint(event.pos):
                        button_data["clicked"] = True
                        for other_button in self.time_control_buttons:
                            if other_button != button:
                                self.time_control_buttons[other_button][
                                    "clicked"
                                ] = False
                        break

    def update(self, context=None):
        self.surface.blit(self.close_window_button, self.close_window_button_rect)
        for button_data in self.time_control_buttons.values():
            if button_data["clicked"]:
                self.surface.blit(button_data["image"]["clicked"], button_data["rect"])
            else:
                self.surface.blit(button_data["image"]["default"], button_data["rect"])


class EnvComponent:
    def __init__(self, context=None):
        self.env_image = pygame.image.load(image_assets + "/dot_grid.svg")
        self.surface = pygame.Surface(
            (self.env_image.get_width(), self.env_image.get_height()), pygame.SRCALPHA
        )
        self.surface.blit(self.env_image, (0, 0))

    def event_handler(self, events):
        pass

    def update(self, context=None):
        plants = context.get("plants")
        creatures = context.get("creatures")

        self.surface.fill(Colors.bg_color)
        self.surface.blit(self.env_image, (0, 0))

        plants.draw(self.surface)
        for creature in creatures:
            creature.draw(self.surface)


class SidebarComponent:
    def __init__(self, context=None):
        self.sidebar_image = pygame.image.load(image_assets + "/sidebar.svg")
        self.surface = pygame.Surface(
            (self.sidebar_image.get_width(), self.sidebar_image.get_height()),
            pygame.SRCALPHA,
        )
        self.surface.blit(self.sidebar_image, (0, 0))

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

    def event_handler(self, events):
        pass

    def load_and_store_button(self, screen, name, image_name, position):
        button_image = pygame.image.load(image_assets + image_name)
        button_rect = button_image.get_rect(center=position)
        # Blit button to the sidebar
        screen.blit(button_image, button_rect)
        # Store button's image and rect in a dictionary for later reference
        self.buttons[name].update({"image": button_image, "rect": button_rect})

    def update(self, context=None):
        creatures = context.get("creatures")
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
