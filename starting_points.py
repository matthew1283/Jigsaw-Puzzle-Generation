import math
import random
from shapely.geometry import Point
from basic_functions import *
import config

def stage0(center, radius, ideal_length):
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
    possible_edges = []

    for p in pieces:
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                print('hello')
                next_point = Point(p.exterior.coords[(i+1) % len(p.exterior.coords)])
                prev_point = Point(p.exterior.coords[i-1])
                if not touches_any(next_point, outline):
                    print('hello2')
                    possible_edges.append([next_point, Point(point)])
                elif not touches_any(prev_point, outline):
                    print('hello3')
                    possible_edges.append([prev_point, Point(point)])
    points = random.choice(possible_edges)
    theta_starting_pt = math.atan2(points[1].y, points[1].x)

    # Generate an additional point on the circle outline
    length = calc_random_length(ideal_length)
    theta = 2 * math.asin(length / (2 * radius))
    theta_second_pt = theta_starting_pt + random.choice([1, -1])*theta
    x_new = center.x + radius * math.cos(theta_second_pt)
    y_new = center.y + radius * math.sin(theta_second_pt)
    new_point_on_circle = Point(x_new, y_new)

    # Combine the points
    points.append(new_point_on_circle)

    angle = math.atan2(points[1].y, points[1].x) + math.pi
    return points, angle

def stage2(pieces, outline):
    for p in pieces:
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                if not touches_any(Point(p.exterior.coords[i-1]), outline):
                    points = [Point(p.exterior.coords[i]), Point(p.exterior.coords[i-1])]
                    matching_edge = True
                    break
                elif not touches_any(Point(p.exterior.coords[(i+1) % len(p.exterior.coords)]), outline):
                    points = [Point(p.exterior.coords[i]), Point(p.exterior.coords[(i+1) % len(p.exterior.coords)])]
                    matching_edge = True
                    break
        if matching_edge:
            break
    angle = math.atan2(points[1].y, points[1].x) + math.pi
    return points, angle

def stage3(pieces, outline):
    for p in pieces:
        matching_edges = 0
        points = []
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                points.append(Point(point))
                if len(points) == 2:
                    matching_edge = True
                    break
            if touches_any(Point(p.exterior.coords[i-1]), outline) or touches_any(Point(p.exterior.coords[(i+1) % len(p.exterior.coords)]), outline):
                matching_edges += 1
            if matching_edges == 2:
                matching_edge = True
                break
        if matching_edge:
            break
    angle = math.atan2(points[1].y, points[1].x) + math.pi
    return points, angle

def stage4(pieces, outline):
    for p in pieces:
        matching_edges = 0
        points = []
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                points.append(Point(point))
                if len(points) == 3:
                    matching_edge = True
                    break
            if touches_any(Point(p.exterior.coords[i-1]), outline) or touches_any(Point(p.exterior.coords[(i+1) % len(p.exterior.coords)]), outline):
                matching_edges += 1
            if matching_edges == 3:
                matching_edge = True
                break
        if matching_edge:
            break
    angle = math.atan2(points[1].y, points[1].x) + math.pi
    return points, angle

def stage5(pieces, outline):
    for p in pieces:
        matching_edges = 0
        points = []
        for i, point in enumerate(p.exterior.coords):
            if touches_any(Point(point), outline):
                points.append(Point(point))
                if len(points) == 4:
                    matching_edge = True
                    break
            if touches_any(Point(p.exterior.coords[i-1]), outline) or touches_any(Point(p.exterior.coords[(i+1) % len(p.exterior.coords)]), outline):
                matching_edges += 1
            if matching_edges == 4:
                matching_edge = True
                break
        if matching_edge:
            break
    angle = math.atan2(points[1].y, points[1].x) + math.pi
    return points, angle

def choose_start(piece_retries, pieces, outline, center, radius, ideal_length):
    x = config.stage_attempts_factor
    if len(pieces) == 0: # 2 points touching circle
        print("implementing stage 0, first piece down!")
        points, angle = stage0(center, radius, ideal_length)
    elif piece_retries < x: # 1 shared edge, 1 circle edge
        print("implementing stage 1")
        points, angle = stage1(pieces, outline, center, radius, ideal_length)
    elif piece_retries < 3*x: # 1 point on circle, and sharing 1 edge
        print("implementing stage 2")
        points, angle = stage2(pieces, outline)
    elif piece_retries < 5*x: # 2 shared edges
        print("implementing stage 3")
        points, angle = stage3(pieces, outline)
    elif piece_retries < 7*x: # 3 shared edges
        print("implementing stage 4")
        points, angle = stage4(pieces, outline)
    else: # 4 shared edges
        print("implementing stage 5")
        points, angle = stage5(pieces, outline)
    return points, angle