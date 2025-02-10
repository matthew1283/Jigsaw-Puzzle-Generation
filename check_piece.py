from basic_functions import touches_any


def is_piece_too_skinny(piece, min_angle_threshold):
    # Check if piece has angles too small (using minimum angle threshold)
    for angle in piece.convex_hull.minimum_rotated_rectangle.interiors:
        if angle < min_angle_threshold:
            return True
    return False

def is_surrounding_too_skinny(pieces, piece, min_distance_threshold):
    # Check if there are other pieces too close to the current piece
    for p in pieces:
        if piece.distance(p) < min_distance_threshold and not touches_any(p, piece):
            return True
    return False

def check_piece_fit(pieces, center, piece, radius, piece_area, area_distribution_factor):
    min_angle_threshold = 0.2 # radians (11.5 degrees)
    min_distance_threshold = 0.05 * radius # units
    # Issues: 1) out of border 2) intersects with other pieces 3) too small or too big
    if not center.buffer(radius * 1.01).covers(piece):
        print('uh oh piece out of border gotta try again')
        return False
    if piece.area < piece_area * (1 - area_distribution_factor) or piece.area > piece_area * (1 + area_distribution_factor):
        print('uh oh piece too small or too big gotta try again')
        return False
    for p in pieces:
        if piece.intersects(p) and not piece.touches(p):
            print('uh oh piece didnt fit gotta try again')
            return False
    if is_piece_too_skinny(piece, min_angle_threshold):
        print('uh oh piece is too skinny gotta try again')
        return False
    if is_surrounding_too_skinny(pieces, piece, min_distance_threshold):
        print('uh oh surroundings too skinny gotta try again')
        return False
    return True