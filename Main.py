from shapely.geometry import Polygon, Point, LineString
from shapely.ops import nearest_points
import random
import math
from time import sleep

from basic_functions import *
from checks import *
from starting_points import *
import config
from edge_functions import *


clear_terminal()
#seed with errors = 62, 129
random.seed(129)

def save_puzzle_state(pieces, available_edges, filename="puzzle_state.txt"):
    with open(filename, "w") as file:
        # Save pieces
        file.write("Pieces:\n")
        for i, piece in enumerate(pieces):
            file.write(f"Piece {i + 1}:\n")
            for coord in piece.exterior.coords:
                file.write(f"  {coord}\n")
        
        # Save available edges
        file.write("\nAvailable Edges:\n")
        for i, edge in enumerate(available_edges):
            file.write(f"Edge {i + 1}:\n")
            for coord in edge.coords:
                file.write(f"  {coord}\n")

def load_puzzle_state(filename="puzzle_state.txt"):
    pieces = []
    available_edges = []

    with open(filename, "r") as file:
        lines = file.readlines()
        i = 0
        while i < len(lines):
            if lines[i].startswith("Piece"):
                # Read piece coordinates
                coords = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith("("):
                    coord = tuple(map(float, lines[i].strip().strip("()").split(",")))
                    coords.append(coord)
                    i += 1
                if coords:
                    pieces.append(Polygon(coords))
            elif lines[i].startswith("Edge"):
                # Read edge coordinates
                coords = []
                i += 1
                while i < len(lines) and lines[i].strip().startswith("("):
                    coord = tuple(map(float, lines[i].strip().strip("()").split(",")))
                    coords.append(coord)
                    i += 1
                if coords:
                    available_edges.append(LineString(coords))
            else:
                i += 1

    return pieces, available_edges

def create_piece(pieces, available_edges):
    num_sides = random.randint(4, 8)
    print("number_of_sides: "+str(num_sides))
    ideal_length = calculate_side_length(num_sides)
    points = []
    last_piece = False
    forbidden_positions = {i: [] for i in range(num_sides)}

    # For LAST PIECE
    if len(pieces) >= config.number_of_pieces // 4:
        points, angle = create_last_piece(available_edges)
        if points:
            last_piece = True
            print("Last piece placed! YAYY!")
            piece = Polygon(points)
            points.append(points[0])
            available_edges = update_available_edges(available_edges, piece)
            return piece, available_edges, last_piece
    
    piece_retries = 0
    while True:
        if piece_retries > config.max_piece_retry_count:
            return None, available_edges, last_piece

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
        if check_piece_fit(pieces, piece):
            available_edges = update_available_edges(available_edges, piece)
            print("This took "+str(piece_retries)+" attempts")
            return piece, available_edges, last_piece
        else:
            piece_retries += 1
            forbidden_positions[2].append(points[2])
            # print(f"Added forbidden position for point {s}: {new_point}")

