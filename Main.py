from shapely.geometry import Polygon, Point, LineString
import random
import math
from time import sleep
from basic_functions import *
from check_piece import *
from starting_points import choose_start, is_edge_shared
import config
from shapely.ops import nearest_points

clear_terminal()

def update_available_edges(available_edges, piece):
    outline = config.center.buffer(config.radius).boundary  # Circle outline

    coords = list(piece.exterior.coords)
    for i in range(len(coords)):
        used_up = False
        point1 = Point(coords[i])
        point2 = Point(coords[(i + 1) % len(coords)])  # Wrap around to the first point
        edge = LineString([point1, point2])

        if touches_any(point1, outline) and touches_any(point2, outline): # Skip edges on the outline
            continue
        
        for existing_edge in available_edges[:]: # Remove pre-existing edges 
            if touches_any(point1, existing_edge) and touches_any(point2, existing_edge):
                available_edges.remove(existing_edge)
                used_up = True
                continue

        if not used_up:
            available_edges.append(edge)
    return available_edges

def revert_available_edges(available_edges, piece):
    outline = config.center.buffer(config.radius).boundary  # Circle outline

    # Iterate over the edges of the piece being removed
    coords = list(piece.exterior.coords)
    for i in range(len(coords)):
        point1 = Point(coords[i])
        point2 = Point(coords[(i + 1) % len(coords)])  # Wrap around to the first point
        edge = LineString([point1, point2])

        # Skip edges on the outline
        if touches_any(point1, outline) and touches_any(point2, outline):
            continue

        # Remove the edge from available_edges if it was added by this piece
        if edge in available_edges:
            available_edges.remove(edge)
            print(f"Removed edge from available_edges: {edge}")

        # Re-add edges that were removed when this piece was added
        # (This requires tracking which edges were removed when the piece was added)
        # For now, assume that any edge touching this piece's edge should be re-added
        for existing_edge in available_edges[:]:
            if touches_any(point1, existing_edge) and touches_any(point2, existing_edge):
                available_edges.append(existing_edge)
                print(f"Re-added edge to available_edges: {existing_edge}")

    return available_edges


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

def is_point_in_piece(pieces, point):
    for piece in pieces:
        if piece.contains(point) and not touches_any(piece, point):
            return True
    return False

def create_piece(pieces, available_edges):
    num_sides = random.randint(4, 8)
    print("number_of_sides: "+str(num_sides))
    ideal_length = calculate_side_length(num_sides)
    points = []
    forbidden_positions = {i: [] for i in range(num_sides)}


    piece_retries = 0
    while True:
        # print(forbidden_positions)
        if piece_retries % 10 == 0:
            print(piece_retries)
        if piece_retries > config.max_piece_retry_count:
            return None, available_edges

        points, angle = choose_start(piece_retries, pieces, ideal_length, available_edges)
        for s in range(num_sides - len(points)):
            vertex_guess_counter = 0
            while vertex_guess_counter < 20:
                length = calc_random_length(ideal_length)
                x = points[-1].x + length * math.cos(angle)
                y = points[-1].y + length * math.sin(angle)
                new_point = Point(x, y)

                if any(new_point.distance(forbidden) < config.min_distance_threshold for forbidden in forbidden_positions[s]):
                    # print(f"Skipping forbidden position for point {s}")
                    angle += get_random_angle()
                    vertex_guess_counter += 1
                    continue

                new_point = check_new_point(pieces, new_point)

                if touches_any(new_point, config.outline):
                    angle += get_random_angle()
                    vertex_guess_counter += 1
                    continue
                
                temp_points = points.copy()
                temp_points.append(new_point)
                temp_polygon = Polygon(temp_points)
                # plot_puzzle(pieces+[temp_polygon], center, radius)
                if temp_polygon.is_valid and not is_point_in_piece(pieces, new_point):
                    points.append(new_point)
                    angle += get_random_angle()
                    break
                else:
                    forbidden_positions[s].append(new_point)
                    # print(f"Added forbidden position for point {s}: {new_point}")

                vertex_guess_counter += 1
                angle += get_random_angle()

            if vertex_guess_counter == config.point_guess_limit:
                piece_retries += 1
                break
        last_edge_length = math.sqrt((points[-1].x - points[0].x)**2 + (points[-1].y - points[0].y)**2)
        if last_edge_length < ideal_length * (1-config.last_side_length_leniency*config.length_distribution_factor) or last_edge_length > ideal_length * (1+config.last_side_length_leniency*config.length_distribution_factor):
            # print('uh oh piece side length bad')
            piece_retries += 1
            continue
        points.append(points[0])
        piece = Polygon(points)
        # plot_puzzle(pieces+[piece])
        if check_piece_fit(pieces, piece):
            available_edges = update_available_edges(available_edges, piece)
            return piece, available_edges
        else:
            piece_retries += 1
            forbidden_positions[2].append(points[2])
            # print(f"Added forbidden position for point {s}: {new_point}")

