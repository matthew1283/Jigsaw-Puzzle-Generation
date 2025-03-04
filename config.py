from shapely.geometry import Point
import math

# Creation of the circle outline
radius = 0.5
center = Point(0,0)
circle = center.buffer(radius)
outline = circle.boundary
circle_area = circle.area


number_of_pieces = 30  # Number of pieces of the puzzle
length_distribution_factor = 0.2 # Factor for length, +-50%
last_side_length_leniency = 5 # How much bigger/shorter the last side can be to close the polygon
last_piece_thickness = 0.3 * radius

min_distance_threshold = 0.05 * radius
touches_threshold = 1e-3 * radius
min_angle_threshold = 0.2 # radians (11.5 degrees)
max_angle_change = 3 * math.pi / 8
stage_attempts_factor = 10
point_guess_limit = 30

max_piece_retry_count = 70*stage_attempts_factor

piece_area = circle_area / number_of_pieces
area_distribution_factor = 0.5  # Factor for area distribution, +-50%
upper_piece_area = piece_area * (1 + area_distribution_factor)
lower_piece_area = piece_area * (1 - area_distribution_factor)