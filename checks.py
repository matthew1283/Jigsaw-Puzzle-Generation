from basic_functions import touches_any
import config
from basic_functions import calculate_polygon_angles
from shapely.ops import nearest_points
from shapely.geometry import Point, LineString, Polygon
import math

def is_edges_equal(edge1, edge2):
    # Extract coordinates directly
    e1x1, e1y1 = edge1.coords[0]
    e1x2, e1y2 = edge1.coords[1]
    e2x1, e2y1 = edge2.coords[0]
    e2x2, e2y2 = edge2.coords[1]

    # Check if the edges are equal within tolerance
    return (
        (abs(e1x1 - e2x1) < config.touches_threshold and abs(e1y1 - e2y1) < config.touches_threshold and
         abs(e1x2 - e2x2) < config.touches_threshold and abs(e1y2 - e2y2) < config.touches_threshold)
        or
        (abs(e1x1 - e2x2) < config.touches_threshold and abs(e1y1 - e2y2) < config.touches_threshold and
         abs(e1x2 - e2x1) < config.touches_threshold and abs(e1y2 - e2y1) < config.touches_threshold)
    )

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

def is_edge_on_outline(edge):
    point1 = Point(edge.coords[0])
    point2 = Point(edge.coords[1])
    return touches_any(point1, config.outline) and touches_any(point2, config.outline)

def is_point_in_piece(pieces, point):
    for piece in pieces:
        if piece.contains(point) and not touches_any(piece, point):
            return True
    return False

def is_piece_too_skinny(piece):
    angles = calculate_polygon_angles(piece)
    if any(angle < config.min_angle_threshold or 
           angle > 2*math.pi - config.min_angle_threshold
           for angle in angles):
        return True
    else:
        return False

def is_surrounding_too_skinny(pieces, piece):
    # Check for proximity to other pieces
    for p in pieces:
        if not touches_any(p, piece) and piece.distance(p) < config.min_distance_threshold:
            # Get the closest points between p and piece
            closest_points = nearest_points(p, piece)
            line_between = LineString([closest_points[0], closest_points[1]])

            # Check if any other piece intersects the line between p and piece
            obstructed = False
            for other_piece in pieces:
                if other_piece != p and other_piece != piece and other_piece.intersects(line_between):
                    obstructed = True
                    break

            # If no piece is directly between p and piece, check the distance
            if not obstructed:
                return True
    
    # Check for new angles formed between the new piece and existing pieces
    for existing_piece in pieces:
        if touches_any(existing_piece, piece):
            # Find shared edges or points between the new piece and the existing piece
            shared_points = []
            for coord in piece.exterior.coords[:-1]:  # Exclude the last duplicate point
                point = Point(coord)
                if touches_any(point, existing_piece):
                    shared_points.append(point)

            # Calculate angles at shared points
            for shared_point in shared_points:
                # Get the edges of the new piece and existing piece that meet at the shared point
                new_piece_edges = get_edges_at_point(piece, shared_point)
                existing_piece_edges = get_edges_at_point(existing_piece, shared_point)

                # Calculate the angle between the edges
                for new_edge in new_piece_edges:
                    for existing_edge in existing_piece_edges:
                        if is_edges_equal(new_edge, existing_edge):
                            continue
                        angle = calculate_angle_between_edges(new_edge, existing_edge)
                        if angle < config.min_angle_threshold or angle > (2 * math.pi - config.min_angle_threshold):
                            return True  # Angle is too skinny

    return False

def get_edges_at_point(polygon, point):
    edges = []
    coords = list(polygon.exterior.coords)
    for i in range(len(coords) - 1):
        p1 = Point(coords[i])
        p2 = Point(coords[i + 1])
        if touches_any(p1, point) or touches_any(p2, point):
            edges.append(LineString([p1, p2]))
    return edges


def calculate_angle_between_edges(edge1, edge2):
    # Get the coordinates of the edges
    p1 = Point(edge1.coords[0])
    p2 = Point(edge1.coords[1])
    p3 = Point(edge2.coords[0])
    p4 = Point(edge2.coords[1])

    # Find the shared point
    shared_point = None
    if touches_any(p1, p3) or touches_any(p1, p4):
        shared_point = p1
    elif touches_any(p2, p3) or touches_any(p2, p4):
        shared_point = p2

    if not shared_point:
        return 0  # No shared point, edges are not connected

    # Calculate vectors for the edges
    if shared_point == p1:
        vec1 = (p2.x - p1.x, p2.y - p1.y)
    else:
        vec1 = (p1.x - p2.x, p1.y - p2.y)

    if shared_point == p3:
        vec2 = (p4.x - p3.x, p4.y - p3.y)
    else:
        vec2 = (p3.x - p4.x, p3.y - p4.y)

    # Calculate the angle between the vectors
    dot_product = vec1[0] * vec2[0] + vec1[1] * vec2[1]
    magnitude1 = math.sqrt(vec1[0] ** 2 + vec1[1] ** 2)
    magnitude2 = math.sqrt(vec2[0] ** 2 + vec2[1] ** 2)
    cos_theta = dot_product / (magnitude1 * magnitude2)
    cos_theta = max(-1, min(1, cos_theta))  # Clamp value to avoid domain errors
    angle = math.acos(cos_theta)

    return angle

def is_surrounding_too_skinny_orig(pieces, piece):
    for p in pieces:
        if not touches_any(p, piece) and piece.distance(p) < config.min_distance_threshold:
            return True
    return False

def is_piece_overlapping_piece(p1, p2):
    try:
        p1_small = p1.buffer(-config.touches_threshold)
        if p1_small.intersects(p2.buffer(-config.touches_threshold)):
                    return True
        return False
    except:
        return True

def is_piece_overlapping_pieces(p1, pieces):
    for p in pieces:
        if is_piece_overlapping_piece(p1, p):
            return True
    return False

def is_point_on_polygon_edge(point: Point, polygon: Polygon) -> bool:
    for i in range(len(polygon.exterior.coords) - 1):
        edge = LineString([polygon.exterior.coords[i], polygon.exterior.coords[i + 1]])
        if touches_any(edge, point):
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

def check_piece_fit_wo_area(pieces, piece):
    if not config.center.buffer(config.radius * 1.01).covers(piece):
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