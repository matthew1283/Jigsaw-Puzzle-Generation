import os
import math
import matplotlib.pyplot as plt
import random

def clear_terminal():
    # Check the operating system and execute the appropriate command
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def touches_any(object1, object2, distance_threshold=1e-3):
    o1 = object1.buffer(distance_threshold)
    o2 = object2.buffer(distance_threshold)
    return o1.intersects(o2)

def calc_random_length(l):
    l_d_factor = 0.2
    return random.uniform(l*(1-l_d_factor), l*(1+l_d_factor))

def calculate_side_length(area, num_sides):
    # Calculate the side length for the given area and number of sides
    side_length = math.sqrt((4 * area * math.tan(math.pi / num_sides)) / num_sides)
    return side_length


def plot_puzzle(pieces, center, radius):
    """Plot a single puzzle piece and the circle outline."""
    fig, ax = plt.subplots()

    for piece in pieces:
        coords = list(piece.exterior.coords)
        x, y = zip(*coords)

        ax.plot(x, y, 'blue', alpha=0.5)  # Plot the polygon

    # Plot the circle outline
    circle = center.buffer(radius)
    circle_coords = list(circle.exterior.coords)
    circle_x, circle_y = zip(*circle_coords)
    ax.plot(circle_x, circle_y, 'red', linestyle='--', alpha=0.5, label='Circle Outline')

    ax.set_xlim(-1, 1)
    ax.set_ylim(-1, 1)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
