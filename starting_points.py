import math
import random
from shapely.geometry import Point, LineString
from shapely.strtree import STRtree

from basic_functions import get_point_from_angle, touches_any, calc_random_length, get_random_angle
from checks import is_edge_touching_outline
import config


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
    usable_edges = [edge for edge in available_edges if is_edge_touching_outline(edge)]

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
    usable_edges = [edge for edge in available_edges if is_edge_touching_outline(edge)]

    # Find two adjacent edges that share a common point
    all_adjacent_edges = []
    for i, edge1 in enumerate(usable_edges):
        for j, edge2 in enumerate(available_edges):
            if edge1 == edge2:
                continue  # Skip the same edge
            # Get the coordinates of the edges
            edge1_coords = list(edge1.coords)
            edge2_coords = list(edge2.coords)
            # Check if the edges share a common point
            if touches_any(Point(edge1_coords[1]), Point(edge2_coords[0])):  # edge1's end point is edge2's start point
                all_adjacent_edges.append([edge1, edge2])
                break
            elif touches_any(Point(edge1_coords[0]), Point(edge2_coords[1])):  # edge1's start point is edge2's end point
                all_adjacent_edges.append([edge2, edge1])
                break
            elif touches_any(Point(edge1_coords[0]), Point(edge2_coords[0])):  # both edges start at the same point
                all_adjacent_edges.append([LineString(edge1.coords[::-1]), edge2])
                break
            elif touches_any(Point(edge1_coords[1]), Point(edge2_coords[1])):
                all_adjacent_edges.append([edge1, LineString(edge2.coords[::-1])])
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

def choose_start(piece_retries, pieces, ideal_length, available_edges):
    # For FIRST PIECE
    if len(pieces) == 0: # 2 points touching circle
        points, angle = stage0(ideal_length)
        return points, angle
    
    # For OTHER PIECES
    if piece_retries < 5*config.stage_attempts_factor: # 1 shared edge, 1 circle edge
        points, angle = stage1(ideal_length, available_edges)
    else: # 2 shared edge, 1 circle edge
        points, angle = stage2(ideal_length, available_edges)
    return points, angle


def add_points_to_middle_orig(piece_retries, points, available_edges, extra_point_count = 0):
    # Add extra points to the middle piece
    if piece_retries > 100*config.stage_attempts_factor:
        extra_point_count += 6
    elif piece_retries > 70*config.stage_attempts_factor:
        extra_point_count += 5
    elif piece_retries > 50*config.stage_attempts_factor:
        extra_point_count += 4
    elif piece_retries > 30*config.stage_attempts_factor:
        extra_point_count += 3
    elif piece_retries > 15*config.stage_attempts_factor:
        extra_point_count += 2
    elif piece_retries > 5*config.stage_attempts_factor:
        extra_point_count += 1


    for i in range(extra_point_count):
        point_to_add_to = random.choice([points[0], points[-1]])
        for edge in available_edges:
            if touches_any(point_to_add_to, edge):
                if not touches_any(points[1], edge) or not touches_any(points[-2], edge):
                    other_point = None
                    if touches_any(point_to_add_to, Point(edge.coords[0])):
                        other_point = Point(edge.coords[1])
                    else:
                        other_point = Point(edge.coords[0])
                    if other_point in points:
                        break
                    if point_to_add_to == points[-1]:
                        points.append(other_point)
                        break
                    else:
                        points.insert(0, other_point)
                        break
    return points

def add_points_to_middle(piece_retries, points, available_edges, extra_point_count = 0):
    # Add extra points to the middle piece
    if piece_retries > 100*config.stage_attempts_factor:
        extra_point_count += 6
    elif piece_retries > 70*config.stage_attempts_factor:
        extra_point_count += 5
    elif piece_retries > 50*config.stage_attempts_factor:
        extra_point_count += 4
    elif piece_retries > 30*config.stage_attempts_factor:
        extra_point_count += 3
    elif piece_retries > 15*config.stage_attempts_factor:
        extra_point_count += 2
    elif piece_retries > 5*config.stage_attempts_factor:
        extra_point_count += 1

    tree = STRtree(available_edges)
    for i in range(extra_point_count):
        point_to_add_to = random.choice([points[0], points[-1]])
        possible_edges = tree.query(point_to_add_to)
        possible_edges = [available_edges[i] for i in possible_edges]
        for edge in possible_edges:
            if touches_any(point_to_add_to, edge):
                if not touches_any(points[1], edge) or not touches_any(points[-2], edge):
                    other_point = None
                    if touches_any(point_to_add_to, Point(edge.coords[0])):
                        other_point = Point(edge.coords[1])
                    else:
                        other_point = Point(edge.coords[0])
                    if other_point in points:
                        break
                    if point_to_add_to == points[-1]:
                        points.append(other_point)
                        break
                    else:
                        points.insert(0, other_point)
                        break
    return points

