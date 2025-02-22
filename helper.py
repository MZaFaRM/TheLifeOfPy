import math
import random
import noise
import numpy as np
import pygame
from functools import lru_cache


def split_text(text, char_limit=42):
    """
    Splits the input text into lines with a maximum of `char_limit` characters per line.
    It ensures words are not cut off in the middle unless a single word exceeds the limit.

    :param text: The input string to be split.
    :param char_limit: The maximum number of characters per line.
    :return: A list of lines with the specified character limit.
    """
    words = text.split()
    lines = []
    current_line = []

    for word in words:
        # If adding the word would exceed the limit, start a new line
        if (
            sum(len(w) for w in current_line) + len(current_line) + len(word)
            > char_limit
        ):
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            current_line.append(word)

    # Add the remaining words as the last line
    if current_line:
        lines.append(" ".join(current_line))

    return lines


def get_random_position(env_window):
    return (
        random.randint(0, env_window.get_width()),
        random.randint(0, env_window.get_height()),
    )


def get_triangle_points(rect):
    """Returns the three points of an equilateral triangle fitting inside a given rect."""
    w, h = rect.width, rect.height
    x, y = rect.topleft  # Top-left of the rect

    # Calculate the height of the equilateral triangle
    triangle_height = (math.sqrt(3) / 2) * w

    # Center the triangle vertically inside the rect
    top_vertex = (x + w // 2, y + (h - triangle_height) // 2)  # Top center
    bottom_left = (x, y + (h + triangle_height) // 2)  # Bottom left
    bottom_right = (x + w, y + (h + triangle_height) // 2)  # Bottom right

    return [top_vertex, bottom_left, bottom_right]


def get_rectangle_points(rect):
    """Returns the four points of a rectangle fitting inside a given rect."""
    w, h = rect.width // 3, rect.height
    x, y = rect.centerx - w // 2, rect.centery - h // 2

    return [x, y, w, h]


def is_point_on_line(point, line_start, line_end, width):
    """Check if a point is within a line of given width."""
    line_start, line_end, point = (
        np.array(line_start),
        np.array(line_end),
        np.array(point),
    )
    distance = np.abs(
        np.cross(line_end - line_start, line_start - point)
    ) / np.linalg.norm(line_end - line_start)
    return distance <= width


def distance_between_points(a, b):
    return pow(b[0] - a[0], 2) + pow(b[1] - a[1], 2) ** 0.5


def normalize_position(rect, env_window):
    x_range = (-(rect.width // 2), env_window.get_width() - (rect.width // 2))
    y_range = (-(rect.height // 2), env_window.get_height() - (rect.height // 2))

    x, y = rect.topleft
    if x < x_range[0]:
        x = x_range[1] - 1
    elif x > x_range[1]:
        x = x_range[0] + 1

    if y < y_range[0]:
        y = y_range[1] - 1
    elif y > y_range[1]:
        y = y_range[0] + 1

    rect.topleft = x, y
    return rect


def scale_image_by_factor(image, factor):
    image = pygame.transform.scale(
        image,
        (
            int(image.get_width() * factor[0]),
            int(image.get_height() * factor[1]),
        ),
    )

    return image


def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
