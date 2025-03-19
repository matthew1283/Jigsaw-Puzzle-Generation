from shapely.geometry import Polygon, Point, LineString
from shapely.ops import nearest_points
from time import sleep
from collections import defaultdict
import random
import math
from shapely.affinity import translate, rotate, scale

from basic_functions import *
from checks import *
from starting_points import *
import config
from edge_functions import *
from connector_interpreter import get_connectors

def get_all_edges(pieces):
    edge_to_pieces = defaultdict(list)  # Dictionary to store edges and their associated piece indices

    for i, piece in enumerate(pieces):
        # Get the exterior coordinates of the piece
        coords = list(piece.exterior.coords)

        # Iterate through the edges of the piece
        for j in range(len(coords) - 1):
            # Create a LineString for the edge
            edge = LineString([coords[j], coords[j + 1]])

            # Check if the edge is on the outline
            if is_edge_on_outline(edge):
                continue
            found = False
            for existing_edge in edge_to_pieces.keys():
                if is_edges_equal(edge, existing_edge):
                    edge_to_pieces[existing_edge].append(i)
                    found = True
                    break
            # Add the edge to the dictionary with the piece index
            if not found:
                edge_to_pieces[edge].append(i)

    return edge_to_pieces

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

def create_piece_connectors(pieces):
    # Get all edges (excluding edges on the outline) and their associated piece indices
    edges = get_all_edges(pieces)
    
    # Load the connectors
    connectors = get_connectors()

    # Iterate through each edge
    for i,(edge, piece_indices) in enumerate(edges.items()):
        print(f"Processing edge {i+1} of {len(edges)}")
        edge_works = True
        # Step 1: Use config.connector_on_edge_chance to determine if a connector is placed
        if random.random() < config.connector_on_edge_chance:
            old_pieces = pieces.copy()  # Make a copy of the pieces to check for overlaps
            # Step 1.5: Randomly choose a connector
            connector = random.choice(connectors)
            connector = scale(connector, xfact=config.connector_scale, yfact=config.connector_scale, origin=(0, 0))
            # Step 2: Configure the connector to fit in the middle of the edge
            # Calculate the midpoint of the edge
            edge_midpoint = Point(
                (edge.coords[0][0] + edge.coords[1][0]) / 2,
                (edge.coords[0][1] + edge.coords[1][1]) / 2)

            # Calculate the angle of the edge
            dx = edge.coords[1][0] - edge.coords[0][0]
            dy = edge.coords[1][1] - edge.coords[0][1]
            edge_angle = math.degrees(math.atan2(dy, dx))

            # Step 2.5: Calculate the initial angle of the connector's edge
            connector_coords = list(connector.exterior.coords)
            connector_edge = LineString([connector_coords[0], connector_coords[-2]])
            connector_midpoint = Point(
                (connector_edge.coords[0][0] + connector_edge.coords[1][0]) / 2,
                (connector_edge.coords[0][1] + connector_edge.coords[1][1]) / 2)
            connector_dx = connector_edge.coords[1][0] - connector_edge.coords[0][0]
            connector_dy = connector_edge.coords[1][1] - connector_edge.coords[0][1]
            connector_initial_angle = math.degrees(math.atan2(connector_dy, connector_dx))


            # Calculate the required rotation angle
            rotation_angle = edge_angle - connector_initial_angle + 180*random.choice([0,1]) # Add random inversion for both sides of connectors
            shift_x = edge_midpoint.x - connector_midpoint.x
            shift_y = edge_midpoint.y - connector_midpoint.y
            # Scale, rotate, and translate the connector to fit the edge
            connector = rotate(connector, rotation_angle, origin=connector_midpoint)
            connector = translate(connector, xoff=shift_x, yoff=shift_y)

            # Step 3: Insert the connector into the pieces
            for piece_index in piece_indices:
                # Get the piece and its exterior coordinates
                piece = pieces[piece_index]
                coords = list(piece.exterior.coords)

                # Find the index of the edge in the piece's exterior coordinates
                for i in range(len(coords) - 1):
                    if (coords[i] == edge.coords[0] and coords[i + 1] == edge.coords[1]) or \
                       (coords[i] == edge.coords[1] and coords[i + 1] == edge.coords[0]):
                        # Insert the connector's coordinates into the piece's exterior coordinates
                        connector_coords = list(connector.exterior.coords[:-1]) # Remove last point as it = 1st point (for closed Polygon)
                        if Point(coords[i]).distance(Point(connector_coords[0])) > Point(coords[i + 1]).distance(Point(connector_coords[0])):
                            connector_coords = connector_coords[::-1] # Reverse the order of the connector if needed
                        coords[i + 1:i + 1] = connector_coords

                        new_piece = Polygon(coords)
                        # Update the piece with the new coordinates if it fits
                        if not is_piece_overlapping_pieces(new_piece, [p for i,p in enumerate(pieces) if i not in piece_indices]):
                            old_pieces[piece_index] = new_piece
                        else:
                            edge_works = False
                        break
                if not edge_works:
                    break
            if edge_works:
                pieces = old_pieces
    return pieces

pieces, available_edges = load_puzzle_state('puzzle_middle.txt')

new_pieces = create_piece_connectors(pieces)

plot_puzzle(new_pieces)

