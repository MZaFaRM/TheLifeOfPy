import sys
import pygame
from src.components.home import HomeComponent
from src.components.laboratory import LaboratoryComponent


class UIHandler:
    def __init__(self):
        self.surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.surface.fill((26, 26, 26))
        pygame.display.set_caption("PetriPixel")

        self.screen_states = {
            "current_screen": "home",
            "screens": ["home", "laboratory", "graphs"],
            "home": {
                "handler": HomeComponent,
                "custom_position": {
                    "topleft": (0, 0),
                },
                "context": {},
            },
            "laboratory": {
                "handler": LaboratoryComponent,
                "custom_position": {
                    "center": (
                        self.surface.get_width() // 2,
                        self.surface.get_height() // 2,
                    ),
                },
                "context": {},
            },
            "graphs": {
                "components": {},
                "context": {},
            },
        }

    def initialize_screen(self, screen="home"):
        self.screen_states["current_screen"] = screen
        self.screen_states["rendered_components"] = {}

        rendered_component = self.screen_states[screen]["handler"](
            main_surface=self.surface,
            context=self.screen_states[screen].get("context", {}),
        )
        self.screen_states["rendered_components"][screen] = {
            **self.screen_states[screen],
            "handler": rendered_component,
        }

    def event_handler(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)

            for name, info in self.screen_states["rendered_components"].items():
                yield info["handler"].event_handler(event) or []

    def update_screen(self, context=None):
        self.surface.fill((26, 26, 26))

        for name, info in self.screen_states["rendered_components"].items():
            info["handler"].update(context=context)
            rect = info["handler"].surface.get_rect(**info["custom_position"])
            self.surface.blit(info["handler"].surface, dest=rect)

        pygame.display.flip()

    def get_component(self, name):
        current_screen = self.screen_states["current_screen"]
        for component in self.screen_states["rendered_components"][current_screen][
            "handler"
        ].components:
            if component["name"] == name:
                return component["rendered_handler"]
        return ValueError(f"Component {name} not found in {current_screen}")
