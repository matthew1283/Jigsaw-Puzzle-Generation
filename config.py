from shapely.geometry import Point

# CREATION OF THE BORDER
radius = 0.5
center = Point(0,0)
circle = center.buffer(radius)
border = circle.boundary

border_area = border.area

#########################
### GENERAL VARIABLES ###
#########################

# Number of pieces of the puzzle
number_of_pieces = 30

# How random the length/area can be, +-%
length_distribution_factor = 0.2
area_distribution_factor = 0.5

# How jagged the pieces can be (internal angles)
min_angle_threshold = 0.2 # radians (11.5 degrees)

# How much bigger/shorter the last side can be to close the polygon
last_side_length_leniency = 5 

# Chance that a connector will generate on that piece edge
connector_on_edge_chance = 0.9 

# Number of times to run the puzzle generation (in the run_func_till_success() method)
# Useful for running multiple, putting into files, then picking your favorite
times_to_run = 1

# Set to True to see the plots of the puzzle generation: 
# NOTE: this will stop the code while the plots are open
see_plots = False




##############################
### UNDERLYING CONSTRAINTS ###
##############################

# Used a lot, usually within this limit is bad, means something is too skinny/close (too fine for laser cutting)
min_distance_threshold = 0.05 * radius

# Important!! Used to determine how close for pieces to be considered touching (i.e. adjacent)
touches_threshold = 1e-3 * radius

# How many times to try a particular stage (i.e. higher stage = more controlled piece generation)
stage_attempts_factor = 10

# How many times to try to generate the next point on a piece
point_guess_limit = 30

# How many times to try to generate the piece before it fills it in
max_piece_retry_count = 70*stage_attempts_factor

# Used in run_func_till_success(), how many times it can try to generate a puzzle before it gives up
max_number_of_puzzle_generation_retries = 10

# Scaling the connector down to fit within the bounds of the puzzle
connector_scale_factor_from_unit_circle = radius * 0.1

# How fine to make the pieces line up with the border
outline_edge_precision = 0.02




####################
### CALCULATIONS ###
####################

piece_area = border_area / number_of_pieces
upper_piece_area = piece_area * (1 + area_distribution_factor)
lower_piece_area = piece_area * (1 - area_distribution_factor)







connector_scale = 0.5


