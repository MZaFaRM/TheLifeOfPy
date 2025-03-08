import numpy as np
import pygame
from gym.spaces import MultiDiscrete

import agents
from enums import Attributes, EventType, MessagePacket
from handlers import genetics
import handlers.organisms as organisms
from handlers.ui import UIHandler


class Nature:
    def __init__(self):
        pygame.font.init()

        self.clock = pygame.time.Clock()

        self.time_steps = 0
        self.done = False
        self.truncated = False
        self.paused = False

        self.ui_handler = UIHandler()

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

    def step(self):
        reward = 0

        events = pygame.event.get()
        packet = list(self.ui_handler.event_handler(events))
        self.time_steps += 1
        if packet:
            packet = packet[0]
            if packet:
                print("Packet: ", str(packet))
            if packet == "pause_time":
                self.paused = True
            elif packet == "play_time":
                self.paused = False
            elif packet == MessagePacket(EventType.NAVIGATION, "home"):
                self.paused = False
                self.ui_handler.initialize_screen(screen="home")
                if EventType.GENESIS in packet.context:
                    data = packet.context[EventType.GENESIS]
                    self.critters = self.species.create_species(
                        n=data.pop(Attributes.BASE_POPULATION), context=data
                    )
            elif packet == MessagePacket(EventType.NAVIGATION, "laboratory"):
                self.ui_handler.initialize_screen(screen="laboratory")

        if self.paused:
            return reward, self.done, self.truncated

        self.neuron_manager.update(self.critters, self.plants)

        # self.graph_manager.update_population(self.time_steps, critter_data)
        self.clock.tick(1000)
        # self.done = all(critter.done for critter in critters)
        self.truncated = False  # or len(self.critters) == 0
        if self.critters and all(critter.done for critter in self.critters):
            max_fitness = max([critter.fitness for critter in self.critters])
            print(f"Max fitness: {max_fitness}")
            min_fitness = min([critter.fitness for critter in self.critters])
            print(f"Min fitness: {min_fitness}")
            return

        if self.time_steps % 75 == 0:
            self.forest.create_plant_patch()

        return reward, self.done, self.truncated

    def render(self):
        self.ui_handler.update_screen(
            context={
                "critters": self.species.get_critters(),
                "plants": self.forest.get_plants(),
            }
        )


try:
    env = Nature()

    # while True:
    env.render()
    done = False
    truncated = False

    while 1 + 1 == 2:
        env.step()
        env.render()

        # if truncated:
        #     break
except KeyboardInterrupt:
    pygame.quit()
    quit()
except Exception as e:
    raise e
