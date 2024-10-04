import pygame
import random

# Initialize Pygame
pygame.init()
screen = pygame.display.set_mode((600, 400))

# Colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)

# Traffic Light Timings
green_time = 3000
red_time = 2000

# Vehicle class
class Vehicle(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((20, 10))
        self.image.fill(random.choice([RED, GREEN]))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = random.randint(2, 5)
    
    def update(self):
        self.rect.x += self.speed

# Groups for vehicles
vehicles = pygame.sprite.Group()

# Add vehicles
for i in range(10):
    vehicle = Vehicle(random.randint(0, 500), random.randint(150, 250))
    vehicles.add(vehicle)

# Main loop
running = True
while running:
    screen.fill(WHITE)
    
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update vehicle positions
    vehicles.update()
    
    # Draw vehicles
    vehicles.draw(screen)
    
    pygame.display.flip()
    pygame.time.delay(100)

pygame.quit()
