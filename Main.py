from shapely.geometry import Polygon, Point, LineString
from shapely.ops import nearest_points, unary_union
import random
import math
import os
import shutil

from basic_functions import clear_terminal, touches_any, plot_puzzle, \
    load_puzzle_state, save_puzzle_state, rotate_array,save_puzzle_as_pic
from checks import is_edge_on_outline, is_adjacent
import config
from piece_generation import create_puzzle_edge, create_puzzle_middle
from add_connectors import create_piece_connectors



clear_terminal()

random.seed(710912213223)



def merge_two_pieces(smallest_piece, piece_to_merge_to):
    # Get the coordinates of both polygons
    smallest_coords = list(smallest_piece.exterior.coords[:-1])
    merge_coords = list(piece_to_merge_to.exterior.coords[:-1])

    # Find the shared edge (points where the two polygons touch)
    shared_points = []
    for i,coord in enumerate(smallest_coords):
        if touches_any(Point(coord), piece_to_merge_to):
            shared_points.append(coord)
            if not touches_any(Point(smallest_coords[(i + 1) % len(smallest_coords)]), piece_to_merge_to):
                last_point = smallest_coords[i]
            if not touches_any(Point(smallest_coords[(i - 1) % len(smallest_coords)]), piece_to_merge_to):
                first_point = smallest_coords[i]
    shared_points = rotate_array(shared_points, shared_points.index(last_point))
    
    if smallest_coords[smallest_coords.index(first_point)-1 % len(smallest_coords)] in shared_points:
        smallest_coords = smallest_coords[::-1]
    if merge_coords[merge_coords.index(first_point)-1 % len(merge_coords)] in shared_points:
        merge_coords = merge_coords[::-1]
    smallest_coords = rotate_array(smallest_coords, (smallest_coords.index(shared_points[0])-1) % len(smallest_coords))
    merge_coords = rotate_array(merge_coords, (merge_coords.index(shared_points[0])-1) % len(merge_coords))
    merge_coords = [mc for mc in merge_coords if mc not in shared_points[1:-1]]
    smallest_coords = [sc for sc in smallest_coords if sc not in shared_points]
    new_coords = [merge_coords[0]] + smallest_coords + merge_coords[1:]
    new_coords.append(new_coords[0])
    # Create the merged polygon
    merged_piece = Polygon(new_coords)
    if not merged_piece.is_valid:
        smallest_coords = smallest_coords[::-1]
        new_coords = [merge_coords[0]] + smallest_coords + merge_coords[1:]
        new_coords.append(new_coords[0])
        # Create the merged polygon
        merged_piece = Polygon(new_coords)
    return merged_piece

def merge_pieces(): 
    pieces, available_edges = load_puzzle_state("puzzle_middle.txt")
    
    # Sort pieces by area (smallest first)
    pieces.sort(key=lambda p: p.area)

    # Merge smaller pieces into larger adjacent pieces
    while len(pieces) > config.number_of_pieces:
        # Find the smallest piece
        smallest_piece = pieces[0]

        # Find an adjacent larger piece to merge with
        adjacent_pieces = []
        for piece in pieces[1:]:  # Skip the smallest piece
            if is_adjacent(smallest_piece, piece):
                adjacent_pieces.append(piece)

        adjacent_pieces.sort(key=lambda p: p.area)
        if adjacent_pieces:
            piece_to_merge_to = adjacent_pieces[0]

            # Merge the two pieces
            merged_piece = merge_two_pieces(smallest_piece, piece_to_merge_to)

            # Remove the smallest and adjacent pieces from the list
            smallest_piece_index = pieces.index(smallest_piece)
            del pieces[smallest_piece_index]
            piece_to_merge_to_index = pieces.index(piece_to_merge_to)
            del pieces[piece_to_merge_to_index]

            # Add the merged piece to the list
            pieces.append(merged_piece)

            # Re-sort the pieces by area
            pieces.sort(key=lambda p: p.area)

    plot_puzzle(pieces)
    # Save the updated puzzle state
    print("All Pieces Merged!")
    save_puzzle_state(pieces, available_edges, filename="puzzle_merged.txt")

def connect_to_outline():
    pieces, available_edges = load_puzzle_state("puzzle_merged.txt")
    
    for p, piece in enumerate(pieces):
        new_piece = []
        for i, coord in enumerate(piece.exterior.coords[:-1]):
            point = Point(coord)
            next_point = Point(piece.exterior.coords[(i + 1) % len(piece.exterior.coords)])
            new_piece.append(point)
            if is_edge_on_outline(LineString([point, next_point])):
                edge_length = math.sqrt((point.x - next_point.x)**2 + (point.y - next_point.y)**2)
                added_points = []
                num_points = math.floor(edge_length / config.outline_edge_precision)
                for j in range(num_points-1):
                    x = point.x + (next_point.x - point.x) * (j+1) / num_points
                    y = point.y + (next_point.y - point.y) * (j+1) / num_points
                    new_point = Point(x, y)
                    added_points.append(nearest_points(config.outline, new_point)[0])
                new_piece.extend(added_points)
        new_piece.append(new_piece[0])
        pieces[p] = Polygon(new_piece)
    
    plot_puzzle(pieces, [], False)
    print('All Pieces Connected to Outline!')
    save_puzzle_state(pieces, available_edges, filename="puzzle_outlined.txt")
    
def create_folder_and_save_files():
    i = 1
    while True:
        folder_name = f"puzzles/puzzle{i}"
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)  # Create the folder
            
            # List of files to move (modify as needed)
            files_to_move = [
                "puzzle_edges.txt",
                "puzzle_middle.txt",
                "puzzle_merged.txt",
                "puzzle_outlined.txt",
                "puzzle_connected.txt",
                "finished_puzzle.png"]
            
            # Move each file to the new folder
            for file in files_to_move:
                if os.path.exists(file):
                    shutil.move(file, os.path.join(folder_name, file))
                else:
                    print(f"Warning: {file} not found. Skipping.")
            
            print(f"Files Successfully Saved to {folder_name}/")
            break
        i += 1

def overall_process():
    seed = random.randint(0, 1000000)
    random.seed(seed)  # Seed the random number generator
    print(f"Seed For This Generation: {seed}")

    create_puzzle_edge()
    create_puzzle_middle()
    merge_pieces()
    connect_to_outline()
    create_piece_connectors()
    save_puzzle_as_pic()
    create_folder_and_save_files()

# Run the overall process for the specified number of times
# run_func_till_success(overall_process, config.times_to_run)

# TESTING TIMINGS
import cProfile
cProfile.run('create_puzzle_middle()', 'timing_breakdown_w_strtree.txt')
# snakeviz timing_breakdown.txt
