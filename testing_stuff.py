from starting_points import is_edge_shared
from basic_functions import touches_any, plot_puzzle
from shapely.geometry import Point, LineString, Polygon
import config


def update_available_edges(available_edges, piece):
    outline = config.center.buffer(config.radius).boundary  # Circle outline

    coords = list(piece.exterior.coords)
    for i in range(len(coords)):
        used_up = False
        point1 = Point(coords[i])
        point2 = Point(coords[(i + 1) % len(coords)])  # Wrap around to the first point
        edge = LineString([point1, point2])

        if touches_any(point1, outline) and touches_any(point2, outline): # Skip edges on the outline
            continue
        
        for existing_edge in available_edges[:]: # Remove pre-existing edges 
            if touches_any(point1, existing_edge) and touches_any(point2, existing_edge):
                available_edges.remove(existing_edge)
                used_up = True
                continue

        if not used_up:
            available_edges.append(edge)

    return available_edges

center = Point(0, 0)

piece = Polygon([(0.1558138493697397, 0.4751021409597983), 
                (0.0983202788063661, 0.4902378226692005), 
                (0.0884860407100238, 0.4412030199765011), 
                (0.0447291060684318, 0.3915575777163378), 
                (0.0263967263463847, 0.3331930793782943), 
                (-0.0113483806528873, 0.2714593443815841), 
                (-0.0314671650866549, 0.2032256428765404), 
                (-0.0484526474329989, 0.134990748125333), 
                (-0.0276531496350525, 0.0838017048344632), 
                (-0.0276531496350525, 0.0838017048344632), 
                (0.1558138493697397, 0.4751021409597983)])

# print(update_available_edges([], piece))



from shapely.geometry import Polygon
import numpy as np
import math





piece = Polygon([(0,0), (0,.1), (.1, .15), (.2, .15), (.1, 0.14), (0,0)])


