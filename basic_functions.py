import os
import math
import matplotlib.pyplot as plt
import random
import config
from shapely.geometry import Point

def clear_terminal():
    # Check the operating system and execute the appropriate command
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def get_point_from_angle(angle):
    x = config.center.x + config.radius * math.cos(angle)
    y = config.center.y + config.radius * math.sin(angle)
    return Point(x,y)

def touches_any(object1, object2):
    o1 = object1.buffer(config.touches_threshold)
    o2 = object2.buffer(config.touches_threshold)
    return o1.intersects(o2)

def get_random_angle():
    while True:
        a = random.uniform(-config.max_angle_change, config.max_angle_change)
        if abs(a) > config.min_angle_threshold:
            return a

def calc_random_length(l):
    return random.uniform(l*(1-config.length_distribution_factor), l*(1+config.length_distribution_factor))

def calculate_side_length(num_sides):
    return math.sqrt((4 * config.piece_area * math.tan(math.pi / num_sides)) / num_sides)

def plot_puzzle(pieces):
    """Plot a single puzzle piece and the circle outline."""
    fig, ax = plt.subplots()

    for piece in pieces:
        coords = list(piece.exterior.coords)
        x, y = zip(*coords)

        ax.plot(x, y, 'blue', alpha=0.5)  # Plot the polygon

    # Plot the circle outline
    circle = config.center.buffer(config.radius)
    circle_coords = list(circle.exterior.coords)
    circle_x, circle_y = zip(*circle_coords)
    ax.plot(circle_x, circle_y, 'red', linestyle='--', alpha=0.5, label='Circle Outline')

    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()

