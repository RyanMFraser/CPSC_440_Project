from pathlib import Path
import sys


# Add project root (.../CPSC_440_Project) to import path
sys.path.append(str(Path(__file__).resolve().parents[2]))
from Simulation.holecomponent import HoleComponent
from Simulation.golfhole import Hole

def create_hole():
    green = HoleComponent(center=(55, 350), semi_major_axis=20, semi_minor_axis=15, rotation=-25, comp_type="green")
    tee = HoleComponent(center=(55, 25), semi_major_axis=15, semi_minor_axis=15, rotation=0, comp_type="tee")
    left_trees = HoleComponent(center=(-300, 100), semi_major_axis=150, semi_minor_axis=300, rotation=35, comp_type="tree")
    left_water = HoleComponent(center=(-200, 350), semi_major_axis=70, semi_minor_axis=150, rotation=-55, comp_type="water")
    left_bunker = HoleComponent(center=(-125, 250), semi_major_axis=30, semi_minor_axis=50, rotation=-55, comp_type="bunker")
    green_bunker = HoleComponent(center=(125, 350), semi_major_axis=30, semi_minor_axis=50, rotation=-35, comp_type="bunker")
    # right_trees = HoleComponent(center=(145, 100), semi_major_axis=150, semi_minor_axis=30, rotation=-45, comp_type="tree")
    right_tree_2 = HoleComponent(center=(300, 265), semi_major_axis=150, semi_minor_axis=300, rotation=-25, comp_type="tree")
    pin = HoleComponent(center=(50, 350), semi_major_axis=3, semi_minor_axis=3, rotation=0, comp_type="pin")
    hole = Hole(size=(500, 400), components=[green, tee, left_trees, left_water, left_bunker, green_bunker, right_tree_2, pin], pin_location=(50, 350), tee_location=(55, 25))
    hole.draw()
    return hole




if __name__ == "__main__":
    from Simulation.holecomponent import HoleComponent
    from Simulation.golfhole import Hole
    
    create_hole()
