import math

# Simulation/holecomponent.py
import matplotlib.patches as patches

TYPE_COLORS = {
    "green": "#5FAF5F",
    "fairway": "#7FB069",
    "bunker": "#E6D3A3",
    "water": "#4F9FD9",
    "tee": "#4B8B3B",
    "tree": "#083008",
    "pin": "#D7263D",
}

DEFAULT_COLOR = "#888888"


class HoleComponent:
    def __init__(self, center, semi_major_axis, semi_minor_axis, rotation, comp_type):
        self.center = center
        self.semi_major_axis = semi_major_axis
        self.semi_minor_axis = semi_minor_axis
        self.rotation = rotation
        self.type = comp_type

    def contains(self, x, y):
        # Check if the point (x, y) is within the ellipse defined by the hole
        cos_angle = math.cos(-self.rotation)
        sin_angle = math.sin(-self.rotation)
        dx = x - self.center[0]
        dy = y - self.center[1]
        rotated_x = dx * cos_angle - dy * sin_angle
        rotated_y = dx * sin_angle + dy * cos_angle
        return (rotated_x**2 / self.semi_major_axis**2) + (rotated_y**2 / self.semi_minor_axis**2) <= 1

    def intersects_segment(self, x1, y1, x2, y2):
        # For simplicity, we can sample points along the segment and check for containment.
        num_samples = 1000
        for i in range(num_samples + 1):
            t = i / num_samples
            sample_x = x1 + t * (x2 - x1)
            sample_y = y1 + t * (y2 - y1)
            if self.contains(sample_x, sample_y):
                return True
        return False

    def draw(self, ax, alpha=0.7):
        color = TYPE_COLORS.get(self.type, DEFAULT_COLOR)

        ellipse = patches.Ellipse(
            xy=self.center,
            width=2 * self.semi_major_axis,
            height=2 * self.semi_minor_axis,
            angle=self.rotation,  # if stored in degrees
            facecolor=color,
            edgecolor="#2f2f2f",
            linewidth=1.0,
            alpha=alpha,
            zorder=3
        )
        ax.add_patch(ellipse)