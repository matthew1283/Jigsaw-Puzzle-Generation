from collections import defaultdict
from shapely.geometry import Point, LineString, Polygon
from shapely.strtree import STRtree
from shapely.ops import nearest_points

import config
from basic_functions import touches_any, find_edge_containing_point
from checks import is_edge_on_outline, check_piece_fit, is_edges_equal



def post_piece_processing(piece, pieces):
    if isinstance(piece, list):
        for p in piece:
            p, pieces = split_any_edges(p, pieces)
            pieces.append(p)
    else:
        piece, pieces = split_any_edges(piece, pieces)
        pieces.append(piece)
    
    pieces = remove_dupe_points(pieces)

    # Adjust pieces and update available_edges
    pieces = adjust_pieces(pieces)
    pieces = remove_dupe_points(pieces)
    pieces = point_recalibration(pieces)
    available_edges = calc_available_edges(pieces)
    return pieces, available_edges

def calc_available_edges(pieces):
    # Dictionary to store edge counts and detect duplicates
    edge_counts = defaultdict(int)
    edge_list = []
    edge_to_index = {}
    
    # First pass: collect all edges and count occurrences
    for p in pieces:
        coords = p.exterior.coords
        for i in range(len(coords) - 1):
            point1 = Point(coords[i])
            point2 = Point(coords[i + 1])
            
            if touches_any(point1, point2):
                continue
                
            # Create a normalized edge (sorted points to avoid duplicate edges in different directions)
            normalized_edge = tuple(sorted([(point1.x, point1.y), (point2.x, point2.y)]))
            
            # Store the actual LineString
            linestring = LineString([point1, point2])
            
            if normalized_edge not in edge_to_index:
                edge_to_index[normalized_edge] = len(edge_list)
                edge_list.append(linestring)
            
            edge_counts[normalized_edge] += 1
    
    # Second pass: identify available edges
    available_edges = []
    for normalized_edge, count in edge_counts.items():
        idx = edge_to_index[normalized_edge]
        edge = edge_list[idx]
        
        if count == 1 and not is_edge_on_outline(edge):
            available_edges.append(edge)
    
    return available_edges

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

def adjust_pieces(pieces):
    tree = STRtree(pieces)
    for idx1, piece1 in enumerate(pieces):  # Iterate over all pieces
        for i, point in enumerate(piece1.exterior.coords[:-1]):  # Iterate over exterior coordinates (excluding the last duplicate)
            point = Point(point)  # Convert coordinate to Point object

            # Skip points that are on the outline
            if touches_any(point, config.outline):
                continue

            # Check if the point is too close to another piece but not touching it
            possible_pieces_indicies = tree.query(point)
            possible_pieces = [pieces[i] for i in possible_pieces_indicies]
            for idx2, piece2 in enumerate(possible_pieces):
                if piece1 == piece2:
                    continue  # Skip the same piece

                if piece2.distance(point) < config.min_distance_threshold and not touches_any(piece2, point):
                    # Save the original state of the pieces in case we need to roll back
                    original_piece1 = pieces[idx1]
                    original_piece2 = pieces[possible_pieces_indicies[idx2]]

                    # Find the nearest point on piece2 to the current point
                    new_point = nearest_points(piece2, point)[0]

                    # Check if the new_point is on piece1's own edge (invalid case)
                    if touches_any(new_point, piece1):
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
                        pieces[possible_pieces_indicies[idx2]] = adjusted_piece2


                    # Update all pieces that share the old point or edge
                    for idx3, piece3 in enumerate(possible_pieces):
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
                            pieces[possible_pieces_indicies[idx3]] = adjusted_piece3
                    break  # Move to the next point in piece1
    return pieces

def split_edge(piece, point, new_coords_p):
    edge_on_piece2 = find_edge_containing_point(piece, point)
    if edge_on_piece2 and not (touches_any(point, Point(edge_on_piece2.coords[0])) or touches_any(point, Point(edge_on_piece2.coords[1]))):
        # Update piece2 in the pieces list
        for j in range(len(new_coords_p) - 1):
            edge = LineString([new_coords_p[j], new_coords_p[j + 1]])
            if is_edges_equal(edge, edge_on_piece2):
                # Insert the new_point into piece2's coordinates
                new_coords_p.insert(j + 1, (point.x, point.y))
                break
    return new_coords_p

def split_any_edges(piece, pieces):
    tree = STRtree(pieces)
    # Checks for points that intersect other piece edges
    for coord in piece.exterior.coords:
        point = Point(coord)
        possible_pieces_indicies = tree.query(point)
        possible_pieces = [pieces[i] for i in possible_pieces_indicies]
        for i,p in enumerate(possible_pieces):
            new_coords_p = list(p.exterior.coords)
            if touches_any(point, p):
                new_coords_p = split_edge(p, point, new_coords_p)
                pieces[possible_pieces_indicies[i]] = Polygon(new_coords_p)
    # Checks for points on other pieces that intersect with piece edges
    new_coords_p = list(piece.exterior.coords)
    for i,p in enumerate(pieces):
        for coord in p.exterior.coords:
            point = Point(coord)
            if touches_any(point, piece):
                new_coords_p = split_edge(piece, point, new_coords_p)
                piece = Polygon(new_coords_p)
    return piece, pieces
