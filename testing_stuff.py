from starting_points import *
from basic_functions import *
from shapely.geometry import Point, LineString, Polygon
import config


def is_piece_too_skinny(piece):
    angles = calculate_polygon_angles(piece)
    print(angles)
    if any(angle < config.min_angle_threshold or 
           angle > 2*math.pi - config.min_angle_threshold
           for angle in angles):
        return True
    else:
        return False

p1 = Polygon([(0.3705082176918692, -0.0157597269594846), 
(0.4952422551931858, -0.068812125902107), 
(0.499537404734132, 0.021503052608593), 
(0.4142330710546697, 0.0333557822325157), 
(0.3452132280805231, 0.1098411812998306), 
(0.2549089512295644, 0.1250397970723055), 
(0.3705082176918692, -0.0157597269594846)])

p2 = Polygon([(0.2312236816010503, 0.129026134432001), 
(0.2096358893829192, 0.2265974979633772), 
(-0.0962427172483482, 0.2338010755222715), 
(0.2312236816010503, 0.129026134432001)])

plot_puzzle([p1, p2])