def adjust_pieces(pieces: list[Polygon], available_edges: list[LineString]):
    old_edges = []
    new_edges = []

    for idx1, piece1 in enumerate(pieces):  # Use enumerate to track the index of piece1
        for i, point in enumerate(piece1.exterior.coords[:-1]):  # Iterate over exterior coordinates (excluding the last duplicate)
            point = Point(point)  # Convert coordinate to Point object
            for idx2, piece2 in enumerate(pieces):  # Use enumerate to track the index of piece2
                if piece1 == piece2:
                    continue
                if piece2.distance(point) < config.min_distance_threshold and not touches_any(piece2, point):
                    # Get the previous and next points in the polygon's exterior ring
                    previous_point = Point(piece1.exterior.coords[i - 1])
                    next_point = Point(piece1.exterior.coords[(i + 1) % len(piece1.exterior.coords)])

                    # Find the nearest point on piece2 to the current point
                    new_point = nearest_points(piece2, point)[0]

                    # Update the current point in piece1
                    new_coords_piece1 = list(piece1.exterior.coords)
                    new_coords_piece1[i] = (new_point.x, new_point.y)
                    pieces[idx1] = Polygon(new_coords_piece1)  # Update piece1 in the pieces list

                    # Record the old and new edges
                    old_edges.append(LineString([previous_point, point]))
                    new_edges.append(LineString([next_point, new_point]))

                    # Find the edge on piece2 that contains the new_point
                    edge_on_piece2 = find_edge_containing_point(piece2, new_point)
                    if edge_on_piece2:
                        # Split the edge on piece2 into two edges at the new_point
                        split_edges = split_edge(edge_on_piece2, new_point)
                        old_edges.append(edge_on_piece2)
                        new_edges.extend(split_edges)

                        # Update piece2 in the pieces list
                        new_coords_piece2 = list(piece2.exterior.coords)
                        for j in range(len(new_coords_piece2) - 1):
                            edge = LineString([new_coords_piece2[j], new_coords_piece2[j + 1]])
                            if edge.equals_exact(edge_on_piece2, tolerance=config.touches_threshold):
                                # Insert the new_point into piece2's coordinates
                                new_coords_piece2.insert(j + 1, (new_point.x, new_point.y))
                                break
                        pieces[idx2] = Polygon(new_coords_piece2)  # Update piece2 in the pieces list

                    break  # Move to the next point in piece1

    # Update available_edges by removing old edges and adding new ones
    for edge in old_edges:
        for available_edge in available_edges:
            if edge.equals_exact(available_edge, tolerance=config.touches_threshold):
                available_edges.remove(available_edge)
                break

    available_edges.extend(new_edges)

    return pieces, available_edges  # Return the updated list

def find_edge_containing_point(piece: Polygon, point: Point) -> LineString:
    """Find the edge of a polygon that contains a given point."""
    coords = list(piece.exterior.coords)
    for i in range(len(coords) - 1):
        edge = LineString([coords[i], coords[i + 1]])
        if edge.distance(point) < config.touches_threshold:
            return edge
    return None

def split_edge(edge: LineString, point: Point) -> list[LineString]:
    """Split an edge into two edges at a given point."""
    coords = list(edge.coords)
    for i in range(len(coords) - 1):
        segment = LineString([coords[i], coords[i + 1]])
        if segment.distance(point) < config.touches_threshold:
            return [
                LineString([coords[i], (point.x, point.y)]),
                LineString([(point.x, point.y), coords[i + 1]])
            ]
    return [edge]
        

def create_puzzle():
    pieces = []
    available_edges = []
    i = 0
    while i < config.number_of_pieces-5:
        print(f"Creating piece {i + 1}...")
        piece, available_edges = create_piece(pieces, available_edges)
        if piece is None:
            print("Had to reset last piece, it made it impossible!")
            print(available_edges)
            available_edges = revert_available_edges(available_edges, pieces[-1])
            print(available_edges)
            pieces = pieces[:-1]
            continue
        pieces.append(piece)
        pieces, available_edges = adjust_pieces(pieces, available_edges)
        if i > 5:
            plot_puzzle(pieces)
        
        i += 1


# Example usage
create_puzzle()