def adjust_pieces_orig(pieces: list[Polygon], available_edges: list[LineString]):
    old_edges = []  # Track edges that are being replaced
    new_edges = []  # Track edges that are being added

    for idx1, piece1 in enumerate(pieces):  # Iterate over all pieces
        for i, point in enumerate(piece1.exterior.coords[:-1]):  # Iterate over exterior coordinates (excluding the last duplicate)
            point = Point(point)  # Convert coordinate to Point object

            # Skip points that are on the outline
            if touches_any(point, config.outline):
                continue

            # Check if the point is too close to another piece but not touching it
            for idx2, piece2 in enumerate(pieces):
                if piece1 == piece2:
                    continue  # Skip the same piece

                if piece2.distance(point) < config.min_distance_threshold and not touches_any(piece2, point):
                    # Save the original state of the pieces in case we need to roll back
                    original_piece1 = pieces[idx1]
                    original_piece2 = pieces[idx2]

                    # Get the previous and next points in piece1's exterior ring
                    previous_point = Point(piece1.exterior.coords[i - 1])
                    next_point = Point(piece1.exterior.coords[(i + 1) % len(piece1.exterior.coords)])

                    # Find the nearest point on piece2 to the current point
                    new_point = nearest_points(piece2, point)[0]

                    # Update the current point in piece1
                    new_coords_piece1 = list(piece1.exterior.coords)
                    new_coords_piece1[i] = (new_point.x, new_point.y)
                    adjusted_piece1 = Polygon(new_coords_piece1)

                    # Check if the adjusted piece1 is valid
                    if not adjusted_piece1.is_valid:
                        print("Adjustment makes piece1 invalid. Skipping.")
                        continue

                    # Check if the adjusted piece1 overlaps with any other piece
                    overlaps = any(is_piece_overlapping_piece(p, piece1) for p in pieces if p != piece1)
                    if overlaps:
                        print("Adjustment causes overlaps. Skipping.")
                        continue

                    # Update piece1 in the pieces list
                    pieces[idx1] = adjusted_piece1

                    # Record the old and new edges for piece1
                    old_edge = LineString([previous_point, point])
                    new_edge = LineString([next_point, new_point])

                    # Find the edge on piece2 that contains the new_point
                    edge_on_piece2 = find_edge_containing_point(piece2, new_point)
                    if edge_on_piece2:
                        # Split the edge on piece2 into two edges at the new_point
                        split_edges = split_edge(edge_on_piece2, new_point)

                        # Update piece2 in the pieces list
                        new_coords_piece2 = list(piece2.exterior.coords)
                        for j in range(len(new_coords_piece2) - 1):
                            edge = LineString([new_coords_piece2[j], new_coords_piece2[j + 1]])
                            if is_edges_equal(edge, edge_on_piece2):
                                # Insert the new_point into piece2's coordinates
                                new_coords_piece2.insert(j + 1, (new_point.x, new_point.y))
                                break
                        adjusted_piece2 = Polygon(new_coords_piece2)

                        # Check if the adjusted piece2 is valid
                        if not adjusted_piece2.is_valid:
                            print("Adjustment makes piece2 invalid. Skipping.")
                            # Roll back changes to piece1
                            pieces[idx1] = original_piece1
                            continue

                        # Check if the adjusted piece2 overlaps with any other piece
                        overlaps = any(is_piece_overlapping_piece(p, piece2) for p in pieces if p != piece2)
                        if overlaps:
                            print("Adjustment causes overlaps. Skipping.")
                            # Roll back changes to piece1
                            pieces[idx1] = original_piece1
                            continue

                        # Update piece2 in the pieces list
                        pieces[idx2] = adjusted_piece2

                        # Record the old and new edges for piece2
                        old_edges.append(edge_on_piece2)
                        new_edges.extend(split_edges)

                    # Record the old and new edges for piece1
                    old_edges.append(old_edge)
                    new_edges.append(new_edge)

                    break  # Move to the next point in piece1

    # Update available_edges by removing old edges and adding new ones
    for edge in old_edges:
        available_edges = [ae for ae in available_edges if not is_edges_equal(ae, edge)]

    for edge in new_edges:
        # Skip invalid edges (e.g., edges with the same start and end point)
        if edge.length > 0 and not any(is_edges_equal(edge, ae) for ae in available_edges):
            # Check if the edge overlaps with any existing piece
            overlaps = any(piece.intersects(edge) for piece in pieces)
            if not overlaps:
                available_edges.append(edge)

    return pieces, available_edges

