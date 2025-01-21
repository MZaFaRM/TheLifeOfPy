import numpy as np
import pygame
from gym.spaces import MultiDiscrete

import agents
from enums import EventType, MessagePacket
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

        self.action_space = MultiDiscrete([3, 3])
        self.observation_space = None

        self.truncation = 1_000_000

        # self.graph_manager = PopulationPlot([1, 2], 200)
        self.ui_handler.initialize_screen(screen="home")
        env_surface = self.ui_handler.get_component(name="env").surface
        self.neuron_manager = genetics.NeuronManager()

        self.creature_manager = organisms.Species(
            context={
                "env_surface": env_surface,
                "neuron_manager": self.neuron_manager,
            }
        )
        self.plant_manager = organisms.PlantManager(
            context={
                "env_surface": env_surface,
            }
        )
        self.creatures = []
        self.plants = self.plant_manager.bulk_generate_plants_patch(n=20)

    def remove_food(self, position):
        for plant in self.plant_manager.get_plants():
            if plant.rect.collidepoint(position):
                self.plant_manager.remove_plant(plant)
                return True
        return False

    def step(self):
        reward = 0

        events = pygame.event.get()
        packet = list(self.ui_handler.event_handler(events))
        self.time_steps += 1
        if packet:
            packet = packet[0]
            print("Packet: ", str(packet))
            if "pause_time" == packet:
                self.paused = True
            if "play_time" == packet:
                self.paused = False
            if MessagePacket(EventType.NAVIGATION, "home") == packet:
                self.paused = False
                self.ui_handler.initialize_screen(screen="home")

                if EventType.GENESIS in packet.context:
                    data = packet.context[EventType.GENESIS]
                    self.creatures = self.creature_manager.generate_creatures(
                        n=data.pop("base_pop"), context=data
                    )

            if packet == MessagePacket(EventType.NAVIGATION, "laboratory"):
                self.paused = True
                self.ui_handler.initialize_screen(screen="laboratory")

        if self.paused:
            return self.get_observation(), reward, self.done, self.truncated

        self.neuron_manager.update(self.creatures, self.plants)

        # Batch all steps before rendering
        for creature in self.creatures:
            creature.step()

        # self.graph_manager.update_population(self.time_steps, creature_data)
        self.clock.tick(1000)
        # self.done = all(creature.done for creature in creatures)
        self.truncated = False  # or len(self.creatures) == 0

        if self.time_steps % 75 == 0:
            self.plant_manager.create_plant_patch()

        return self.get_observation(), reward, self.done, self.truncated

    def render(self):
        self.ui_handler.update_screen(
            context={
                "creatures": self.creature_manager.get_creatures(),
                "plants": self.plant_manager.get_plants(),
            }
        )

    def get_observation(self):
        return None


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
