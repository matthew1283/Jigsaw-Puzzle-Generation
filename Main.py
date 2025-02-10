from shapely.geometry import Polygon, Point
import random
import math
from time import sleep
from basic_functions import *
from check_piece import *
from starting_points import choose_start
import config
from shapely.ops import nearest_points

clear_terminal()

def check_new_point(pieces, points, outline, new_point):
    # Check if the new point is too close to any existing piece
    for p in pieces:
        if p.distance(new_point) < config.minimum_distance_threshold:
            print("moved point to optimize puzzle creation!!!")
            return nearest_points(p, new_point)[0]
        
    # Check if the new point is too close to the outline
    if outline.distance(new_point) <= config.minimum_distance_threshold:
        return nearest_points(outline, new_point)[0]
    return new_point


def create_piece(center, outline, pieces, radius, piece_area, area_distribution_factor):
    num_sides = random.randint(4, 9)
    ideal_length = calculate_side_length(piece_area, num_sides)
    points = []
    
    piece_retries = 0
    while True:
        points, angle = choose_start(piece_retries, pieces, outline, center, radius, ideal_length)

        for s in range(num_sides - len(points)):
            vertex_guess_counter = 0
            while vertex_guess_counter < 20:
                length = calc_random_length(ideal_length)
                x = points[-1].x + length * math.cos(angle)
                y = points[-1].y + length * math.sin(angle)
                new_point = Point(x, y)

                # new_point = check_new_point(pieces, points, outline, new_point)
                
                # Ensure the new point is within the outline
                if not outline.distance(new_point) <= 1e-3:
                    angle += random.uniform(-3 * math.pi / 8, 3 * math.pi / 8)
                    vertex_guess_counter += 1
                    continue

                temp_points = points.copy()
                temp_points.append(new_point)
                temp_polygon = Polygon(temp_points)
                plot_puzzle(pieces+[temp_polygon], center, radius)
                if temp_polygon.is_valid:
                    points.append(new_point)
                    angle += random.uniform(-3 * math.pi / 8, 3 * math.pi / 8)
                    break

                vertex_guess_counter += 1
                angle += random.uniform(-3 * math.pi / 8, 3 * math.pi / 8)

            if vertex_guess_counter == 20:
                piece_retries += 1
                break
        points.append(points[-1])
        piece = Polygon(points)
        plot_puzzle(pieces+[piece], center, radius)
        if check_piece_fit(pieces, center, piece, radius, piece_area, area_distribution_factor):
            return piece

def create_puzzle(num_pieces, radius, area_distribution_factor):
    center = Point(0, 0)
    circle = center.buffer(radius)
    outline = circle.boundary
    circle_area = circle.area
    piece_area = circle_area / num_pieces

    pieces = []
    for i in range(num_pieces-10):
        print(f"Creating piece {i + 1}...")
        piece = create_piece(center, outline, pieces, radius, piece_area, area_distribution_factor)
        pieces.append(piece)
        plot_puzzle(pieces, center, radius)


# Example usage
create_puzzle(config.number_of_pieces, config.radius, config.area_distribution_factor)