def adjust_pieces(pieces: list[Polygon], available_edges: list[LineString]):
    old_edges = []  # Track edges that are being replaced
    new_edges = []  # Track edges that are being added

    for idx1, piece1 in enumerate(pieces):  # Iterate over all pieces
        for i, point in enumerate(piece1.exterior.coords[:-1]):  # Iterate over exterior coordinates (excluding the last duplicate)
            point = Point(point)  # Convert coordinate to Point object

            # Skip points that are on the outline
            if touches_any(point, config.outline):
                continue

            # Check if the point is too close to another piece but not touching it
            for idx2, piece2 in enumerate(pieces):
                if piece1 == piece2:
                    continue  # Skip the same piece

                if piece2.distance(point) < config.min_distance_threshold and not touches_any(piece2, point):
                    # Save the original state of the pieces in case we need to roll back
                    original_piece1 = pieces[idx1]
                    original_piece2 = pieces[idx2]

                    # Get the previous and next points in piece1's exterior ring
                    previous_point = Point(piece1.exterior.coords[i - 1])
                    next_point = Point(piece1.exterior.coords[(i + 1) % len(piece1.exterior.coords)])

                    # Find the nearest point on piece2 to the current point
                    new_point = nearest_points(piece2, point)[0]

                    # Check if the new_point is on piece1's own edge (invalid case)
                    if is_point_on_polygon_edge(new_point, piece1):
                        print("New point is on piece1's own edge. Skipping.")
                        continue

                    # Update the current point in piece1
                    new_coords_piece1 = list(piece1.exterior.coords)
                    new_coords_piece1[i] = (new_point.x, new_point.y)
                    adjusted_piece1 = Polygon(new_coords_piece1)

                    # Check if the adjusted piece1 is valid
                    if not adjusted_piece1.is_valid:
                        print("Adjustment makes piece1 invalid. Skipping.")
                        continue

                    # Check if the adjusted piece1 overlaps with any other piece
                    overlaps = any(is_piece_overlapping_piece(p, piece1) for p in pieces if p != piece1)
                    if overlaps:
                        print("Adjustment causes overlaps. Skipping.")
                        continue

                    # Update piece1 in the pieces list
                    pieces[idx1] = adjusted_piece1

                    # Record the old and new edges for piece1
                    old_edge = LineString([previous_point, point])
                    new_edge = LineString([next_point, new_point])

                    # Find the edge on piece2 that contains the new_point
                    edge_on_piece2 = find_edge_containing_point(piece2, new_point)
                    if edge_on_piece2:
                        # Split the edge on piece2 into two edges at the new_point
                        split_edges = split_edge(edge_on_piece2, new_point)

                        # Update piece2 in the pieces list
                        new_coords_piece2 = list(piece2.exterior.coords)
                        for j in range(len(new_coords_piece2) - 1):
                            edge = LineString([new_coords_piece2[j], new_coords_piece2[j + 1]])
                            if is_edges_equal(edge, edge_on_piece2):
                                # Insert the new_point into piece2's coordinates
                                new_coords_piece2.insert(j + 1, (new_point.x, new_point.y))
                                break
                        adjusted_piece2 = Polygon(new_coords_piece2)

                        # Check if the adjusted piece2 is valid
                        if not adjusted_piece2.is_valid:
                            print("Adjustment makes piece2 invalid. Skipping.")
                            # Roll back changes to piece1
                            pieces[idx1] = original_piece1
                            continue

                        # Check if the adjusted piece2 overlaps with any other piece
                        overlaps = any(is_piece_overlapping_piece(p, piece2) for p in pieces if p != piece2)
                        if overlaps:
                            print("Adjustment causes overlaps. Skipping.")
                            # Roll back changes to piece1
                            pieces[idx1] = original_piece1
                            continue

                        # Update piece2 in the pieces list
                        pieces[idx2] = adjusted_piece2

                        # Record the old and new edges for piece2
                        old_edges.append(edge_on_piece2)
                        new_edges.extend(split_edges)

                    # Record the old and new edges for piece1
                    old_edges.append(old_edge)
                    new_edges.append(new_edge)

                    # Update all pieces that share the old point or edge
                    for idx3, piece3 in enumerate(pieces):
                        if piece3 == piece1 or piece3 == piece2:
                            continue  # Skip the pieces we've already updated

                        # Check if piece3 shares the old point
                        if any(touches_any(Point(coord), point) for coord in piece3.exterior.coords):
                            # Update the shared point in piece3
                            new_coords_piece3 = list(piece3.exterior.coords)
                            for k, coord in enumerate(new_coords_piece3):
                                if touches_any(Point(coord), point):
                                    new_coords_piece3[k] = (new_point.x, new_point.y)
                            adjusted_piece3 = Polygon(new_coords_piece3)

                            # Check if the adjusted piece3 is valid
                            if not adjusted_piece3.is_valid:
                                print("Adjustment makes piece3 invalid. Skipping.")
                                continue

                            # Check if the adjusted piece3 overlaps with any other piece
                            overlaps = any(is_piece_overlapping_piece(p, piece3) for p in pieces if p != piece3)
                            if overlaps:
                                print("Adjustment causes overlaps. Skipping.")
                                continue

                            # Update piece3 in the pieces list
                            pieces[idx3] = adjusted_piece3

                    break  # Move to the next point in piece1

    # Update available_edges by removing old edges and adding new ones
    for edge in old_edges:
        available_edges = [ae for ae in available_edges if not is_edges_equal(ae, edge)]

    for edge in new_edges:
        # Skip invalid edges (e.g., edges with the same start and end point)
        if edge.length > 0 and not any(is_edges_equal(edge, ae) for ae in available_edges):
            # Check if the edge overlaps with any existing piece
            overlaps = any(piece.intersects(edge) for piece in pieces)
            if not overlaps:
                available_edges.append(edge)

    return pieces, available_edges

