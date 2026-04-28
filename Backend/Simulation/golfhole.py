import matplotlib.pyplot as plt
from pathlib import Path


class Hole:
    def __init__(self, size, components, pin_location, tee_location=None, name = None):
        self.x = size[0]
        self.y = size[1]
        self.components = components
        self.pin_location = pin_location
        self.tee_location = tee_location
        self.name = name


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

        output_dir = Path(__file__).resolve().parents[1] / "Output" / "Holes"
        output_dir.mkdir(parents=True, exist_ok=True)
        hole_name = str(self.name) if self.name else "hole"
        output_path = output_dir / f"{hole_name}.png"
        fig.savefig(output_path, bbox_inches="tight")

        return fig, ax









