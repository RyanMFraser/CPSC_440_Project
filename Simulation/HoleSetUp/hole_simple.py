from pathlib import Path
import sys

# Add project root (.../CPSC_440_Project) to import path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from Simulation.holecomponent import HoleComponent
from Simulation.golfhole import Hole

def create_hole():
    green = HoleComponent(center=(0, 350), semi_major_axis=40, semi_minor_axis=30, rotation=-25, comp_type="green")
    tee = HoleComponent(center=(0, 25), semi_major_axis=15, semi_minor_axis=15, rotation=0, comp_type="tee")
    pin = HoleComponent(center=(0, 350), semi_major_axis=3, semi_minor_axis=3, rotation=0, comp_type="pin")
    hole = Hole(
            size=(300, 400),
            components=[green, tee, pin],
            pin_location=(0, 350),
            tee_location=(0, 25),
            name="hole_simple",
        )
    hole.draw()

    return hole