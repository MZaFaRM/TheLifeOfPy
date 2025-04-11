import colorsys
import math
import random
import numpy as np
import pygame


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


import random


def generate_species_name():
    first_parts = [
        "Shadow",
        "Iron",
        "Blue",
        "Red",
        "Swift",
        "Golden",
        "Storm",
        "Frost",
        "Wild",
        "Silent",
        "Night",
        "Silver",
        "Bright",
        "Crimson",
        "Dawn",
        "Dark",
        "Fire",
        "Glade",
        "River",
        "Stone",
    ]

    second_parts = [
        "fang",
        "claw",
        "tail",
        "wing",
        "horn",
        "pelt",
        "eye",
        "bloom",
        "root",
        "scale",
        "howl",
        "stride",
        "song",
        "flame",
        "heart",
        "gaze",
        "leaf",
        "whisper",
        "thorn",
        "mark",
    ]

    return f"{random.choice(first_parts)} {random.choice(second_parts)}"


def get_square_points(rect, rotation_degrees=90):
    """Generates a square directly with a given rotation, inside the given rect."""
    cx, cy = rect.center  # Center of the rectangle
    radius = min(rect.width, rect.height) / 2  # Fit inside the rect

    # Convert rotation from degrees to radians
    rotation_radians = math.radians(rotation_degrees)

    points = []
    for i in range(4):
        angle = rotation_radians + (i * math.pi / 2)  # Spread points evenly
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))

    return points


def get_triangle_points(rect, rotation_degrees=90):
    """Generates a triangle directly with a given rotation, inside the given rect."""
    cx, cy = rect.center  # Center of the rectangle
    radius = min(rect.width, rect.height) / 2  # Fit inside the rect

    # Convert rotation from degrees to radians
    rotation_radians = math.radians(rotation_degrees)

    points = []
    for i in range(3):
        angle = rotation_radians + (i * 2 * math.pi / 3)  # Spread points evenly
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))

    return points


def get_pentagon_points(rect, rotation_degrees=90):
    """Generates a pentagon directly with a given rotation, inside the given rect."""
    cx, cy = rect.center  # Center of the rectangle
    radius = min(rect.width, rect.height) / 2  # Fit inside the rect

    # Convert rotation from degrees to radians
    rotation_radians = math.radians(rotation_degrees)

    points = []
    for i in range(5):
        angle = rotation_radians + (i * 2 * math.pi / 5)  # Spread points evenly
        x = cx + radius * math.cos(angle)
        y = cy + radius * math.sin(angle)
        points.append((x, y))

    return points

def is_point_on_line_segment(point, line_start, line_end, width):
    """Check if a point is within a finite line segment of given width."""
    point = np.array(point)
    line_start = np.array(line_start)
    line_end = np.array(line_end)

    line_vec = line_end - line_start
    point_vec = point - line_start

    # Project point onto the line (scalar projection)
    proj_length = np.dot(point_vec, line_vec) / np.linalg.norm(line_vec)

    # Check if projection is within the segment bounds
    if proj_length < 0 or proj_length > np.linalg.norm(line_vec):
        return False

    # Compute perpendicular distance
    distance = np.abs(np.cross(line_vec, point_vec)) / np.linalg.norm(line_vec)
    return distance <= width

def distance_between_points(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


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


def hex_to_rgb(hex_color: str):
    hex_color = hex_color.lstrip("#")
    hex_color = hex_color.ljust(6, "0")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb_color):
    return "#{:02x}{:02x}{:02x}".format(*rgb_color)


def get_random_color(seed=None, saturation=0.7, brightness=0.8):
    """Generates a distinct color using the golden angle method with a random index."""
    golden_angle = 137.5 / 360  # Convert degrees to fraction
    index = random.randint(0, 10**6) if seed is None else seed  # Random large index
    hue = (index * golden_angle) % 1.0  # Distribute hues evenly
    r, g, b = colorsys.hsv_to_rgb(hue, saturation, brightness)
    return rgb_to_hex((int(r * 255), int(g * 255), int(b * 255)))


def limit_text_size(text, max_size):
    """
    Limits the size of the text to a maximum number of characters.
    If the text exceeds the limit, it truncates the text and adds ellipsis.

    :param text: The input string to be limited.
    :param max_size: The maximum number of characters allowed.
    :return: The limited string with ellipsis if truncated.
    """
    if len(text) > max_size:
        return text[: max_size - 1] + "."
    return text


def split_word(text, max_size):
    """
    Splits a word into smaller parts if it exceeds the maximum size.

    :param text: The input string to be split.
    :param max_size: The maximum number of characters allowed.
    :return: A list of strings, each within the specified size limit.
    """
    if len(text) <= max_size:
        return [text]

    return [text[i : i + max_size] for i in range(0, len(text), max_size)]


def dfs(graph, node=None, visited: list = None, group: list = None):
    if visited is None:
        visited = []

    if node is not None:
        visited.append(node)
        if group is not None:
            group.append(node)
        for neighbor in graph.get(node, set()):
            if neighbor not in visited:
                dfs(graph, neighbor, visited, group)
    else:
        for node in graph:
            if node not in visited:
                dfs(graph, node, visited, group)

    return visited
