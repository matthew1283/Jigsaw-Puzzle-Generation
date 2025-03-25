import os
import math
import matplotlib.pyplot as plt
import random
import config
from shapely.geometry import Point, Polygon, LineString
import numpy as np

def clear_terminal():
    # Check the operating system and execute the appropriate command
    if os.name == 'nt':
        os.system('cls')
    else:
        os.system('clear')

def run_func_till_success(func, times_to_run = 1):
    for i in range(times_to_run):
        i = 0
        while True:
            try:
                func()
                print(f'Successfully completed {func}.')
                break
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                print(f'Some error occured: {e}. Retrying...')
            finally:
                i += 1
                if i >= config.max_number_of_puzzle_generation_retries:
                    print(f'Max retries reached on {func}. Exiting.')
                    exit()

def get_point_from_angle(angle):
    x = config.center.x + config.radius * math.cos(angle)
    y = config.center.y + config.radius * math.sin(angle)
    return Point(x,y)

def touches_any_orig(object1, object2):
    o1 = object1.buffer(config.touches_threshold)
    o2 = object2.buffer(config.touches_threshold)
    return o1.intersects(o2)

def touches_any(object1, object2):
    if object1.distance(object2) > 2*config.touches_threshold:
        return False
    o1 = object1.buffer(config.touches_threshold, resolution = 1)
    o2 = object2.buffer(config.touches_threshold, resolution = 1)
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
    return random.uniform(config.min_angle_threshold, 2*math.pi-config.min_angle_threshold)

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

def plot_puzzle(pieces, edges = [], plot_outline = True):
    if not config.see_plots:
        return
    fig, ax = plt.subplots()
    for piece in pieces:
        coords = list(piece.exterior.coords)
        x, y = zip(*coords)

        ax.plot(x, y, 'blue', alpha=0.5)  # Plot the polygon

    for edge in edges:
        coords = list(edge.coords)
        x, y = zip(*coords)

        ax.plot(x, y, 'red', alpha=0.5)  # Plot the edge

    if plot_outline:
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

def save_puzzle_as_pic():
    pieces, available_edges = load_puzzle_state('puzzle_connected.txt')
    fig, ax = plt.subplots()
    for piece in pieces:
        coords = list(piece.exterior.coords)
        x, y = zip(*coords)

        ax.plot(x, y, 'blue', alpha=0.5)  # Plot the polygon
    ax.set_axis_off()  # Hide X and Y axes
    # fig.add_axes(ax)
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.6, 0.6)
    plt.gca().set_aspect('equal', adjustable='box')
    plt.savefig('finished_puzzle.png', dpi=300, bbox_inches='tight')
    
    if config.see_plots:
        plt.show()
    

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

def find_edge_containing_point(piece: Polygon, point: Point) -> LineString:
    coords = list(piece.exterior.coords)
    for i in range(len(coords) - 1):
        edge = LineString([coords[i], coords[i + 1]])
        if touches_any(edge, point):
            return edge
    return None

def save_puzzle_state(pieces, available_edges, filename):
    with open(filename, "w") as file:
        # Save pieces
        file.write("Pieces:\n")
        for i, piece in enumerate(pieces):
            file.write(f"Piece {i + 1}:\n")
            for coord in piece.exterior.coords:
                file.write(f"  {coord}\n")
        
        # Save available edges
        file.write("\nAvailable Edges:\n")
        for i, edge in enumerate(available_edges):
            file.write(f"Edge {i + 1}:\n")
            for coord in edge.coords:
                file.write(f"  {coord}\n")

def load_puzzle_state(filename):
    pieces = []
    available_edges = []

    with open(filename, "r") as file:
        lines = file.readlines()
        i = 0
        while i < len(lines):
            if lines[i].startswith("Piece"):
                # Read piece coordinates
                coords = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith("("):
                    coord = tuple(map(float, lines[i].strip().strip("()").split(",")))
                    coords.append(coord)
                    i += 1
                if coords:
                    pieces.append(Polygon(coords))
            elif lines[i].startswith("Edge"):
                # Read edge coordinates
                coords = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith("("):
                    coord = tuple(map(float, lines[i].strip().strip("()").split(",")))
                    coords.append(coord)
                    i += 1
                if coords:
                    available_edges.append(LineString(coords))
            else:
                i += 1

    return pieces, available_edges

def rotate_array(array, index):
    return array[index + 1:] + array[:index + 1]

# p = Polygon([(0.0103348577794272, -0.3067097743900926), 
# (0.0438017852924971, -0.3870564474046238), 
# (0.1929726673125626, -0.2617615591019039), 
# (0.1022765512984391, -0.2011692801772722), 
# (0.1193398499630565, -0.1437817279296914), 
# (0.0665302607283096, -0.1120159270808799), 
# (0.005173712270116, -0.1477953587930986), 
# (-0.0547967319717189, -0.1789342313635206), 
# (0.0103348577794272, -0.3067097743900926)])

# p2 = Point(-0.024, -0.233)

# asss = find_edge_containing_point(p, p2)

# print(asss)
