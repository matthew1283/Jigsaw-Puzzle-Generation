import config
from shapely.geometry import Point, LineString, Polygon
from basic_functions import touches_any

def update_available_edges(available_edges, piece):

    coords = list(piece.exterior.coords)
    for i in range(len(coords)):
        used_up = False
        point1 = Point(coords[i])
        point2 = Point(coords[(i + 1) % len(coords)])  # Wrap around to the first point

        if touches_any(point1, point2):
            continue

        edge = LineString([point1, point2])
        if touches_any(point1, config.outline) and touches_any(point2, config.outline): # Skip edges on the outline
            continue
        
        for existing_edge in available_edges[:]: # Remove pre-existing edges 
            if touches_any(point1, existing_edge) and touches_any(point2, existing_edge):
                available_edges.remove(existing_edge)
                used_up = True
                continue

        if not used_up:
            available_edges.append(edge)
    return available_edges

def revert_available_edges(available_edges, piece):
    outline = config.center.buffer(config.radius).boundary  # Circle outline

    # Iterate over the edges of the piece being removed
    coords = list(piece.exterior.coords)
    for i in range(len(coords)):
        point1 = Point(coords[i])
        point2 = Point(coords[(i + 1) % len(coords)])  # Wrap around to the first point
        edge = LineString([point1, point2])

        # Skip edges on the outline
        if touches_any(point1, outline) and touches_any(point2, outline):
            continue

        # Remove the edge from available_edges if it was added by this piece
        if edge in available_edges:
            available_edges.remove(edge)
            print(f"Removed edge from available_edges: {edge}")

        # Re-add edges that were removed when this piece was added
        # (This requires tracking which edges were removed when the piece was added)
        # For now, assume that any edge touching this piece's edge should be re-added
        for existing_edge in available_edges[:]:
            if touches_any(point1, existing_edge) and touches_any(point2, existing_edge):
                available_edges.append(existing_edge)
                print(f"Re-added edge to available_edges: {existing_edge}")

    return available_edges

def find_edge_containing_point(piece: Polygon, point: Point) -> LineString:
    coords = list(piece.exterior.coords)
    for i in range(len(coords) - 1):
        edge = LineString([coords[i], coords[i + 1]])
        if touches_any(edge, point):
            return edge
    return None

def split_edge(edge: LineString, point: Point) -> list[LineString]:
    """Split an edge into two edges at a given point."""
    coords = list(edge.coords)
    for i in range(len(coords) - 1):
        segment = LineString([coords[i], coords[i + 1]])
        if segment.distance(point) < config.touches_threshold:
            return [
                LineString([coords[i], (point.x, point.y)]),
                LineString([(point.x, point.y), coords[i + 1]])
            ]
    return [edge]

