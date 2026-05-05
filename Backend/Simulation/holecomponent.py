import math
import numpy as np
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
        angle = math.radians(self.rotation)
        cos_angle = math.cos(-angle)
        sin_angle = math.sin(-angle)
        dx = x - self.center[0]
        dy = y - self.center[1]
        rotated_x = dx * cos_angle - dy * sin_angle
        rotated_y = dx * sin_angle + dy * cos_angle
        ellipse_value = (rotated_x**2 / self.semi_major_axis**2) + (rotated_y**2 / self.semi_minor_axis**2)
        return ellipse_value <= 1.0 + 1e-9

    def intersects_segment(self, x1, y1, x2, y2):
        """
        Check if line segment from (x1, y1) to (x2, y2) intersects the ellipse.
        Uses analytical solution - no sampling required.
        
        Returns:
            True if segment intersects or passes through ellipse, False otherwise
        """
        # Translate segment so ellipse center is at origin
        dx1 = x1 - self.center[0]
        dy1 = y1 - self.center[1]
        dx2 = x2 - self.center[0]
        dy2 = y2 - self.center[1]
        
        # Rotate segment by -rotation to align with axis-aligned ellipse
        angle = np.radians(self.rotation)
        cos_angle = np.cos(-angle)
        sin_angle = np.sin(-angle)
        
        # Rotated start point
        rx1 = dx1 * cos_angle - dy1 * sin_angle
        ry1 = dx1 * sin_angle + dy1 * cos_angle
        
        # Rotated end point
        rx2 = dx2 * cos_angle - dy2 * sin_angle
        ry2 = dx2 * sin_angle + dy2 * cos_angle
        
        # Check if either endpoint is inside ellipse (quick early exit)
        if (rx1**2 / self.semi_major_axis**2 + ry1**2 / self.semi_minor_axis**2) <= 1:
            return True
        if (rx2**2 / self.semi_major_axis**2 + ry2**2 / self.semi_minor_axis**2) <= 1:
            return True
        
        # Parametric line equation: P(t) = P1 + t*(P2 - P1), where t ∈ [0,1]
        # P(t) = (rx1, ry1) + t*((rx2 - rx1), (ry2 - ry1))
        # Let dx = rx2 - rx1, dy = ry2 - ry1
        # P(t) = (rx1 + t*dx, ry1 + t*dy)
        
        dx = rx2 - rx1
        dy = ry2 - ry1
        
        # Substitute into ellipse equation: (x/a)^2 + (y/b)^2 = 1
        # ((rx1 + t*dx)/a)^2 + ((ry1 + t*dy)/b)^2 = 1
        # 
        # Expand to get quadratic in t: A*t^2 + B*t + C = 0
        
        a = self.semi_major_axis
        b = self.semi_minor_axis
        
        A = (dx**2 / a**2) + (dy**2 / b**2)
        B = 2 * (rx1 * dx / a**2 + ry1 * dy / b**2)
        C = (rx1**2 / a**2 + ry1**2 / b**2) - 1

        # Degenerate or nearly-degenerate segment: the endpoint checks above
        # already handled the only intersection case that can occur here.
        if abs(A) < 1e-12:
            return False
        
        # Solve quadratic equation
        discriminant = B**2 - 4*A*C
        
        # No intersection if discriminant < 0
        if discriminant < -1e-12:
            return False
        discriminant = max(discriminant, 0.0)
        
        # Two solutions (possibly equal)
        sqrt_disc = np.sqrt(discriminant)
        t1 = (-B - sqrt_disc) / (2*A)
        t2 = (-B + sqrt_disc) / (2*A)
        
        # Check if either solution is in the segment range [0, 1]
        # Segment intersects if any t value is in [0, 1]
        if (0 <= t1 <= 1) or (0 <= t2 <= 1):
            return True
        
        # Also check if the segment is entirely inside the ellipse
        # (both endpoints outside but segment passes through)
        # This is covered by checking if 0 is between t1 and t2
        if t1 < 0 < t2 or t2 < 0 < t1:
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