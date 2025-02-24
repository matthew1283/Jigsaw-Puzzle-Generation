from basic_functions import touches_any
import config
from basic_functions import plot_puzzle
import math
import numpy as np

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
    coords = np.array(polygon.exterior.coords)  # Get coordinates of the polygon
    angles = []
    for i in range(len(coords) - 2):  # Loop through each triplet of points
        p1, p2, p3 = coords[i], coords[i + 1], coords[i + 2]
        angle = angle_between_three_points(p1, p2, p3)
        
        angles.append(angle)

    return angles

def is_piece_too_skinny(piece):
    angles = calculate_polygon_angles(piece)
    print(angles)
    if any(angle < config.min_angle_threshold for angle in angles):
        return True
    else:
        return False

def is_surrounding_too_skinny(pieces, piece):
    for p in pieces:
        if piece.distance(p) < config.min_distance_threshold and not touches_any(p, piece):
            return True
    return False

def check_piece_fit(pieces, piece):
    if not config.center.buffer(config.radius * 1.01).covers(piece):
        # print('uh oh piece out of border gotta try again')
        return False
    if piece.area < config.lower_piece_area or piece.area > config.upper_piece_area:
        # print('uh oh piece too small or too big gotta try again')
        return False
    shrunk_piece = piece.buffer(-config.touches_threshold)
    for p in pieces:
        if shrunk_piece.intersects(p.buffer(-config.touches_threshold)):
            # print('uh oh piece didnt fit gotta try again')
            return False
    if is_piece_too_skinny(piece):
        # print('uh oh piece is too skinny gotta try again')
        return False
    if is_surrounding_too_skinny(pieces, piece):
        # print('uh oh surroundings too skinny gotta try again')
        return False
    return True

    