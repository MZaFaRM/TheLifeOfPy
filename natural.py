import os
import random
import time
from creatures import Carnivore, Herbivore, Plant, Terms
from stable_baselines3 import PPO
from stable_baselines3.common.env_checker import check_env
from gymnasium import Env
from gymnasium.spaces import Box, Discrete
import numpy as np


class NatureEnv(Env):
    ANIMALS = []
    PLANTS = []
    DEAD_ANIMALS = []
    COMMUNICATION_BUFFER = {}

    def __init__(
        self,
        carnivores: int,
        herbivores: int,
        plants: int,
        carnivore_model_path: str = None,
        herbivore_model_path: str = None,
    ) -> None:
        self.population_carnivores = carnivores
        self.population_herbivores = herbivores
        self.population_plants = plants

        self.carnivore_model_path = carnivore_model_path
        self.herbivore_model_path = herbivore_model_path

        self.observation_space = Discrete(5)
        self.action_space = Discrete(5)

    def assign_model(self):
        for animal in self.ANIMALS:
            if isinstance(animal, Carnivore):
                if self.carnivore_model_path:
                    animal.model = PPO.load(self.carnivore_model_path, env=animal)
                else:
                    animal.model = PPO("MlpPolicy", env=animal)
            elif isinstance(animal, Herbivore):
                if self.herbivore_model_path:
                    animal.model = PPO.load(self.herbivore_model_path, env=animal)
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
        observations = []
        rewards = []
        terminations = []
        truncations = []
        infos = []

        n = len(self.ANIMALS)
        i = 0

        while i < n:
            action, _ = self.ANIMALS[i].model.predict(obs[i])
            observation, reward, done, truncated, info = self.ANIMALS[i].step(action)

            observations.append(observation)
            rewards.append(reward)
            terminations.append(done)
            truncations.append(truncated)
            infos.append(info)

            if done or truncated:
                self.DEAD_ANIMALS.append(self.ANIMALS.pop(i))
                n -= 1
            else:
                i += 1

        return (
            np.array(observations),
            np.array(rewards),
            np.array(terminations),
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

        observations = [animal.get_observation() for animal in self.ANIMALS]

        self.assign_model()

        return (np.array(observations), {})


env = NatureEnv(
    carnivores=1,
    herbivores=1,
    plants=1,
    # carnivore_model_path=os.path.join("models", "carnivores"),
    # herbivore_model_path=os.path.join("models", "herbivores"),
)

done = False
score = 0
obs, infos = env.reset()
# print(evaluate_policy(model, env, n_eval_episodes=100, deterministic=True))

for i in range(1):
    while not done:
        obs, rewards, terminations, truncations, infos = env.step(obs)
        if all(truncations) or all(terminations):
            done = True

        env.render()
    obs, infos = env.reset()
