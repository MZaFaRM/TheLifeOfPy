import os
import random
from creatures import Carnivore, Herbivore, Plant, Terms
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from gymnasium import Env
from gymnasium.spaces import Box, Discrete
import numpy as np


class NatureEnv(Env):
    ANIMALS = []
    PLANTS = []
    COMMUNICATION_BUFFER = {}

    def __init__(self, carnivores: int, herbivores: int, plants: int) -> None:
        self.population_carnivores = carnivores
        self.population_herbivores = herbivores
        self.population_plants = plants

        for i in range(carnivores):
            self.create_animal(Terms.CARNIVORE, f"Carnivore {i}")
        for i in range(herbivores):
            self.create_animal(Terms.HERBIVORE, f"Herbivore {i}")
        for i in range(plants):
            self.create_animal(Terms.PLANT, f"Plant {i}")

        self.observation_space = Discrete(5)
        self.action_space = Discrete(5)

    def assign_model(self, carnivore_model_path=None, herbivore_model_path=None):
        for animal in self.ANIMALS:
            check_env(animal)
            if isinstance(animal, Carnivore):
                if carnivore_model_path:
                    animal.model = PPO.load(carnivore_model_path, env=animal)
                else:
                    animal.model = PPO("MlpPolicy", env=animal)
            elif isinstance(animal, Herbivore):
                if herbivore_model_path:
                    animal.model = PPO.load(herbivore_model_path, env=animal)
                else:
                    animal.model = PPO("MlpPolicy", env=animal)

    def create_animal(self, animal_type: str, name: str, parents=None):
        if animal_type == Terms.CARNIVORE:
            self.ANIMALS.append(
                Carnivore(name, parents=parents, comms=self.COMMUNICATION_BUFFER)
            )
        elif animal_type == Terms.HERBIVORE:
            self.ANIMALS.append(
                Herbivore(name, parents=parents, comms=self.COMMUNICATION_BUFFER)
            )

    def create_plant(self, name: str):
        self.PLANTS.append(Plant(name))

    def step(self, obs):
        observations, rewards, dones, truncations, infos = zip(
            *[animal.step(animal.model.predict(obs)[0]) for animal in self.ANIMALS]
        )
        return (
            np.array(observations),
            np.array(rewards),
            np.array(dones),
            np.array(truncations),
            infos,
        )

    def render(self):
        for animal in self.ANIMALS:
            animal.render()
        for plant in self.PLANTS:
            plant.render()

    def reset(self, seed=None):
        for i in range(self.population_carnivores):
            self.create_animal(Terms.CARNIVORE, f"Carnivore {i}")
        for i in range(self.population_herbivores):
            self.create_animal(Terms.HERBIVORE, f"Herbivore {i}")
        for i in range(self.population_plants):
            self.create_animal(Terms.PLANT, f"Plant {i}")

        observations = [animal.get_observation() for animal in self.ANIMALS] + [
            plant.get_observation() for plant in self.PLANTS
        ]

        return (np.array(observations), {})


env = NatureEnv(1, 1, 1)
env.assign_model(
    # carnivore_model_path=os.path.join("models", "carnivores"),
    # herbivore_model_path=os.path.join("models", "herbivores"),
)

done = False
score = 0
obs, info = env.reset()
# print(evaluate_policy(model, env, n_eval_episodes=100, deterministic=True))

done = False
score = 0
obs, info = env.reset()

dones = [True]

for i in range(5):
    while any(dones):
        obs, reward, terminated, truncated, info = env.step(obs)
        env.render()
    obs, info = env.reset()
