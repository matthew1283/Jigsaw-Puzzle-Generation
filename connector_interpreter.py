from PIL import Image
import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from skimage import measure
from shapely import affinity
import os

from basic_functions import plot_puzzle
import config

def plot_contour(contour):
    plt.figure(figsize=(8, 8))
    plt.plot(contour[:, 1], contour[:, 0], linewidth=2, color="black")  # Plot the contour
    plt.gca().invert_yaxis()  # Invert the y-axis to match the image orientation
    plt.gca().set_aspect("equal")
    plt.axis("off")
    plt.show()

def extract_polygon_from_image(image_path):
    image = Image.open(image_path)

    # Convert to grayscale
    image_gray = image.convert("L")
    # Convert to binary mask (black line = 1, white background = 0)
    binary_mask = np.array(image_gray) < 128  # Threshold to separate black line from white background

    # Find contours in the binary mask
    contours = measure.find_contours(binary_mask, 0.5)
    contour = contours[0]  # Use only the first contour found

    # Convert the contour to a polygon and return it
    polygon = Polygon(contour)

    # Scale the polygon down to fit within the unit circle
    scale_factor = config.connector_scale_factor_from_unit_circle / max(polygon.bounds[2], polygon.bounds[3])
    scaled_polygon = affinity.scale(polygon, xfact=scale_factor, yfact=scale_factor, origin=(0, 0))
    return scaled_polygon

def get_connectors():
    connectors = []
    i = 1  # Start with connector1.png
    while True:
        image_path = f"connector{i}.png"

        # Check if the file exists
        if not os.path.exists(image_path):
            break  # Exit the loop if the file doesn't exist

        # Extract the polygon from the image
        polygon = extract_polygon_from_image(image_path)
        connectors.append(polygon)

        # Increment the counter for the next file
        i += 1

    return connectors

