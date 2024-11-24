import pygame
from config import image_assets


class MainLayout:
    def __init__(self, buttons):
        self.surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.bg_image = pygame.image.load(image_assets + "/background.svg")
        self.surface.blit(self.bg_image, (0, 0))
        y = self.surface.get_height() - 75

        self.time_control_buttons = buttons

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
        for button, button_data in self.time_control_buttons.items():
            if button_data["rect"].collidepoint(event.pos):
                button_data["clicked"] = True
                for other_button in self.time_control_buttons:
                    if other_button != button:
                        self.time_control_buttons[other_button]["clicked"] = False
                break

    def update(self):
        
        for button_data in self.time_control_buttons.values():
            if button_data["clicked"]:
                self.surface.blit(button_data["image"]["clicked"], button_data["rect"])
            else:
                self.surface.blit(button_data["image"]["default"], button_data["rect"])
