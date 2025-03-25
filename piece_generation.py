import math
from shapely.geometry import Point, Polygon
from shapely.strtree import STRtree
import random


import config
from basic_functions import calc_random_length, touches_any, get_random_angle, calc_avg_points, \
    calc_avg_piece_area, calculate_side_length, plot_puzzle, save_puzzle_state, load_puzzle_state
from checks import check_new_point, is_point_in_piece, is_edge_touching_outline, is_edge_in_piece, \
    check_piece_fit_wo_area, check_piece_fit
from starting_points import choose_start_for_middle, choose_start, add_points_to_middle
from piece_tweaking import post_piece_processing

def add_points_to_piece(num_sides, points, pieces, forbidden_positions, ideal_length, angle, piece_retries):
    for s in range(num_sides - len(points)):
        vertex_guess_counter = 0
        while vertex_guess_counter < config.point_guess_limit:
            length = calc_random_length(ideal_length)
            x = points[-1].x + length * math.cos(angle)
            y = points[-1].y + length * math.sin(angle)
            new_point = Point(x, y)

            if any(new_point.distance(forbidden) < config.min_distance_threshold for forbidden in forbidden_positions[s]):
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
            if len(points) <= 2 and temp_polygon.is_valid and not is_point_in_piece(pieces, new_point):
                points.append(new_point)
                angle += get_random_angle()
                break
            elif len(points) > 2 and temp_polygon.is_valid and not is_point_in_piece(pieces, new_point) \
            and not touches_any(new_point, Polygon(points)):
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
            return None, forbidden_positions, piece_retries
    last_edge_length = math.sqrt((points[-1].x - points[0].x)**2 + (points[-1].y - points[0].y)**2)
    if last_edge_length < ideal_length * (1-config.last_side_length_leniency*config.length_distribution_factor) or last_edge_length > ideal_length * (1+config.last_side_length_leniency*config.length_distribution_factor):
        piece_retries += 1
        return None, forbidden_positions, piece_retries
    points.append(points[0])
    piece = Polygon(points)
    return piece, forbidden_positions, piece_retries

def fill_in_pieces(pieces, available_edges):
    usable_edges = [edge for edge in available_edges if is_edge_touching_outline(edge)]
    valid_pieces = []
    tree = STRtree(pieces)
    for p in pieces:
        if is_edge_in_piece(usable_edges[0], p):
            piece1 = p
        elif is_edge_in_piece(usable_edges[1], p):
            piece2 = p
    for counter,p in enumerate([piece1, piece2]):
        touching_points = []
        for point in p.exterior.coords:
            for q in tree.query(Point(point)):
                if touches_any(Point(point), q):
                    touching_points.append(Point(point))
        touching_point_avg = calc_avg_points(touching_points)
        sorted_points = sorted(p.exterior.coords, key=lambda coord: 
                               Point(coord).distance(touching_point_avg), reverse=True)
        
        while len(sorted_points) > 0:
            max_point = Point(sorted_points.pop(0))

            direction_vector = (max_point.x - config.center.x, max_point.y - config.center.y)
            magnitude = math.sqrt(direction_vector[0]**2 + direction_vector[1]**2)
            normalized_vector = (direction_vector[0] / magnitude, direction_vector[1] / magnitude)
            intersection_point = Point(
                config.center.x + normalized_vector[0] * config.radius,
                config.center.y + normalized_vector[1] * config.radius
            )
            
            piece_coords = list(p.exterior.coords)
            usable_edge_coords = list(usable_edges[counter].coords)
            # Find the index of the usable_edge in the piece's exterior
            if touches_any(Point(usable_edge_coords[0]), config.outline):
                for i,coord in enumerate(piece_coords):
                    if touches_any(Point(usable_edge_coords[0]), Point(coord)):
                        start_index = i
            else:
                for i,coord in enumerate(piece_coords):
                    if touches_any(Point(usable_edge_coords[-1]), Point(coord)):
                        start_index = i
            for i,coord in enumerate(piece_coords):
                if touches_any(max_point, Point(coord)):
                    end_index = i
            # Extract the coordinates from the usable_edge to the max_point
            if start_index < end_index:
                relevant_coords = piece_coords[start_index:end_index + 1]
            else:
                relevant_coords = piece_coords[end_index:start_index + 1][::-1]
            
            # Add the max_point and intersection_point to the relevant coordinates
            # relevant_coords.append((max_point.x, max_point.y))
            relevant_coords.append((intersection_point.x, intersection_point.y))
            
            # Close the polygon by adding the first point again
            relevant_coords.append(relevant_coords[0])
            
            # Create the Polygon
            piece = Polygon(relevant_coords)
            if piece.is_valid and check_piece_fit_wo_area(pieces, piece):
                valid_pieces.append(piece)
                break
    return valid_pieces

