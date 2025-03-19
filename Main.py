from shapely.geometry import Polygon, Point, LineString
from shapely.ops import nearest_points
import random
import math
from time import sleep
from collections import defaultdict

from basic_functions import *
from checks import *
from starting_points import *
import config
from edge_functions import *
from connector_interpreter import get_connectors

# import cProfile


clear_terminal()

random.seed(710912213223)


def remove_dupe_points(pieces):
    for i,p in enumerate(pieces):
        coords = p.exterior.coords
        dupe_index = []
        for j in range(len(coords)-1):
            point = Point(coords[j])
            next_point = Point(coords[j + 1])
            if touches_any(point, next_point):
                dupe_index.append(j)
        
        if len(dupe_index) > 0:
            new_p = []
            for k in range(len(coords)):
                if k not in dupe_index:
                    new_p.append(Point(coords[k]))
            pieces[i] = Polygon(new_p)
    return pieces

def point_recalibration(pieces):
    # Dictionary to store the first occurrence of each point
    point_mapping = {}

    # Iterate through all pieces and their points
    for i, piece in enumerate(pieces):
        new_points = []
        for coord in piece.exterior.coords[:-1]:
            point = Point(coord)

            # Check if this point is close to any previously mapped point
            matched = False
            for mapped_point in point_mapping:
                if touches_any(point, mapped_point):
                    # Use the mapped point's coordinates
                    new_points.append(mapped_point)
                    matched = True
                    break

            if not matched:
                # Add this point to the mapping and use its coordinates
                point_mapping[point] = point
                new_points.append(point)

        # Update the piece with the recalibrated coordinates
        new_points.append(new_points[0])
        pieces[i] = Polygon(new_points)

    return pieces

def calc_available_edges(pieces):
    # Create all edges from piece list
    edges = []
    for p in pieces:
        for i, point in enumerate(p.exterior.coords[:-1]):
            point = Point(point)
            next_point = Point(p.exterior.coords[(i + 1) % len(p.exterior.coords)])
            if touches_any(point, next_point):
                continue
            edges.append(LineString([point, next_point]))
    # Find out which edges are bad (used up, on outline)
    bad = []
    for i, edge1 in enumerate(edges):
        if is_edge_on_outline(edge1):
            bad.append(edge1)
            continue
        for j, edge2 in enumerate(edges):
            if i >= j:
                continue
            if is_edges_equal(edge1, edge2):
                bad.append(edge1)
                bad.append(edge2)
                break
    ae = [edge for edge in edges if not bad.__contains__(edge)]
    return ae

def save_puzzle_state(pieces, available_edges, filename):
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

def load_puzzle_state(filename):
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
            return piece, last_piece
    
    piece_retries = 0
    while True:
        if piece_retries > config.max_piece_retry_count:
            return None, last_piece

        points, angle = choose_start(piece_retries, pieces, ideal_length, available_edges)
        for s in range(num_sides - len(points)):
            vertex_guess_counter = 0
            while vertex_guess_counter < 20:
                length = calc_random_length(ideal_length)
                x = points[-1].x + length * math.cos(angle)
                y = points[-1].y + length * math.sin(angle)
                new_point = Point(x, y)

                if any(new_point.distance(forbidden) < config.min_distance_threshold for forbidden in forbidden_positions[s]):
                    angle += get_random_angle()
                    vertex_guess_counter += 1
                    continue

                if touches_any(new_point, config.outline):
                    angle += get_random_angle()
                    vertex_guess_counter += 1
                    continue
                
                if config.outline.distance(new_point) < config.min_distance_threshold:
                    new_point = nearest_points(config.outline, new_point)[0]

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
            piece_retries += 1
            continue
        points.append(points[0])
        piece = Polygon(points)
        if check_piece_fit(pieces, piece):
            print("This took "+str(piece_retries)+" attempts")
            return piece, last_piece
        else:
            piece_retries += 1
            forbidden_positions[2].append(points[2])
            # print(f"Added forbidden position for point {s}: {new_point}")

def adjust_pieces(pieces):
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

                    # Find the nearest point on piece2 to the current point
                    new_point = nearest_points(piece2, point)[0]

                    # Check if the new_point is on piece1's own edge (invalid case)
                    if is_point_on_polygon_edge(new_point, piece1):
                        continue

                    # Update the current point in piece1
                    new_coords_piece1 = list(piece1.exterior.coords)
                    new_coords_piece1[i] = (new_point.x, new_point.y)
                    adjusted_piece1 = Polygon(new_coords_piece1)

                    # Check if the adjusted piece1 is valid
                    if not adjusted_piece1.is_valid or not check_piece_fit([p for p in pieces if p != piece1], adjusted_piece1):
                        continue

                    # Update piece1 in the pieces list
                    pieces[idx1] = adjusted_piece1
                    
                    # Find the edge on piece2 that contains the new_point
                    edge_on_piece2 = find_edge_containing_point(piece2, new_point)
                    if edge_on_piece2:
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
                        if not adjusted_piece2.is_valid or not check_piece_fit([p for p in pieces if p != piece2], adjusted_piece2):
                            # Roll back changes to piece1
                            pieces[idx1] = original_piece1
                            continue

                        # Update piece2 in the pieces list
                        pieces[idx2] = adjusted_piece2


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
                            if not adjusted_piece3.is_valid or not check_piece_fit([p for p in pieces if p != piece3], adjusted_piece3):
                                continue

                            # Update piece3 in the pieces list
                            pieces[idx3] = adjusted_piece3
                    break  # Move to the next point in piece1
    return pieces

