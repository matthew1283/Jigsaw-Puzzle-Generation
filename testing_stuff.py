from starting_points import *
from basic_functions import *
from shapely.geometry import Point, LineString, Polygon
import config

from shapely.strtree import STRtree

from checks import *


pieces, available_edges = load_puzzle_state('puzzle_middle.txt')

# Create a spatial index for the pieces
spatial_index = STRtree(pieces)


print(spatial_index)
print()

results = spatial_index.query(pieces[10])  # Query for a point within the puzzle
print(pieces[10])

r = [p for i, p in enumerate(pieces) if i in results]
plot_puzzle([pieces[10]])
plot_puzzle(r)

