from matplotlib.patches import Ellipse
import numpy as np

def draw_ellipse(mean, cov, ax, color):
    # Eigen decomposition
    vals, vecs = np.linalg.eigh(cov)

    # Sort eigenvalues (largest first)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]

    # Angle of ellipse
    angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))

    # 1 standard deviation = sqrt(eigenvalues)
    width, height = 2 * np.sqrt(vals)  # factor 2 = full width

    ellipse = Ellipse(
        xy=mean,
        width=width,
        height=height,
        angle=angle,
        color=color,
        alpha=0.2  # shading
    )

    ax.add_patch(ellipse)