def fill_in_pieces(pieces, available_edges):
    usable_edges = []
    # print(available_edges)
    for edge in available_edges:
        if is_edge_touching_outline(edge):
            usable_edges.append(edge)

    for p in pieces:
        if is_edge_in_piece(usable_edges[0], p):
            piece1 = p
        elif is_edge_in_piece(usable_edges[1], p):
            piece2 = p
    for counter,p in enumerate([piece1, piece2]):
        max_distance = 0
        touching_points = []
        for point in p.exterior.coords:
            for q in pieces:
                if touches_any(Point(point), q):
                    touching_points.append(Point(point))
        touching_point_avg = calc_avg_points(touching_points)
        sorted_points = sorted(p.exterior.coords, key=lambda coord: 
                               Point(coord).distance(touching_point_avg), reverse=True)
        
        while True:
            try:
                max_point = Point(sorted_points.pop(0))
            except:
                break
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
            relevant_coords.append((max_point.x, max_point.y))
            relevant_coords.append((intersection_point.x, intersection_point.y))
            
            # Close the polygon by adding the first point again
            relevant_coords.append(relevant_coords[0])
            
            # Create the Polygon
            piece = Polygon(relevant_coords)
            if piece.is_valid and not is_piece_overlapping_pieces(piece, pieces):
                pieces.append(piece)
                # plot_puzzle([piece])
                available_edges = update_available_edges(available_edges, piece)
                break
    return pieces, available_edges

def create_piece_for_middle(pieces, available_edges):
    num_sides = random.randint(4, 8)
    print("number_of_sides: "+str(num_sides))
    ideal_length = calculate_side_length(num_sides)
    points = []
    last_piece = False
    forbidden_positions = {i: [] for i in range(num_sides)}

    piece_retries = 0
    while True:
        if piece_retries > config.max_piece_retry_count:
            return None, available_edges, last_piece

        points, angle = choose_start_for_middle(available_edges, piece_retries)
        for s in range(num_sides - len(points)):
            vertex_guess_counter = 0
            while vertex_guess_counter < config.point_guess_limit:
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
        
        if check_piece_fit(pieces, piece):
            available_edges = update_available_edges(available_edges, piece)
            print("This took "+str(piece_retries)+" attempts")
            return piece, available_edges, last_piece
        else:
            piece_retries += 1
            forbidden_positions[2].append(points[2])
            # print(f"Added forbidden position for point {s}: {new_point}")

def create_puzzle():
    pieces = []
    available_edges = []

    # Create Outside Pieces
    while True:
        print(f"Creating piece {len(pieces) + 1}...")
        piece, available_edges, last_piece = create_piece(pieces, available_edges)
        if piece is None:
            pieces, available_edges = fill_in_pieces(pieces, available_edges)
            print("Had to fill in pieces, it was impossible!")
        else:
            pieces.append(piece)

        pieces, available_edges = adjust_pieces(pieces, available_edges)

        if len(pieces) > 1 and len(pieces) % 2 == 0:
            plot_puzzle(pieces)

        if last_piece:
            plot_puzzle(pieces)
            break
    
    # save_puzzle_state(pieces, available_edges, filename="puzzle_state.txt")

def create_puzzle2():
    pieces, available_edges = load_puzzle_state()
    # Create Middle Pieces
    while len(pieces) < config.number_of_pieces+10:
        print(f"Creating middle piece {len(pieces) + 1}...")
        piece, available_edges, last_piece = create_piece_for_middle(pieces, available_edges)
        
        pieces.append(piece)
        
        # Adjust pieces and update available_edges
        pieces, available_edges = adjust_pieces(pieces, available_edges)
        
        print(piece)
        if len(pieces) > 28:
            plot_puzzle(pieces)


    print("Puzzle generation complete!")

# Example usage
create_puzzle()
