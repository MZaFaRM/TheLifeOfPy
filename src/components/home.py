import os
import sys

import pygame

from src import helper
from src.config import Colors, Fonts, image_assets
from src.enums import Attributes, EventType, MessagePacket, SurfDesc
from src.handlers.organisms import Counter
import webbrowser
import pygame_chart as pyc


class HomeComponent:
    def __init__(self, main_surface, context=None):
        # screen_width, screen_height = pygame.display.get_surface().get_size()
        screen_width, screen_height = main_surface.get_size()

        self.surface = main_surface
        # self.surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.env_title = pygame.image.load(
            os.path.join(image_assets, "home", "env_title.svg")
        )
        self.env_title_rect = self.env_title.get_rect(topleft=(50, 50))

        self.components = [
            {
                "name": "EnvComponent",
                "handler": EnvComponent,
                "position": {
                    "topleft": (50, 100),
                },
            },
            {
                "name": "SidebarComponent",
                "handler": SidebarComponent,
                "position": {
                    "topright": (self.surface.get_width() - 50, 50),
                },
            },
        ]

        self.time_control_buttons = {
            "pause_time": {
                "name": "pause_time",
                SurfDesc.SURFACE: os.path.join("home", "pause_time_button.svg"),
                SurfDesc.CLICKED_SURFACE: os.path.join(
                    "home", "pause_time_button_clicked.svg"
                ),
                "clicked": False,
                "x_position": 75,
            },
            "play_time": {
                "name": "play_time",
                SurfDesc.SURFACE: os.path.join("home", "play_time_button.svg"),
                SurfDesc.CLICKED_SURFACE: os.path.join(
                    "home", "play_time_button_clicked.svg"
                ),
                "clicked": True,
                "x_position": 125,
            },
        }

        self.close_window_button = pygame.image.load(
            os.path.join(image_assets, "home", "close_window_button.svg")
        )
        self.close_window_button_rect = self.close_window_button.get_rect(
            topright=(screen_width, 0)
        )

        y = screen_height - 75
        for _, button_data in self.time_control_buttons.items():
            default_button = pygame.image.load(
                os.path.join(image_assets, button_data.pop(SurfDesc.SURFACE))
            )
            clicked_button = pygame.image.load(
                os.path.join(image_assets, button_data.pop(SurfDesc.CLICKED_SURFACE))
            )
            button_rect = default_button.get_rect(
                center=(button_data.pop("x_position"), y)
            )

            button_data.update(
                {
                    SurfDesc.SURFACE: {
                        "default": default_button,
                        "clicked": clicked_button,
                    },
                    SurfDesc.RECT: button_rect,
                }
            )

        self.counter_surface = pygame.Surface((300, 35), pygame.SRCALPHA)
        self.counter_font = pygame.font.Font(Fonts.PixelifySansMedium, 35)
        self.counter_rect = self.counter_surface.get_rect(
            topleft=(160, screen_height - 90)
        )

        self._initialize_screen(context)

    def _initialize_screen(self, context):
        for component in self.components:
            rendered_component = component["handler"](
                main_surface=self.surface,
                context=context,
            )
            component["rendered_handler"] = rendered_component

    def event_handler(self, event):
        if event.type == pygame.MOUSEBUTTONUP:
            if self.close_window_button_rect.collidepoint(event.pos):
                pygame.quit()
                sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            for button, button_data in self.time_control_buttons.items():
                if button_data[SurfDesc.RECT].collidepoint(event.pos):
                    button_data["clicked"] = True
                    for other_button in self.time_control_buttons:
                        if other_button != button:
                            self.time_control_buttons[other_button]["clicked"] = False
                    return button

        return next(
            filter(
                lambda packet: packet is not None,
                (
                    component["rendered_handler"].event_handler(event)
                    for component in self.components
                ),
            ),
            None,
        )

    def update(self, context=None):
        if context.get("paused"):
            self.time_control_buttons["pause_time"]["clicked"] = True
            self.time_control_buttons["play_time"]["clicked"] = False
        else:
            self.time_control_buttons["pause_time"]["clicked"] = False
            self.time_control_buttons["play_time"]["clicked"] = True

        for component in self.components:
            component["rendered_handler"].update(context=context)
            rect = component["rendered_handler"].surface.get_rect(
                **component["position"]
            )
            self.surface.blit(component["rendered_handler"].surface, dest=rect)

        self.surface.blit(self.close_window_button, self.close_window_button_rect)
        self.surface.blit(self.env_title, self.env_title_rect)

        for button_data in self.time_control_buttons.values():
            if button_data["clicked"]:
                self.surface.blit(
                    button_data[SurfDesc.SURFACE]["clicked"], button_data[SurfDesc.RECT]
                )
            else:
                self.surface.blit(
                    button_data[SurfDesc.SURFACE]["default"], button_data[SurfDesc.RECT]
                )

        self.counter_surface.fill((0, 0, 0, 0))
        text = self.counter_font.render(f"{context['time']:,} Ts", True, Colors.primary)
        text_rect = text.get_rect(topleft=(0, 0))
        self.counter_surface.blit(text, text_rect)
        self.surface.blit(self.counter_surface, self.counter_rect)


