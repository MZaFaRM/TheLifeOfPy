from enum import Enum


class Base(Enum):
    food = "food"

    # Vision States
    found = "found"
    looking = "looking"

    # Mating States
    not_ready = "not_ready"
    ready = "ready"
    mating = "mating"