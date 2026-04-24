import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path


class Hole:
    def __init__(self, size, components, pin_location, tee_location=None):
        self.x = size[0]
        self.y = size[1]
        self.components = components
        self.pin_location = pin_location
        self.tee_location = tee_location


    def draw(self):
        fig, ax = plt.subplots()
        fairway_green = "#7fb069"
        fig.patch.set_facecolor("white")
        ax.set_facecolor(fairway_green)

        for component in self.components:
            # Support component draw methods that either accept an axes object
            # or manage their own plotting internally.
            try:
                component.draw(ax)
            except TypeError:
                component.draw()

        ax.set_xlim(-self.x /2, self.x /2)
        ax.set_ylim(0, self.y)
        ax.set_aspect("equal", adjustable="box")

        output_dir = Path(__file__).resolve().parent / "HoleRendering"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / "hole.png"
        fig.savefig(output_path, bbox_inches="tight")

        # Flip the saved raster so it aligns with imshow(..., origin="lower")
        # when the PNG is used as a background image in the notebook.
        rendered = plt.imread(output_path)
        plt.imsave(output_path, np.flipud(rendered))

        return fig, ax