def fill_in_pieces(pieces, available_edges):
    usable_edges = []
    valid_pieces = []
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
            relevant_coords.append((max_point.x, max_point.y))
            relevant_coords.append((intersection_point.x, intersection_point.y))
            
            # Close the polygon by adding the first point again
            relevant_coords.append(relevant_coords[0])
            
            # Create the Polygon
            piece = Polygon(relevant_coords)
            if piece.is_valid and not is_piece_overlapping_pieces(piece, pieces):
                valid_pieces.append(piece)
                break
    return valid_pieces

def fill_in_piece_middle(pieces, available_edges):
    valid_pieces = []
    for piece_retries in range(110):
        points, angle = choose_start_for_middle(available_edges, piece_retries*config.stage_attempts_factor)
        points.append(points[0])
        piece = Polygon(points)
        
        if check_piece_fit_wo_area(pieces, piece) and piece.is_valid:
            entry = tuple([piece, abs(piece.area-calc_avg_piece_area(pieces))])
            if entry not in valid_pieces:
                valid_pieces.append(entry)
    #This gets the piece with the area closest to the ideal piece area
    best_valid_piece = min(valid_pieces, key=lambda x: x[1])[0]
    return best_valid_piece

def create_piece_for_middle(pieces, available_edges):
    num_sides = random.randint(4, 8)
    print("number_of_sides: "+str(num_sides))
    ideal_length = calculate_side_length(num_sides)
    points = []
    forbidden_positions = {i: [] for i in range(num_sides)}

    piece_retries = 0
    while True:
        if piece_retries > config.max_piece_retry_count:
            return None

        
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
                if temp_polygon.is_valid and not is_point_in_piece(pieces, new_point) \
                and not is_point_on_polygon_edge(new_point, temp_polygon):
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

        if check_piece_fit(pieces, piece) and piece.is_valid:
            print("This took "+str(piece_retries)+" attempts")
            return piece
        else:
            piece_retries += 1
            forbidden_positions[2].append(points[2])
            # print(f"Added forbidden position for point {s}: {new_point}")

def create_puzzle_edge():
    pieces = []
    available_edges = []

    # Create Outside Pieces
    while True:
        print(f"Creating piece {len(pieces) + 1}...")
        piece, last_piece = create_piece(pieces, available_edges)
        if piece is None:
            filled_pieces = fill_in_pieces(pieces, available_edges)
            pieces.extend(filled_pieces)
            print("Had to fill in pieces, it was impossible!")
        else:
            pieces.append(piece)
        pieces = remove_dupe_points(pieces)

        pieces = adjust_pieces(pieces)
        pieces = remove_dupe_points(pieces)
        available_edges = calc_available_edges(pieces)

        if last_piece:
            plot_puzzle(pieces, available_edges)
            break

    save_puzzle_state(pieces, available_edges, filename="puzzle_edges.txt")

def split_any_edges(piece, pieces):
    for coord in piece.exterior.coords:
        point = Point(coord)
        for i,p in enumerate(pieces):
            if touches_any(point, p):
                edge_on_piece2 = find_edge_containing_point(p, point)
                if edge_on_piece2 and not (touches_any(point, Point(edge_on_piece2.coords[0])) or touches_any(point, Point(edge_on_piece2.coords[1]))):
                    # Update piece2 in the pieces list
                    new_coords_p = list(p.exterior.coords)
                    for j in range(len(new_coords_p) - 1):
                        edge = LineString([new_coords_p[j], new_coords_p[j + 1]])
                        if is_edges_equal(edge, edge_on_piece2):
                            # Insert the new_point into piece2's coordinates
                            new_coords_p.insert(j + 1, (point.x, point.y))
                            break
                    pieces[i] = Polygon(new_coords_p)
    return pieces

def create_puzzle_middle():
    pieces, available_edges = load_puzzle_state("puzzle_edges.txt")

    last_piece = False
    # Create Middle Pieces
    while not last_piece:
        print(f"Creating middle piece {len(pieces) + 1}...")
        piece = create_piece_for_middle(pieces, available_edges)
        
        if piece is None:
            piece = fill_in_piece_middle(pieces, available_edges)
            print("Had to fill in pieces, it was impossible!")
        
        pieces = split_any_edges(piece, pieces)
        pieces.append(piece)
        pieces = remove_dupe_points(pieces)

        # Adjust pieces and update available_edges
        pieces = adjust_pieces(pieces)
        pieces = remove_dupe_points(pieces)
        pieces = point_recalibration(pieces)
        available_edges = calc_available_edges(pieces)

        if len(available_edges) == 0:
            last_piece = True
            print("Last Middle Piece Was Placed!")
            plot_puzzle(pieces)
            
        
        # if len(pieces) > 40:
        #     plot_puzzle(pieces)
        
    save_puzzle_state(pieces, available_edges, filename="puzzle_middle.txt")



def run_func_till_success(func):
    i = 0
    while True:
        try:
            func()
            print(f'Successfully completed {func}.')
            break
        except KeyboardInterrupt as e:
            raise e
        except Exception as e:
            print(f'Some error occured: {e}. Retrying...')
        finally:
            i += 1
            if i >= config.max_number_of_puzzle_generation_retries:
                print(f'Max retries reached on {func}. Exiting.')
                exit()
    

run_func_till_success(create_puzzle_edge)
run_func_till_success(create_puzzle_middle)

# TESTING TIMINGS
# cProfile.run('create_puzzle_edge()', 'timing_breakdown.txt')
# snakeviz timing_breakdown.txt