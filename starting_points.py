import math
import random
from shapely.geometry import Point
from basic_functions import *
import config

def is_edge_shared(edge, piece, pieces):
    for p in pieces:
        if p == piece:
            continue
        for i, point in enumerate(p.exterior.coords):
            current_point = Point(point)
            next_point = Point(p.exterior.coords[(i + 1) % len(p.exterior.coords)])
            # Check if the edge matches any edge in the piece
            if (current_point == edge[0] and next_point == edge[1]) or (current_point == edge[1] and next_point == edge[0]):
                return True
    return False

def is_edge_touching_outline(edge):
    if touches_any(edge, config.outline):
        return True
    return False

def stage0(ideal_length):
    theta_pt1 = random.uniform(0, 2 * math.pi)
    point_on_circle = get_point_from_angle(theta_pt1)

    length = calc_random_length(ideal_length)
    theta = 2 * math.asin(length / (2 * config.radius))
    theta_pt2 = theta_pt1 + theta
    second_point_on_circle = get_point_from_angle(theta_pt2)

    points = [point_on_circle, second_point_on_circle]
    angle = math.atan2(points[1].y, points[1].x) + math.pi
    return points, angle

def stage1(ideal_length, available_edges):
    usable_edges = []
    # print(available_edges)
    for edge in available_edges:
        if is_edge_touching_outline(edge):
            usable_edges.append(edge)
    shared_edge = random.choice(usable_edges)
    points = [Point(coord) for coord in shared_edge.coords]

    if touches_any(points[0], config.outline):
        points = [points[1], points[0]]
    theta_pt1 = math.atan2(points[1].y, points[1].x)

    # Generate an additional point on the circle outline
    length = calc_random_length(ideal_length)
    theta = 2 * math.asin(length / (2 * config.radius))
    theta_pt2 = theta_pt1 + random.choice([1, -1])*theta
    new_point_on_circle = get_point_from_angle(theta_pt2)

    # Combine the points
    points.append(new_point_on_circle)

    angle = math.atan2(points[1].y, points[1].x) + math.pi
    return points, angle

def stage2(ideal_length, available_edges):
    usable_edges = []
    for edge in available_edges:
        if is_edge_touching_outline(edge):
            usable_edges.append(edge)
    # Find two adjacent edges that share a common point
    all_adjacent_edges = []
    for i, edge1 in enumerate(usable_edges):
        for j, edge2 in enumerate(available_edges):
            if i == j:
                continue  # Skip the same edge
            # Get the coordinates of the edges
            edge1_coords = list(edge1.coords)
            edge2_coords = list(edge2.coords)
            # Check if the edges share a common point
            if edge1_coords[1] == edge2_coords[0]:  # edge1's end point is edge2's start point
                all_adjacent_edges.append([edge1, edge2])
                break
            elif edge1_coords[0] == edge2_coords[1]:  # edge1's start point is edge2's end point
                all_adjacent_edges.append([edge2, edge1])
                break
    adjacent_edges = random.choice(all_adjacent_edges)
    # Extract the shared point and the other two points
    shared_point = Point(adjacent_edges[0].coords[1])  # The common point between the two edges
    point1 = Point(adjacent_edges[0].coords[0])  # The first point of the first edge
    point2 = Point(adjacent_edges[1].coords[1])  # The second point of the second edge

    # Combine the points
    if touches_any(point1, config.outline):
        points = [point2, shared_point, point1]
    else:
        points = [point1, shared_point, point2]

    # Generate an additional point on the circle outline
    length = calc_random_length(ideal_length)
    theta = 2 * math.asin(length / (2 * config.radius))
    theta_pt = math.atan2(points[-1].y, points[-1].x) + random.choice([1, -1]) * theta
    new_point_on_circle = get_point_from_angle(theta_pt)

    # Combine the points
    points.append(new_point_on_circle)
    # Calculate the angle for the next side
    angle = math.atan2(points[-1].y, points[-1].x) + math.pi
    return points, angle

def stage3(ideal_length, available_edges):
    points = []
    angle= []
    return points, angle

def choose_start(piece_retries, pieces, ideal_length, available_edges):
    x = config.stage_attempts_factor
    if len(pieces) == 0: # 2 points touching circle
        # print("implementing stage 0, first piece down!")
        points, angle = stage0(ideal_length)
    elif piece_retries < 5*x: # 1 shared edge, 1 circle edge
        # print("implementing stage 1")
        points, angle = stage1(ideal_length, available_edges)
    elif piece_retries < 50*x: # 2 shared edge, 1 circle edge
        # print("implementing stage 2")
        points, angle = stage2(ideal_length, available_edges)
    elif piece_retries < 100*x: # 3 shared edge, 1 circle edge
        # print("implementing stage 3")
        points, angle = stage3(ideal_length, available_edges)
    return points, angle