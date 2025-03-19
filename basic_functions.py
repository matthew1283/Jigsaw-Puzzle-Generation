import os
import math
import matplotlib.pyplot as plt
import random
import config
from shapely.geometry import Point, Polygon
import numpy as np

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

def calc_avg_points(points):
    x = 0
    y = 0
    for center in points:
        x += center.x
        y += center.y
    x /= len(points)
    y /= len(points)
    center = Point(x, y)
    return center

def get_random_angle():
    while True:
        a = random.uniform(-config.max_angle_change, config.max_angle_change)
        if abs(a) > config.min_angle_threshold:
            return a

def calc_avg_piece_area(pieces):
    avg_piece_area = 0
    for p in pieces:
        avg_piece_area += p.area
    avg_piece_area /= len(pieces)
    return avg_piece_area

def calc_random_length(l):
    return random.uniform(l*(1-config.length_distribution_factor), l*(1+config.length_distribution_factor))

def calculate_side_length(num_sides):
    return math.sqrt((4 * config.piece_area * math.tan(math.pi / num_sides)) / num_sides)

def plot_puzzle(pieces, edges = []):
    fig, ax = plt.subplots()
    for piece in pieces:
        coords = list(piece.exterior.coords)
        x, y = zip(*coords)

        ax.plot(x, y, 'blue', alpha=0.5)  # Plot the polygon

    for edge in edges:
        coords = list(edge.coords)
        x, y = zip(*coords)

        ax.plot(x, y, 'red', alpha=0.5)  # Plot the edge

    # Plot the circle outline
    circle = config.center.buffer(config.radius)
    circle_coords = list(circle.exterior.coords)
    circle_x, circle_y = zip(*circle_coords)
    
    ax.plot(circle_x, circle_y, 'red', linestyle='--', alpha=0.5, label='Circle Outline')

    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    ax.minorticks_on()
    ax.grid(visible=True, which='both', axis='both', color='gray', linestyle='-', linewidth=0.5)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.show()
    return ax

def angle_between_three_points(A, B, C):
    BA = (A[0] - B[0], A[1] - B[1])
    BC = (C[0] - B[0], C[1] - B[1])
    angle_BA = math.atan2(BA[1], BA[0])
    angle_BC = math.atan2(BC[1], BC[0])
    angle = angle_BC - angle_BA
    if angle < 0:
        angle += 2 * math.pi
    return angle

def calculate_polygon_angles(polygon):
    coords = np.array(polygon.exterior.coords)[:-1]  # Get coordinates of the polygon
    angles = []
    for i in range(len(coords)):  # Loop through each triplet of points
        p1, p2, p3 = coords[i], coords[(i + 1) % len(coords)], coords[(i + 2) % len(coords)]
        angle = angle_between_three_points(p1, p2, p3)
        
        angles.append(angle)

    return angles