def choose_start_for_middle_orig(available_edges):
    # Find the farthest point from the center
    farthest_point = None
    max_distance = 0
    for edge in available_edges:
        for point in edge.coords:
            distance = Point(point).distance(config.center)
            if distance > max_distance:
                max_distance = distance
                farthest_point = Point(point)
    if not farthest_point:
        print("No farthest point found. Skipping middle piece creation.")
        return None, None
    # print(farthest_point)
    # Find the two edges that share the farthest point
    edges_with_farthest_point = []
    for edge in available_edges:
        if farthest_point.distance(Point(edge.coords[0])) < config.touches_threshold or \
            farthest_point.distance(Point(edge.coords[1])) < config.touches_threshold:
            edges_with_farthest_point.append(edge)
    
    # print(edges_with_farthest_point)
    if len(edges_with_farthest_point) < 2:
        print("Not enough edges to create a middle piece. Skipping.")
        return None, None

    # Create a new piece starting from the two edges
    edge1, edge2 = edges_with_farthest_point[:2]
    if touches_any(Point(edge1.coords[0]), Point(edge2.coords[0])):
        points = [Point(edge1.coords[1]), Point(edge1.coords[0]), Point(edge2.coords[1])]
    elif touches_any(Point(edge1.coords[0]), Point(edge2.coords[1])):
        points = [Point(edge1.coords[1]), Point(edge1.coords[0]), Point(edge2.coords[0])]
    elif touches_any(Point(edge1.coords[1]), Point(edge2.coords[0])):
        points = [Point(edge1.coords[0]), Point(edge1.coords[1]), Point(edge2.coords[1])]
    else:
        points = [Point(edge1.coords[0]), Point(edge1.coords[1]), Point(edge2.coords[0])]
    angle = get_random_angle()
    
    return points, angle

def choose_start_for_middle(available_edges):
    # Find the farthest point from the center
    farthest_point = None
    max_distance = 0
    for edge in available_edges:
        for point in edge.coords:
            distance = Point(point).distance(config.center)
            if distance > max_distance:
                max_distance = distance
                farthest_point = Point(point)
    if not farthest_point:
        print("No farthest point found. Skipping middle piece creation.")
        return None, None
    # print(farthest_point)
    # Find the two edges that share the farthest point
    edges_with_farthest_point = []
    tree = STRtree(available_edges)
    possible_edges = tree.query(farthest_point)
    possible_edges = [available_edges[i] for i in possible_edges]
    for edge in possible_edges:
        if farthest_point.distance(Point(edge.coords[0])) < config.touches_threshold or \
            farthest_point.distance(Point(edge.coords[1])) < config.touches_threshold:
            edges_with_farthest_point.append(edge)
    
    # print(edges_with_farthest_point)
    if len(edges_with_farthest_point) < 2:
        print("Not enough edges to create a middle piece. Skipping.")
        return None, None

    # Create a new piece starting from the two edges
    edge1, edge2 = edges_with_farthest_point[:2]
    if touches_any(Point(edge1.coords[0]), Point(edge2.coords[0])):
        points = [Point(edge1.coords[1]), Point(edge1.coords[0]), Point(edge2.coords[1])]
    elif touches_any(Point(edge1.coords[0]), Point(edge2.coords[1])):
        points = [Point(edge1.coords[1]), Point(edge1.coords[0]), Point(edge2.coords[0])]
    elif touches_any(Point(edge1.coords[1]), Point(edge2.coords[0])):
        points = [Point(edge1.coords[0]), Point(edge1.coords[1]), Point(edge2.coords[1])]
    else:
        points = [Point(edge1.coords[0]), Point(edge1.coords[1]), Point(edge2.coords[0])]
    angle = get_random_angle()
    
    return points, angle
