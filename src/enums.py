from enum import Enum


class NeuronType(Enum):
    SENSOR = "sensor"
    HIDDEN = "hidden"
    ACTUATOR = "actuator"
    BIAS = "bias"

    # Other
    CONN = "connection"


class Defence(Enum):
    NONE = "None"
    SHIELDLING = "Shieldling"
    SWORDLING = "Swordling"
    CAMOUFLING = "Camoufling"


class MatingState(Enum):
    MINOR = "Minor"
    NOT_READY = "Not Ready"
    READY = "Ready"
    MATING = "Mating"
    WAITING = "Waiting"


class SurfDesc(Enum):
    SURFACE = "surface"
    CLICKED_SURFACE = "clicked_surface"
    CURRENT_SURFACE = "current_surface"
    RECT = "rect"
    ABSOLUTE_RECT = "absolute_rect"


class Attributes(Enum):
    BASE_POPULATION = "Base Population"
    SPECIES = "Species"
    POPULATION = "Population"
    ID = "ID"
    POSITION = "Position"
    AGE = "Age"
    ENERGY = "Energy"
    FITNESS = "Fitness"
    DEFENSE_MECHANISM = "Defense Mechanism"
    DOMAIN = "Domain"
    MATING_STATE = "Mating State"
    CHILDREN = "Children"
    VISION_RADIUS = "Vision Radius"
    SIZE = "Size"
    AGE_OF_MATURITY = "Age Of Maturity"
    COLOR = "Color"
    MAX_SPEED = "Max Speed"
    MAX_ENERGY = "Max Energy"
    MAX_LIFESPAN = "Max Lifespan"


class EventType(Enum):
    NAVIGATION = "navigation"
    OTHER = "other"
    GENESIS = "genesis"
    RESTART_SIMULATION = "restart_simulation"


class Shapes(Enum):
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"
    PENTAGON = "pentagon"


class MessagePacket:
    def __init__(
        self,
        msg_type: EventType,
        value: str,
        context: dict | list = None,
    ) -> None:
        self.msg_type = msg_type
        self.value = value
        self.context = context or {}

    def __eq__(self, value):
        try:
            return self.msg_type == value.msg_type and self.value == value.value
        except Exception:
            return False

    def __str__(self):
        return f"{self.msg_type}_{self.value}".lower()

    def __repr__(self):
        return f"Packet(type={self.msg_type.name}, value={self.value}, context={self.context})"
