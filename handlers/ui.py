import pygame
from components.home import EnvComponent, HomeComponent, SidebarComponent
from components.laboratory import LaboratoryComponent
from config import Colors, image_assets
from copy import deepcopy


class UIHandler:
    def __init__(self):
        self.surface = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        self.surface.fill((26, 26, 26))
        pygame.display.set_caption("DARWIN")

        self.screen_states = {
            "current_screen": "home",
            "screens": ["home", "laboratory"],
            "home": {
                "components": {
                    "env": {
                        "handler": EnvComponent,
                        "custom_position": {
                            "topleft": (50, 100),
                        },
                    },
                    "sidebar": {
                        "handler": SidebarComponent,
                        "custom_position": {
                            "topright": (self.surface.get_width() - 50, 50),
                        },
                    },
                    "main": {
                        "handler": HomeComponent,
                        "custom_position": {
                            "topleft": (0, 0),
                        },
                    },
                },
                "context": {},
            },
            "laboratory": {
                "components": {
                    "env": {
                        "handler": LaboratoryComponent,
                        "custom_position": {
                            "center": (
                                self.surface.get_width() // 2,
                                self.surface.get_height() // 2,
                            ),
                        },
                    },
                },
                "context": {},
            },
        }

    def initialize_screen(self, screen="home"):
        self.screen_states["current_screen"] = screen
        self.screen_states["rendered_components"] = {}

        for name, info in self.screen_states[screen]["components"].items():
            rendered_component = info["handler"](
                main_surface=self.surface,
                context=self.screen_states[screen].get("context", {}),
            )
            self.screen_states["rendered_components"][name] = {
                **info,
                "handler": rendered_component,
            }

    def event_handler(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

            for name, info in self.screen_states["rendered_components"].items():
                yield from info["handler"].event_handler(event) or []
    
    def update_screen(self, context=None):
        self.surface.fill((26, 26, 26))

        for name, info in self.screen_states["rendered_components"].items():
            info["handler"].update(context=context)
            rect = info["handler"].surface.get_rect(**info["custom_position"])
            self.surface.blit(info["handler"].surface, dest=rect)

        pygame.display.flip()

    def get_component(self, name):
        return self.screen_states["rendered_components"].get(name)["handler"]