def fill_in_piece_middle(pieces, available_edges):
    valid_pieces = []
    points, _ = choose_start_for_middle(available_edges)

    def add_points_recursive(points, remaining_points, results):
        if remaining_points == 0:
            results.append(points.copy())
            return

        # Try adding a point to the left
        point_to_add_to = points[0]
        tree = STRtree(available_edges)
        possible_touching_edges = tree.query(point_to_add_to)
        possible_touching_edges = [available_edges[i] for i in possible_touching_edges]
        for edge in possible_touching_edges:
            if touches_any(point_to_add_to, edge):
                if not touches_any(points[1], edge):
                    other_point = None
                    if touches_any(point_to_add_to, Point(edge.coords[0])):
                        other_point = Point(edge.coords[1])
                    else:
                        other_point = Point(edge.coords[0])
                    if other_point not in points:
                        points.insert(0, other_point)
                        add_points_recursive(points, remaining_points - 1, results)
                        points.pop(0)  # Backtrack

        # Try adding a point to the right
        point_to_add_to = points[-1]
        possible_touching_edges = tree.query(point_to_add_to)
        possible_touching_edges = [available_edges[i] for i in possible_touching_edges]
        for edge in possible_touching_edges:
            if touches_any(point_to_add_to, edge):
                if not touches_any(points[-2], edge):
                    other_point = None
                    if touches_any(point_to_add_to, Point(edge.coords[0])):
                        other_point = Point(edge.coords[1])
                    else:
                        other_point = Point(edge.coords[0])
                    if other_point not in points:
                        points.append(other_point)
                        add_points_recursive(points, remaining_points - 1, results)
                        points.pop()  # Backtrack

    for extra_point_count in range(5):
        results = []
        add_points_recursive(points, extra_point_count, results)
        for piece in results:
            piece.append(piece[0])
            piece = Polygon(piece)
            
            if piece.is_valid and check_piece_fit_wo_area(pieces, piece):
                entry = tuple([piece, abs(piece.area-calc_avg_piece_area(pieces))])
                if entry not in valid_pieces:
                    valid_pieces.append(entry)
    #This gets the piece with the area closest to the ideal piece area
    best_valid_piece = min(valid_pieces, key=lambda x: x[1])[0]
    return best_valid_piece

def create_piece(pieces, available_edges, piece_type):
    num_sides = random.randint(4, 8)
    # print("Number Of Sides: "+str(num_sides))
    ideal_length = calculate_side_length(num_sides)
    points = []
    forbidden_positions = {i: [] for i in range(num_sides)}

    piece_retries = 0
    while True:
        if piece_retries > config.max_piece_retry_count:
            return None
        
        if piece_type == "edge":
            points, angle = choose_start(piece_retries, pieces, ideal_length, available_edges)
        elif piece_type == "middle":
            points, angle = choose_start_for_middle(available_edges)
            points = add_points_to_middle(piece_retries, points, available_edges)

        piece, forbidden_positions, piece_retries = add_points_to_piece(num_sides, points, pieces, forbidden_positions, ideal_length, angle, piece_retries)
        
        if piece is None:
            continue

        if check_piece_fit(pieces, piece) and piece.is_valid:
            # print("This took "+str(piece_retries+1)+" attempts")
            return piece
        else:
            piece_retries += 1
            forbidden_positions[2].append(points[2])
            # print(f"Added forbidden position for point {s}: {new_point}")

def create_last_edge_piece(pieces, available_edges):
    if len(pieces) >= config.number_of_pieces / 4:
        points, _ = create_last_piece(available_edges)
        if points:
            # print("Last piece placed! YAYY!")
            piece = Polygon(points)
            points.append(points[0])
            return piece
    return None

def create_last_piece(available_edges):
    angle = get_random_angle()
    
    usable_edges = [edge for edge in available_edges if is_edge_touching_outline(edge)]

    # Try to find two edges that can form the last piece
    edge1 = list(usable_edges[0].coords)
    edge2 = list(usable_edges[1].coords)

    # Get the endpoints of the edges
    if touches_any(Point(edge1[0]), config.outline):
        edge1_circle_point = Point(edge1[0])
        edge1_other_point = Point(edge1[1])
    else:
        edge1_circle_point = Point(edge1[1])
        edge1_other_point = Point(edge1[0])
    if touches_any(Point(edge2[0]), config.outline):
        edge2_circle_point = Point(edge2[0])
        edge2_other_point = Point(edge2[1])
    else:
        edge2_circle_point = Point(edge2[1])
        edge2_other_point = Point(edge2[0])
    
    if edge1_circle_point.distance(edge2_circle_point) > config.last_side_length_leniency:
        return None, angle
    points = [edge1_other_point, edge1_circle_point, edge2_circle_point, edge2_other_point]
    return points, angle

def create_puzzle_edge():
    pieces = []
    available_edges = []
    last_piece = False
    
    # Create Outside Pieces
    while not last_piece:
        # print(f"Creating edge piece {len(pieces) + 1}...")
        piece = create_last_edge_piece(pieces, available_edges)

        if piece is None:
            piece = create_piece(pieces, available_edges, "edge")

        if piece is None:
            piece = fill_in_pieces(pieces, available_edges)
            # print("Had to fill in pieces, it was impossible!")

        pieces, available_edges = post_piece_processing(piece, pieces)

        usable_edges = [edge for edge in available_edges if is_edge_touching_outline(edge)]
        if len(usable_edges) == 0:
            last_piece = True
            # print("Last Edge Piece Was Placed!")
            plot_puzzle(pieces, available_edges)
    print("All Edge Pieces Placed!")
    save_puzzle_state(pieces, available_edges, filename="puzzle_edges.txt")

def create_puzzle_middle():
    pieces, available_edges = load_puzzle_state("puzzle_edges.txt")

    last_piece = False
    # Create Middle Pieces
    while not last_piece:
        # print(f"Creating middle piece {len(pieces) + 1}...")
        piece = create_piece(pieces, available_edges, "middle")
        
        if piece is None:
            piece = fill_in_piece_middle(pieces, available_edges)
            # print("Had to fill in pieces, it was impossible!")
        
        pieces, available_edges = post_piece_processing(piece, pieces)

        if len(available_edges) == 0:
            last_piece = True
            # print("Last Middle Piece Was Placed!")
            plot_puzzle(pieces)
    print("All Middle Pieces Placed!")
    save_puzzle_state(pieces, available_edges, filename="puzzle_middle.txt")