class EnvComponent:
    def __init__(self, main_surface, context=None):
        self.env_image = pygame.image.load(
            os.path.join(image_assets, "home", "dot_grid.svg")
        )
        self.surface = pygame.Surface(
            (self.env_image.get_width(), self.env_image.get_height())
        )
        self.surface.blit(self.env_image, (0, 0))
        self.plants = []
        self.critters = []

    def event_handler(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            pos = (event.pos[0] - 50, event.pos[1] - 100)
            for critter in self.critters:
                if critter.interaction_rect.collidepoint(pos):
                    return MessagePacket(
                        EventType.NAVIGATION,
                        "profile",
                        context={"critter": critter},
                    )

    def update(self, context=None):
        self.plants = context.get("plants")
        self.critters = context.get("critters")

        self.surface.fill(Colors.bg_color)
        self.surface.blit(self.env_image, (0, 0))

        for critter in self.critters:
            critter.draw(self.surface)

        for plant in self.plants:
            plant.draw(self.surface)


class SidebarComponent:
    def __init__(self, main_surface, context=None):
        self.main_surface = main_surface
        self.surface = pygame.Surface((408, 988), pygame.SRCALPHA)

        self.DEFAULT = "default"
        self.SHOW_GRAPHS = "show_graphs"
        self.PROFILE = "profile"

        self.sidebar_screens = {
            SurfDesc.CURRENT_SURFACE: self.DEFAULT,
            "update": True,
            "screens": [self.DEFAULT, self.SHOW_GRAPHS, self.PROFILE],
            self.DEFAULT: {
                "function": self.setup_default_sidebar,
                SurfDesc.SURFACE: pygame.image.load(
                    os.path.join(image_assets, "home", "sidebar.png")
                ),
            },
            self.SHOW_GRAPHS: {
                "function": self.setup_graph_sidebar,
                SurfDesc.SURFACE: pygame.image.load(
                    os.path.join(image_assets, "graphs", "main.svg")
                ),
            },
            self.PROFILE: {
                "function": self.setup_profile_sidebar,
                SurfDesc.SURFACE: pygame.image.load(
                    os.path.join(image_assets, "profile", "main.svg")
                ),
            },
        }

    def setup_profile_sidebar(self, context=None):
        self.surface.blit(self.sidebar_screens[self.PROFILE][SurfDesc.SURFACE], (0, 0))

        # Back button setup
        back_button = pygame.image.load(
            os.path.join(image_assets, "graphs", "back_button.svg")
        )
        back_button_clicked = pygame.image.load(
            os.path.join(image_assets, "graphs", "back_button_clicked.svg")
        )
        back_button_rect = back_button.get_rect(center=(50, 50))

        self.sidebar_screens[self.PROFILE].update(
            {
                "back_button": {
                    SurfDesc.CURRENT_SURFACE: back_button,
                    SurfDesc.SURFACE: back_button,
                    SurfDesc.CLICKED_SURFACE: back_button_clicked,
                    SurfDesc.RECT: back_button_rect,
                },
            }
        )

        critter_data = context.get("selected_critter")
        self.__setup_critter_head(critter_data)

        dynamic_options = {
            Attributes.POPULATION: {},
            Attributes.AGE: {},
            Attributes.ENERGY: {},
            Attributes.POSITION: {},
            Attributes.FITNESS: {},
        }

        self.__setup_options(critter_data, dynamic_options)

        self.sidebar_screens[self.PROFILE].update(
            {
                "critter_id": critter_data.get(Attributes.ID),
                "dynamic_options": dynamic_options,
            }
        )

    def __setup_options(self, critter_data, dynamic_options):
        y = 430
        options_x = 35
        value_x = 35 + 150

        for key in [
            Attributes.AGE,
            Attributes.POPULATION,
            Attributes.ENERGY,
            Attributes.POSITION,
            Attributes.FITNESS,
            Attributes.DOMAIN,
            Attributes.AGE_OF_MATURITY,
            Attributes.DEFENSE_MECHANISM,
            Attributes.VISION_RADIUS,
            Attributes.SIZE,
            Attributes.COLOR,
            Attributes.MAX_SPEED,
            Attributes.MAX_ENERGY,
            Attributes.MAX_LIFESPAN,
        ]:
            value = critter_data.get(key, None)
            key_surface = pygame.font.Font(Fonts.PixelifySans, 18).render(
                helper.limit_text_size(key.value, 14), True, Colors.bg_color
            )
            key_rect = key_surface.get_rect(topleft=(options_x, y))

            value_surface = pygame.Surface(
                (self.surface.get_width() - 225, 30), pygame.SRCALPHA
            )
            value_rect = value_surface.get_rect(topleft=(value_x, y - 10))
            value_surface.fill(Colors.bg_color)

            if key in dynamic_options:
                dynamic_options[key].update(
                    {
                        SurfDesc.SURFACE: value_surface,
                        SurfDesc.RECT: value_rect,
                    }
                )

            value_text_surface = pygame.font.Font(Fonts.PixelifySans, 18).render(
                str(value), True, Colors.primary
            )
            value_surface.blit(value_text_surface, (10, 5))

            self.surface.blit(key_surface, key_rect)
            self.surface.blit(value_surface, value_rect)

            y += 35

    def __setup_critter_head(self, critter_data):
        species = critter_data.get(Attributes.SPECIES)
        species_name_surface = pygame.font.Font(Fonts.PixelifySansBold, 30).render(
            species, True, Colors.bg_color
        )
        species_name_rect = species_name_surface.get_rect(topleft=(35, 320))
        self.surface.blit(species_name_surface, species_name_rect)

        critter_id = str(critter_data.get(Attributes.ID)).upper()
        y = 360
        for text in helper.split_word(critter_id, 30):
            critter_id_surface = pygame.font.Font(Fonts.PixelifySans, 18).render(
                text, True, Colors.bg_color
            )
            critter_id_rect = critter_id_surface.get_rect(topleft=(35, y))
            self.surface.blit(critter_id_surface, critter_id_rect)
            y += 22

    def setup_graph_sidebar(self, context=None):
        self.surface.blit(
            self.sidebar_screens[self.SHOW_GRAPHS][SurfDesc.SURFACE], (0, 0)
        )

        # Back button setup
        back_button = pygame.image.load(
            os.path.join(image_assets, "graphs", "back_button.svg")
        )
        back_button_clicked = pygame.image.load(
            os.path.join(image_assets, "graphs", "back_button_clicked.svg")
        )
        back_button_rect = back_button.get_rect(center=(50, 50))

        # Create Population Graph Figure
        population_figure = pyc.Figure(
            self.surface, 15, 120, 380, 200, bg_color=Colors.white
        )
        fitness_figure = pyc.Figure(
            self.surface, 15, 375, 380, 200, bg_color=Colors.white
        )
        plant_abundance_figure = pyc.Figure(
            self.surface, 15, 630, 380, 200, bg_color=Colors.white
        )

        self.sidebar_screens[self.SHOW_GRAPHS].update(
            {
                "back_button": {
                    SurfDesc.CURRENT_SURFACE: back_button,
                    SurfDesc.SURFACE: back_button,
                    SurfDesc.CLICKED_SURFACE: back_button_clicked,
                    SurfDesc.RECT: back_button_rect,
                },
                "population_graph": population_figure,
                "fitness_graph": fitness_figure,
                "plant_abundance_graph": plant_abundance_figure,
            }
        )

    def setup_default_sidebar(self, context=None):
        self.surface.blit(self.sidebar_screens[self.DEFAULT][SurfDesc.SURFACE], (0, 0))

        self.sidebar_screens[self.DEFAULT].update(
            {
                "alive_counter": Counter(),
                "dead_counter": Counter(),
            }
        )

        # For button click checks
        self.surface_x = self.main_surface.get_width() - self.surface.get_width() - 50
        self.surface_y = 50

        sidebar_window_width = self.surface.get_width()
        sidebar_window_height = self.surface.get_height()

        sidebar_center = sidebar_window_width // 2
        self.buttons = {
            "create_organism": {
                "name": "create_organism",
                SurfDesc.CURRENT_SURFACE: None,
                SurfDesc.SURFACE: os.path.join("home", "create_organism_button.svg"),
                SurfDesc.CLICKED_SURFACE: os.path.join(
                    "home", "create_organism_button_clicked.svg"
                ),
                "position": (sidebar_center, 725),
            },
            "restart_simulation": {
                "name": "restart_simulation",
                SurfDesc.CURRENT_SURFACE: None,
                SurfDesc.SURFACE: os.path.join("home", "restart_simulation_button.svg"),
                SurfDesc.CLICKED_SURFACE: os.path.join(
                    "home", "restart_simulation_button_clicked.svg"
                ),
                "position": (sidebar_center, 785),
            },
            "show_graphs": {
                "name": "show_graphs",
                SurfDesc.CURRENT_SURFACE: None,
                SurfDesc.SURFACE: os.path.join("home", "show_graphs_button.svg"),
                SurfDesc.CLICKED_SURFACE: os.path.join(
                    "home", "show_graphs_button_clicked.svg"
                ),
                "position": (sidebar_center, 845),
            },
            "docs": {
                "name": "docs",
                SurfDesc.CURRENT_SURFACE: None,
                SurfDesc.SURFACE: os.path.join("home", "docs_button.svg"),
                SurfDesc.CLICKED_SURFACE: os.path.join(
                    "home", "docs_button_clicked.svg"
                ),
                "position": (122, 905),
            },
            "github": {
                "name": "github",
                SurfDesc.CURRENT_SURFACE: None,
                SurfDesc.SURFACE: os.path.join("home", "github_button.svg"),
                SurfDesc.CLICKED_SURFACE: os.path.join(
                    "home", "github_button_clicked.svg"
                ),
                "position": (287, 905),
            },
        }

        # Load, position, and blit each button
        for button in self.buttons.values():
            self.load_and_store_button(
                name=button["name"],
                image=button[SurfDesc.SURFACE],
                clicked_image=button[SurfDesc.CLICKED_SURFACE],
                position=button.pop("position"),
            )

    def event_handler(self, event):
        if event.type in [pygame.MOUSEBUTTONUP, pygame.MOUSEBUTTONDOWN]:
            # Get mouse position relative to the sidebar
            mouse_x, mouse_y = event.pos
            rel_x, rel_y = mouse_x - self.surface_x, mouse_y - self.surface_y
            if self.sidebar_screens[SurfDesc.CURRENT_SURFACE] == self.DEFAULT:
                return self.handle_default_sidebar_event(event, rel_x, rel_y)
            elif self.sidebar_screens[SurfDesc.CURRENT_SURFACE] == self.SHOW_GRAPHS:
                return self.handle_graphs_sidebar_event(event, rel_x, rel_y)
            elif self.sidebar_screens[SurfDesc.CURRENT_SURFACE] == self.PROFILE:
                return self.handle_profile_sidebar_event(event, rel_x, rel_y)

    def handle_graphs_sidebar_event(self, event, rel_x, rel_y):
        self.sidebar_screens[self.SHOW_GRAPHS]["back_button"][
            SurfDesc.CURRENT_SURFACE
        ] = self.sidebar_screens[self.SHOW_GRAPHS]["back_button"][SurfDesc.SURFACE]

        if self.sidebar_screens[self.SHOW_GRAPHS]["back_button"][
            SurfDesc.RECT
        ].collidepoint((rel_x, rel_y)):
            if event.type == pygame.MOUSEBUTTONDOWN:
                self.sidebar_screens[self.SHOW_GRAPHS]["back_button"][
                    SurfDesc.CURRENT_SURFACE
                ] = self.sidebar_screens[self.SHOW_GRAPHS]["back_button"][
                    SurfDesc.CLICKED_SURFACE
                ]
            elif event.type == pygame.MOUSEBUTTONUP:
                self.sidebar_screens[SurfDesc.CURRENT_SURFACE] = self.DEFAULT
                self.sidebar_screens["update"] = True

    def handle_default_sidebar_event(self, event, rel_x, rel_y):
        for name in [
            "create_organism",
            "restart_simulation",
            "show_graphs",
            "docs",
            "github",
        ]:
            # Reset button to default
            self.buttons[name][SurfDesc.CURRENT_SURFACE] = self.buttons[name][
                SurfDesc.SURFACE
            ]

        # Check if the mouse is within the bounds of the button
        if self.buttons["create_organism"][SurfDesc.RECT].collidepoint((rel_x, rel_y)):
            if event.type == pygame.MOUSEBUTTONDOWN:
                button = self.buttons["create_organism"]
                button[SurfDesc.CURRENT_SURFACE] = button[SurfDesc.CLICKED_SURFACE]
            elif event.type == pygame.MOUSEBUTTONUP:
                return MessagePacket(
                    EventType.NAVIGATION,
                    "laboratory",
                )
        elif self.buttons["restart_simulation"][SurfDesc.RECT].collidepoint(
            (rel_x, rel_y)
        ):
            if event.type == pygame.MOUSEBUTTONDOWN:
                button = self.buttons["restart_simulation"]
                button[SurfDesc.CURRENT_SURFACE] = button[SurfDesc.CLICKED_SURFACE]
            elif event.type == pygame.MOUSEBUTTONUP:
                return MessagePacket(
                    EventType.NAVIGATION,
                    "home",
                    context={EventType.RESTART_SIMULATION: True},
                )
        elif self.buttons["show_graphs"][SurfDesc.RECT].collidepoint((rel_x, rel_y)):
            if event.type == pygame.MOUSEBUTTONDOWN:
                button = self.buttons["show_graphs"]
                button[SurfDesc.CURRENT_SURFACE] = button[SurfDesc.CLICKED_SURFACE]
            elif event.type == pygame.MOUSEBUTTONUP:
                self.sidebar_screens[SurfDesc.CURRENT_SURFACE] = self.SHOW_GRAPHS
                self.sidebar_screens["update"] = True

        elif self.buttons["docs"][SurfDesc.RECT].collidepoint((rel_x, rel_y)):
            if event.type == pygame.MOUSEBUTTONDOWN:
                button = self.buttons["docs"]
                button[SurfDesc.CURRENT_SURFACE] = button[SurfDesc.CLICKED_SURFACE]
            elif event.type == pygame.MOUSEBUTTONUP:
                webbrowser.open("https://github.com/MZaFaRM/PetriPixel/wiki/1.-Home")
        elif self.buttons["github"][SurfDesc.RECT].collidepoint((rel_x, rel_y)):
            if event.type == pygame.MOUSEBUTTONDOWN:
                button = self.buttons["github"]
                button[SurfDesc.CURRENT_SURFACE] = button[SurfDesc.CLICKED_SURFACE]
            elif event.type == pygame.MOUSEBUTTONUP:
                webbrowser.open("https://github.com/MZaFaRM/PetriPixel")

    def handle_profile_sidebar_event(self, event, rel_x, rel_y):
        back_button = self.sidebar_screens[self.PROFILE]["back_button"]
        back_button[SurfDesc.CURRENT_SURFACE] = back_button[SurfDesc.SURFACE]

        if back_button[SurfDesc.RECT].collidepoint((rel_x, rel_y)):
            if event.type == pygame.MOUSEBUTTONDOWN:
                back_button[SurfDesc.CURRENT_SURFACE] = back_button[
                    SurfDesc.CLICKED_SURFACE
                ]
            elif event.type == pygame.MOUSEBUTTONUP:
                self.sidebar_screens[SurfDesc.CURRENT_SURFACE] = self.DEFAULT
                self.sidebar_screens["update"] = True
                return MessagePacket(EventType.CRITTER, "unselect_critter")

    def load_and_store_button(self, name, image, clicked_image, position):
        button_image = pygame.image.load(os.path.join(image_assets, image))
        clicked_button_image = pygame.image.load(
            os.path.join(image_assets, clicked_image)
        )
        button_rect = button_image.get_rect(center=position)
        # Blit button to the sidebar
        self.surface.blit(button_image, button_rect)
        # Store button's image and rect in a dictionary for later reference
        self.buttons[name].update(
            {
                SurfDesc.CURRENT_SURFACE: button_image,
                SurfDesc.SURFACE: button_image,
                SurfDesc.RECT: button_rect,
                SurfDesc.CLICKED_SURFACE: clicked_button_image,
            }
        )

    def update(self, context=None):
        if context.get("selected_critter", None) is not None:
            if self.sidebar_screens[SurfDesc.CURRENT_SURFACE] != self.PROFILE:
                self.sidebar_screens[self.PROFILE]["function"](context=context)
                self.sidebar_screens[SurfDesc.CURRENT_SURFACE] = self.PROFILE
            else:
                self.update_profile_sidebar(context)

        elif self.sidebar_screens[SurfDesc.CURRENT_SURFACE] == self.SHOW_GRAPHS:
            if self.sidebar_screens["update"]:
                self.sidebar_screens[self.SHOW_GRAPHS]["function"]()
                self.sidebar_screens["update"] = False
            self.update_graph_sidebar(context)
        else:
            if self.sidebar_screens["update"]:
                self.sidebar_screens[self.DEFAULT]["function"]()
                self.sidebar_screens["update"] = False
            self.update_default_sidebar(context)

    def update_default_sidebar(self, context):
        alive = len(context.get("critters"))
        dead = len(context.get("dead_critters"))

        alive_counter = self.sidebar_screens[self.DEFAULT]["alive_counter"]
        dead_counter = self.sidebar_screens[self.DEFAULT]["dead_counter"]

        alive_counter.draw(value=alive)
        dead_counter.draw(value=dead)

        self.surface.blit(alive_counter.surface, (115, 325))
        self.surface.blit(dead_counter.surface, (290, 325))

        for button in self.buttons.values():
            self.surface.blit(button[SurfDesc.CURRENT_SURFACE], button[SurfDesc.RECT])

    def update_graph_sidebar(self, context):
        back_button = self.sidebar_screens[self.SHOW_GRAPHS]["back_button"]
        self.surface.blit(
            back_button[SurfDesc.CURRENT_SURFACE], back_button[SurfDesc.RECT]
        )

        self.update_population_graph(context)
        self.update_fitness_graph(context)
        self.update_plant_abundance_graph(context)

    def update_population_graph(self, context):
        figure = self.sidebar_screens[self.SHOW_GRAPHS].get("population_graph")
        population_history = context.get("population_history", [])
        species_colors = context.get("species_colors", {})

        time_steps, critter_counts = zip(*population_history)
        time_steps = list(time_steps)

        # Extract total population
        total_population = [c["total"] for c in critter_counts]
        if sum(total_population) == 0:
            return  # No data, don't attempt to draw

        species_keys = {
            species for c in critter_counts for species in c if species != "total"
        }

        figure.chart_names = []
        figure.charts = []

        # Plot total population
        figure.line(
            "Total Population", time_steps, total_population, color=Colors.bg_color
        )

        # Plot each species separately
        for species in species_keys:
            species_population = [c.get(species, 0) for c in critter_counts]
            species_color = species_colors.get(
                species, (255, 255, 255)
            )  # Default white if not found
            figure.line(
                f"Species {species}",
                time_steps,
                species_population,
                color=species_color,
            )

        figure.draw()

    def update_fitness_graph(self, context):
        figure = self.sidebar_screens[self.SHOW_GRAPHS].get("fitness_graph")
        fitness_history = context.get("fitness_history", [])
        time_steps, fitness_values = zip(*fitness_history)

        time_steps = list(time_steps)
        total_fitness = [f["total"] for f in fitness_values]
        if sum(total_fitness) == 0:
            return

        species_keys = {
            species for f in fitness_values for species in f if species != "total"
        }

        figure.chart_names = []
        figure.charts = []

        figure.line("Total Fitness", time_steps, total_fitness, color=Colors.bg_color)

        for species in species_keys:
            species_fitness = [f.get(species, 0) for f in fitness_values]
            species_color = context.get("species_colors", {}).get(
                species, (255, 255, 255)
            )
            figure.line(
                f"Species {species}", time_steps, species_fitness, color=species_color
            )

        figure.draw()

    def update_plant_abundance_graph(self, context):
        figure = self.sidebar_screens[self.SHOW_GRAPHS].get("plant_abundance_graph")
        time_steps, population_values = map(list, zip(*context.get("plant_history")))

        figure.chart_names = []
        figure.charts = []

        figure.line(
            "Plant Abundance", time_steps, population_values, color=Colors.bg_color
        )
        figure.draw()

    def update_profile_sidebar(self, context):
        # TODO: Clean this
        critter_data = context.get("selected_critter")
        if critter_data.get(Attributes.ID) != self.sidebar_screens[self.PROFILE]["critter_id"]:
            self.setup_profile_sidebar(context)
            return

        back_button = self.sidebar_screens[self.PROFILE]["back_button"]
        self.surface.blit(
            back_button[SurfDesc.CURRENT_SURFACE], back_button[SurfDesc.RECT]
        )

        dynamic_options = self.sidebar_screens[self.PROFILE].get(
            "dynamic_options"
        )
        for key, value in critter_data.items():
            if key not in dynamic_options:
                continue
            value_surface = dynamic_options[key][SurfDesc.SURFACE]
            value_rect = dynamic_options[key][SurfDesc.RECT]
            value_surface.fill(Colors.bg_color)

            value_text_surface = pygame.font.Font(Fonts.PixelifySans, 18).render(
                str(value), True, Colors.primary
            )
            value_surface.blit(value_text_surface, (10, 5))

            self.surface.blit(value_surface, value_rect)
