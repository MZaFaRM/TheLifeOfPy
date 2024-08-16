import enum
from gymnasium.spaces import Discrete
from gymnasium import Env
from uuid import uuid4


class Terms(enum.Enum):
    HERBIVORE = "Herbivore"
    CARNIVORE = "Carnivore"
    PLANT = "Plant"

    MATING_CALL = "Mating Call"


class Animal(Env):
    def __init__(self, name="Animal", parents=None, comms=None) -> None:
        self.id = uuid4()
        print("Animal created named:", name)
        self.name = name
        self.satiation = 5
        self.capacity = 3
        self.rest = 10

        self.comms = comms

        self.max_satiation = 5
        self.max_capacity = 3
        self.max_rest = 10

        self.alive = True
        self.sleeping = False

        self.action_space = Discrete(5)
        self.observation_space = Discrete(5)

        self.life_span = 100

        if parents is not None:
            self.parents = parents
        else:
            self.parents = []

    def __str__(self) -> str:
        return self.name

    def __repr__(self) -> str:
        return self.name

    def step(self, action):
        self.life_span -= 1
        self.action = action
        reward = 0

        # - Eat Food
        # - Collect Food
        # - Sleep
        # - Do nothing
        # - Reproduce

        # if action successfully executed
        if action == 0:
            if self.satiation >= self.max_satiation:
                reward -= 1
            else:
                self.satiation = 6
                reward += 5

        elif action == 1:
            if self.capacity > 0:
                self.capacity -= 1
                reward += 5
            else:
                reward -= 1

        elif action == 2:
            if self.rest >= self.max_rest:
                reward -= 1
            else:
                self.rest = 11
                reward += 5

        elif action == 3:
            self.rest += 2
            reward += 0

        elif action == 4:
            self.rest -= 1
            # self.comms[Terms.MATING_CALL] = self.comms.get(Terms.MATING_CALL, [])

            reward += 5

        self.rest = max(0, self.rest - 1)

        if self.life_span % 3 == 0:
            self.satiation = max(0, self.satiation - 1)

        if self.rest == 0:
            self.rest = 11
            self.sleep()
            reward -= 10

        if self.satiation == 0:
            self.alive = False
            reward -= 20
            self.die(reason="Hunger")

        if self.life_span <= 0:
            self.alive = False
            self.die(reason="Old Age")
        # observation, reward, done, truncated, info
        return self.get_observation(), reward, not self.alive, self.life_span <= 0, {}

    def render(self):
        if self.action == 0:
            self.eat()
        elif self.action == 1:
            self.collect_food()
        elif self.action == 2:
            self.sleep()
        elif self.action == 3:
            self.do_nothing()
        elif self.action == 4:
            self.reproduce()

    def get_observation(self):
        return 3

    def reset(self, seed=None):
        return 4, {}

    def eat(self):
        print(f"{self.name} is eating")

    def collect_food(self):
        print(f"{self.name} is collecting food")

    def sleep(self):
        print(f"{self.name} is sleeping")

    def do_nothing(self):
        print(f"{self.name} is doing nothing")

    def reproduce(self):
        print(f"{self.name} is reproducing")

    def die(self, reason: str = "Unknown"):
        print(f"{self.name} is dead. Reason: {reason}")

    def walk(self, position):
        print(f"{self.name} is walking to position {position}")


class Herbivore(Animal):
    def eat(self):
        print(f"{self.name} is eating")

    def collect_food(self):
        print(f"{self.name} is collecting food")

    def sleep(self):
        print(f"{self.name} is sleeping")

    def do_nothing(self):
        print(f"{self.name} is doing nothing")

    def reproduce(self):
        print(f"{self.name} is reproducing")

    def walk(self, position):
        print(f"{self.name} is walking to position {position}")


class Carnivore(Animal):
    def eat(self):
        print(f"{self.name} is eating")

    def collect_food(self):
        print(f"{self.name} is collecting food")

    def sleep(self):
        print(f"{self.name} is sleeping")

    def do_nothing(self):
        print(f"{self.name} is doing nothing")

    def reproduce(self):
        print(f"{self.name} is reproducing")

    def walk(self, position):
        print(f"{self.name} is walking to position {position}")


class Plant:
    def __init__(self, name) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name

    def get_observation(self):
        return 5
