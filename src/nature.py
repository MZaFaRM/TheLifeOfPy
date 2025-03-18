import os
import sys
import pygame

from src.enums import Attributes, EventType, MessagePacket
from src.handlers import genetics
import src.handlers.organisms as organisms
from src.handlers.ui import UIHandler
from src.config import image_assets

class Nature:
    def __init__(self):
        icon = pygame.image.load(os.path.join(image_assets, "icons", "256x256.png"))
        icon = pygame.transform.scale(icon, (32, 32))
        pygame.display.set_icon(icon)
        
        pygame.font.init()
        self.clock = pygame.time.Clock()
        self.ui_handler = UIHandler()
        self.reset()

    def reset(self):
        self.time_steps = 0
        self.done = False
        self.truncated = False
        self.paused = False

        self.ui_handler.initialize_screen(screen="home")
        env_surface = self.ui_handler.get_component(name="EnvComponent").surface
        self.neuron_manager = genetics.NeuronManager()

        self.species = organisms.Species(
            context={
                "env_surface": env_surface,
                "neuron_manager": self.neuron_manager,
            }
        )
        self.forest = organisms.Forest(
            context={
                "env_surface": env_surface,
            }
        )

        self.critters = []
        self.plants = self.forest.bulk_generate_plants_patch(n=20)
        self.population_history = []
        self.fitness_history = []
        self.plant_history = [(0, 0)]
        self.species_colors = {}

    def step(self):
        events = pygame.event.get()
        packet = list(self.ui_handler.event_handler(events))
        if packet:
            packet = packet[0]
            if packet:
                print("Packet: ", str(packet))
            if packet == "pause_time":
                self.paused = True
            elif packet == "play_time":
                self.paused = False
            elif packet == MessagePacket(EventType.NAVIGATION, "home"):
                self.ui_handler.initialize_screen(screen="home")
                if EventType.GENESIS in packet.context:
                    data = packet.context[EventType.GENESIS]
                    self.critters = self.species.create_species(
                        n=data.pop(Attributes.BASE_POPULATION), context=data
                    )
                elif EventType.RESTART_SIMULATION in packet.context:
                    self.reset()

            elif packet == MessagePacket(EventType.NAVIGATION, "laboratory"):
                self.ui_handler.initialize_screen(screen="laboratory")

        if self.paused:
            return self.done, self.truncated

        self.species.step(events)

        self.neuron_manager.update(
            self.species.get_critters(),
            self.forest.get_plants(),
        )

        self.clock.tick(1000)
        self.truncated = False

        if self.time_steps % 75 == 0:
            self.forest.create_plant_patch()

        if self.time_steps % 50 == 0:
            critter_count, fitness, self.species_colors = (
                self.species.get_critter_count()
            )
            self.population_history.append((self.time_steps, critter_count))
            self.fitness_history.append((self.time_steps, fitness))
            self.plant_history.append(
                (self.time_steps + 1, self.forest.get_plant_count())
            )

        self.time_steps += 1
        return self.done, self.truncated
    
    def run(self):
        try:
            self.render()
            while 1 + 1 == 2:
                self.step()
                self.render()
        except KeyboardInterrupt:
            pygame.quit()
            sys.exit(0)
        except Exception as e:
            raise

    def render(self):
        self.ui_handler.update_screen(
            context={
                "critters": self.species.get_critters(),
                "dead_critters": self.species.get_critters(alive=False),
                "population_history": self.population_history,
                "plant_history": self.plant_history,
                "fitness_history": self.fitness_history,
                "species_colors": self.species_colors,
                "time": self.time_steps,
                "paused": self.paused,
                "plants": self.forest.get_plants(),
            }
        )