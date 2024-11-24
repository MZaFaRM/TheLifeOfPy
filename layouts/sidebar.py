import pygame
from config import image_assets
from manager import Counter


class SidebarLayout:
    def __init__(self, main_layout):
        self.main_layout = main_layout

        self.sidebar_image = pygame.image.load(image_assets + "/sidebar.svg")
        self.surface = pygame.Surface(
            (self.sidebar_image.get_width(), self.sidebar_image.get_height()),
            pygame.SRCALPHA,
        )
        self.surface.blit(self.sidebar_image, (0, 0))
        self.sidebar_window_rect = self.surface.get_rect()
        self.sidebar_window_rect.topright = (
            self.main_layout.surface.get_width() - 50,
            50,
        )

        self.alive_counter = Counter(start=10)
        self.dead_counter = Counter(start=5)

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
        self.main_layout.surface.blit(self.surface, self.sidebar_window_rect)

    def load_and_store_button(self, screen, name, image_name, position):
        button_image = pygame.image.load(image_assets + image_name)
        button_rect = button_image.get_rect(center=position)
        # Blit button to the sidebar
        screen.blit(button_image, button_rect)
        # Store button's image and rect in a dictionary for later reference
        self.buttons[name].update({"image": button_image, "rect": button_rect})
