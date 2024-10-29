import random
import noise
import numpy as np
import pygame


def map_value(value, start1, stop1, start2, stop2):
    return start2 + (stop2 - start2) * ((value - start1) / (stop1 - start1))


def generate_noise_map(width, height, octaves=4, scale=100.0, cutoff=0.02):
    noise_map = np.zeros((width, height))
    for x in range(width):
        for y in range(height):
            # Generate noise value for this position
            noise_value = noise.pnoise2(x / scale, y / scale, octaves=octaves)

            # Apply cutoff: If noise_value is lesser than cutoff, add terrain
            if noise_value < cutoff:
                noise_map[x][y] = True  # Grass is present
            else:
                noise_map[x][y] = False  # No grass here
    return noise_map


def create_gradient(surface, top_color, bottom_color):
    height = surface.get_height()
    width = surface.get_width()

    for row in range(height):
        # Calculate the interpolation factor (0.0 at the top, 1.0 at the bottom)
        blend_factor = row / height

        # Interpolate between the top and bottom colors (green to yellow)
        r = top_color[0] * (1 - blend_factor) + bottom_color[0] * blend_factor
        g = top_color[1] * (1 - blend_factor) + bottom_color[1] * blend_factor
        b = top_color[2] * (1 - blend_factor) + bottom_color[2] * blend_factor

        # Draw the gradient line inside the rectangle
        pygame.draw.line(surface, (int(r), int(g), int(b)), (0, row), (width, row))


def get_random_position(screen):
    return (
        random.randint(0, screen.get_width()),
        random.randint(0, screen.get_height()),
    )


def distance_between_points(a, b):
    return pow(b[0] - a[0], 2) + pow(b[1] - a[1], 2) ** 0.5

def normalize_position(rect, screen):
    rect.centerx = rect.centerx % screen.get_width()
    rect.centery = rect.centery % screen.get_height()
    return rect
