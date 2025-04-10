import random
from uuid import uuid4

import pygame
from pygame.sprite import Sprite

from src import config
import src.helper as helper
from src.enums import Attributes, Defence, EventType, MessagePacket, Shapes, MatingState
from src.handlers.genetics import Genome


class Critter(Sprite):
    def __init__(self, surface, context):
        # Unique ID and inheritance setup
        self.id = uuid4()
        super().__init__()

        # Backup context for crossover
        self.creation_context = context

        # Retrieve context-based properties
        position = context.get("position", None)
        parents = context.get("parents", None)

        # Genetic & species attributes
        self.genome = Genome(context.get("genome"))
        self.species = context.get(Attributes.SPECIES)
        self.domain = context.get(Attributes.DOMAIN)

        # Physical properties
        self.color = context.get(Attributes.COLOR)
        self.size = context.get(Attributes.SIZE)
        self.max_speed = context.get(Attributes.MAX_SPEED)
        self.max_energy = context.get(Attributes.MAX_ENERGY)

        # Defense mechanism
        self.defense_active = False
        self.defense_mechanism = context.get(Attributes.DEFENSE_MECHANISM)

        # Vision-related properties
        self.vision = {"radius": context.get(Attributes.VISION_RADIUS, 40)}

        # Visual representation
        self.colors = {
            "alive": self.color,
            "dead": (0, 0, 0),
            "reproducing": (255, 255, 255),
        }
        self.border = {
            Attributes.COLOR: (100, 57, 255),
            "thickness": 2.5,
        }

        # Lifecycle properties
        self.alive = True
        self.age = 0
        self.time = 0
        self.max_lifespan = context.get(Attributes.MAX_LIFESPAN)
        self.energy = self.max_energy
        self.fitness = 0

        # Mating properties
        self.FETUS = None
        self.mating_timeout = 300
        self.current_mating_timeout = 0
        self.mating_state = MatingState.NOT_READY
        self.age_of_maturity = context.get(Attributes.AGE_OF_MATURITY)
        self.mate = None
        self.incoming_mate_request = None
        self.outgoing_mate_request = None

        # Movement properties
        self.td = random.randint(0, 1000)  # for pnoise generation
        self.angle = 0  # degrees
        self.rotation = 0  # degrees
        self.max_speed = context.get(Attributes.MAX_SPEED)

        # Environment setup
        self.env_surface = surface
        self.seed = random.randint(0, 1000)
        self.parents = parents
        self.done = False

        # Positioning & visual rendering
        surface_size = (
            self.size + self.border["thickness"] + (2 * self.vision["radius"])
        )
        self.image = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        self.defense_image = self.image.copy()

        # Center calculation
        self.center = (surface_size // 2, surface_size // 2)

        # Rect & collision setup
        self.rect = self.image.get_rect()
        self.rect.center = position or helper.get_random_position(surface)
        self.interaction_rect = self.rect.inflate(
            (-2 * self.vision["radius"]) + 10,
            (-2 * self.vision["radius"]) + 10,
        )
        self.body_rect = self.rect.inflate(
            -2 * self.vision["radius"] + 10,
            -2 * self.vision["radius"] + 10,
        )
        self.body_rect.center = self.center
        self.previous_position = self.rect.center

    def draw(self, surface):
        if not self.alive:
            return

        if self.time > 1:
            if self.defense_active:
                return surface.blit(self.defense_image, self.rect)
            else:
                return surface.blit(self.image, self.rect)

        color = self.color

        self.body_rect = pygame.Rect(0, 0, self.size, self.size)
        self.body_rect.center = self.center

        # temporary rect used to draw defense mechanism
        defense_rect = self.body_rect.inflate(20, 20)

        # Defense mechanism
        if self.defense_mechanism == Defence.SWORDLING:
            square_1 = helper.get_square_points(defense_rect)
            square_2 = helper.get_square_points(defense_rect, 45)
            pygame.draw.polygon(self.defense_image, (125, 28, 74, 180), square_1)
            pygame.draw.polygon(self.defense_image, (125, 28, 74, 180), square_2)
        elif self.defense_mechanism == Defence.SHIELDLING:
            pygame.draw.rect(
                self.defense_image,
                (255, 255, 255),
                defense_rect.inflate(-10, -10),
                3,
            )
        elif self.defense_mechanism == Defence.CAMOUFLING:
            color = (color[0], color[1], color[2], int(0.2 * 255))

        # Critter
        for image_surface in [self.image, self.defense_image]:
            if self.domain == Shapes.CIRCLE:
                pygame.draw.circle(image_surface, color, self.center, self.size // 2)
            elif self.domain == Shapes.SQUARE:
                pygame.draw.rect(image_surface, color, self.body_rect)
            elif self.domain == Shapes.TRIANGLE:
                points = helper.get_triangle_points(self.body_rect)
                pygame.draw.polygon(image_surface, color, points)
            elif self.domain == Shapes.PENTAGON:
                points = helper.get_pentagon_points(self.body_rect)
                pygame.draw.polygon(image_surface, color, points)

        surface.blit(self.image, self.rect)

    def step(self, events):
        if not self.done:
            self.time += 1
            self.age += 1
            self.energy -= 1

            if self.energy <= 0 or self.age >= self.max_lifespan:
                self.die()
                return

            self.update_mating_state()

            obs = self.genome.observe(self)
            outputs = self.genome.forward(obs)
            self.genome.step(outputs, self)
            self.update_rect()

            if self.energy > self.max_energy:
                self.energy = self.max_energy

            return self.handle_events(events)


    def handle_events(self, events):
        if events:
            for event in events:
                if event.type == pygame.MOUSEBUTTONUP:
                    mouse_pos = pygame.mouse.get_pos()
                    if self.interaction_rect.collidepoint(mouse_pos):
                        return MessagePacket(EventType.CRITTER, "profile", context={"id" : self.id})

    def update_mating_state(self):
        self.current_mating_timeout -= 1

        if self.mating_state == MatingState.MINOR:
            if self.age >= self.age_of_maturity:
                self.mating_state = MatingState.READY

        elif self.mating_state == MatingState.READY:
            if self.incoming_mate_request:
                if self.incoming_mate_request.mate == None:
                    self.set_mate(self.incoming_mate_request)
                    self.mate.set_mate(self)
            self.incoming_mate_request = None

        elif self.mating_state == MatingState.NOT_READY:
            if self.current_mating_timeout <= 0:
                self.mating_state = MatingState.READY

        elif self.mating_state == MatingState.WAITING:
            if self.outgoing_mate_request:
                if self.outgoing_mate_request.mate:
                    if self.outgoing_mate_request.mate.id == self.id:     
                        self.set_mate(self.outgoing_mate_request)
                        self.mate.set_mate(self)
                        self.outgoing_mate_request = None
                    elif self.outgoing_mate_request.mate.id != self.id:
                        self.outgoing_mate_request = None
                        self.mating_state = MatingState.READY
            else:
                self.mating_state = MatingState.READY

        elif self.mating_state == MatingState.MATING:
            pass

    def update_rect(self):
        # Enforce max movement offset
        dx = max(-self.max_speed, min(self.max_speed, self.rect.centerx - self.previous_position[0]))
        dy = max(-self.max_speed, min(self.max_speed, self.rect.centery - self.previous_position[1]))

        # Apply the constrained movement
        self.rect.centerx = (self.previous_position[0] + dx) % self.env_surface.get_width()
        self.rect.centery = (self.previous_position[1] + dy) % self.env_surface.get_height()

        # Update other rectangles
        self.body_rect.center = self.rect.center
        self.interaction_rect.center = self.rect.center

        self.interaction_rect.centerx = self.interaction_rect.centerx + config.ENV_OFFSET_X
        self.interaction_rect.centery = self.interaction_rect.centery + config.ENV_OFFSET_Y

        # Store updated position
        self.previous_position = self.rect.center

    def set_mate(self, mate):
        self.mating_state = MatingState.MATING
        self.mate = mate

    def remove_mate(self):
        self.mating_state = MatingState.NOT_READY
        self.mate = None
        self.current_mating_timeout = self.mating_timeout

    def crossover(self):
        phenotypes = {
            key: random.choice(
                [self.creation_context[key], self.mate.creation_context[key]]
            )
            for key in self.creation_context.keys()
        }
        genotypes = self.genome.crossover(self.mate)
        phenotypes["genome"] = genotypes
        self.FETUS = phenotypes

    def die(self):
        self.alive = False
        self.done = True

    def eat(self):
        self.hunger -= 1
        self.energy += self.max_energy // 2
        self.env.remove_food(self.rect.center)


class Plant(Sprite):
    def __init__(
        self,
        env_surface,
        pos=None,
        radius=4,
        n=200,
        color=(124, 176, 109),
    ):
        super().__init__()

        self.env_surface = env_surface

        self.radius = radius
        self.n = n

        # Create a transparent surface for the food
        self.image = pygame.Surface(((2 * radius), (2 * radius)), pygame.SRCALPHA)

        # Random position within env_window bounds
        self.position = pos or (
            random.randint(radius + 75, env_surface.get_width() - radius - 75),
            random.randint(radius + 75, env_surface.get_height() - radius - 75),
        )

        # Create the circle on the image surface (center of the surface)
        pygame.draw.circle(self.image, color, (radius, radius), radius)

        # Get rect for positioning
        self.rect = self.image.get_rect()
        self.rect.center = self.position

    def draw(self, surface):
        # Blit the food image to the env_window at its position
        surface.blit(self.image, self.rect.topleft)
