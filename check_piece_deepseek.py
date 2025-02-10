import math
import random
from shapely.geometry import Point
from basic_functions import touches_any, calc_random_length

def stage0(center, radius, ideal_length):
    """
    Stage 0: First piece (two points on the circle).
    """
    theta_starting_pt = random.uniform(0, 2 * math.pi)
    x_i = center.x + radius * math.cos(theta_starting_pt)
    y_i = center.y + radius * math.sin(theta_starting_pt)
    point_on_circle = Point(x_i, y_i)

    length = calc_random_length(ideal_length)
    theta = 2 * math.asin(length / (2 * radius))
    theta_second_pt = theta_starting_pt + theta
    x_j = center.x + radius * math.cos(theta_second_pt)
    y_j = center.y + radius * math.sin(theta_second_pt)
    second_point_on_circle = Point(x_j, y_j)

    points = [point_on_circle, second_point_on_circle]
    angle = math.atan2(points[1].y, points[1].x) + math.pi
    return points, angle

def stage1(pieces, outline, center, radius, ideal_length):
    """
    Stage 1: Touch 1 edge with another piece and 1 edge on the outline.
    """
    for p in pieces:
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                next_point = Point(p.exterior.coords[(i + 1) % len(p.exterior.coords)])
                prev_point = Point(p.exterior.coords[i - 1])
                if not touches_any(next_point, outline):
                    return [next_point, Point(point)], math.atan2(next_point.y, next_point.x)
                elif not touches_any(prev_point, outline):
                    return [prev_point, Point(point)], math.atan2(prev_point.y, prev_point.x)
    return None, None

def stage2(pieces, outline):
    """
    Stage 2: Touch 2 edges with other pieces and 1 edge on the outline.
    """
    for p in pieces:
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                next_point = Point(p.exterior.coords[(i + 1) % len(p.exterior.coords)])
                prev_point = Point(p.exterior.coords[i - 1])
                if not touches_any(next_point, outline) and not touches_any(prev_point, outline):
                    return [next_point, Point(point), prev_point], math.atan2(next_point.y, next_point.x)
    return None, None

def stage3(pieces, outline):
    """
    Stage 3: Touch 3 edges with other pieces.
    """
    for p in pieces:
        matching_edges = 0
        points = []
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                points.append(Point(point))
                if len(points) == 3:
                    return points, math.atan2(points[1].y, points[1].x)
    return None, None

def stage4(pieces, outline):
    """
    Stage 4: Touch 4 edges with other pieces.
    """
    for p in pieces:
        matching_edges = 0
        points = []
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                points.append(Point(point))
                if len(points) == 4:
                    return points, math.atan2(points[1].y, points[1].x)
    return None, None

def choose_start(piece_retries, pieces, outline, center, radius, ideal_length):
    """
    Choose the starting points based on the current stage.
    """
    if len(pieces) == 0:
        print("Stage 0: First piece")
        return stage0(center, radius, ideal_length)
    elif piece_retries < 20:
        print("Stage 1: 1 shared edge, 1 outline edge")
        points, angle = stage1(pieces, outline, center, radius, ideal_length)
        if points:
            return points, angle
    elif piece_retries < 40:
        print("Stage 2: 2 shared edges, 1 outline edge")
        points, angle = stage2(pieces, outline)
        if points:
            return points, angle
    elif piece_retries < 60:
        print("Stage 3: 3 shared edges")
        points, angle = stage3(pieces, outline)
        if points:
            return points, angle
    elif piece_retries < 80:
        print("Stage 4: 4 shared edges")
        points, angle = stage4(pieces, outline)
        if points:
            return points, angle
    else:
        print("Fallback: Random points on the outline")
        return stage0(center, radius, ideal_length)