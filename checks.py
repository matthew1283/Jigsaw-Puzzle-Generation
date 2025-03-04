from basic_functions import touches_any
import config
from basic_functions import calculate_polygon_angles
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString, Polygon


def is_edges_equal(edge1, edge2):
    coords1 = sorted([(edge1.coords[0][0], edge1.coords[0][1]), (edge1.coords[1][0], edge1.coords[1][1])])
    coords2 = sorted([(edge2.coords[0][0], edge2.coords[0][1]), (edge2.coords[1][0], edge2.coords[1][1])])
    return coords1 == coords2

def is_edge_in_piece(edge, p):
    if isinstance(edge, LineString):
        edges_list = list(edge.coords)
        edge = [Point(point) for point in edges_list]
    for i, point in enumerate(p.exterior.coords):
        current_point = Point(point)
        next_point = Point(p.exterior.coords[(i + 1) % len(p.exterior.coords)])
        # Check if the edge matches any edge in the piece
        if (current_point == edge[0] and next_point == edge[1]) or (current_point == edge[1] and next_point == edge[0]):
            return True
    return False

def is_edge_shared(edge, piece, pieces):
    for p in pieces:
        if p == piece:
            continue
        if is_edge_in_piece(edge, p):
            return True
    return False

def is_edge_touching_outline(edge):
    if touches_any(edge, config.outline):
        return True
    return False

def is_point_in_piece(pieces, point):
    for piece in pieces:
        if piece.contains(point) and not touches_any(piece, point):
            return True
    return False

def is_piece_too_skinny(piece):
    angles = calculate_polygon_angles(piece)
    if any(angle < config.min_angle_threshold for angle in angles):
        return True
    else:
        return False

def is_surrounding_too_skinny(pieces, piece):
    for p in pieces:
        if piece.distance(p) < config.min_distance_threshold and not touches_any(p, piece):
            return True
    return False

def is_piece_overlapping_piece(p1, p2):
    p1_small = p1.buffer(-config.touches_threshold)
    if p1_small.intersects(p2.buffer(-config.touches_threshold)):
                return True
    return False

def is_piece_overlapping_pieces(p1, pieces):
    for p in pieces:
        if is_piece_overlapping_piece(p1, p):
            return True
    return False

def is_point_on_polygon_edge(point: Point, polygon: Polygon) -> bool:

    for i in range(len(polygon.exterior.coords) - 1):
        edge = LineString([polygon.exterior.coords[i], polygon.exterior.coords[i + 1]])
        if edge.distance(point) < config.touches_threshold:
            return True
    return False


def check_piece_fit(pieces, piece):
    if not config.center.buffer(config.radius * 1.01).covers(piece):
        return False
    if piece.area < config.lower_piece_area or piece.area > config.upper_piece_area:
        return False
    if is_piece_overlapping_pieces(piece, pieces):
        return False
    if is_piece_too_skinny(piece):
        return False
    if is_surrounding_too_skinny(pieces, piece):
        return False
    return True

def check_new_point(pieces, new_point):
    # Check if the new point is too close to any existing piece
    for p in pieces:
        if p.distance(new_point) < config.min_distance_threshold:
            # print("moved point to optimize puzzle creation!!!")
            return nearest_points(p, new_point)[0]
        
    # Check if the new point is too close to the outline
    if config.outline.distance(new_point) <= config.min_distance_threshold:
        return nearest_points(config.outline, new_point)[0]
    return new_point