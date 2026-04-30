from pathlib import Path
import sys

# Add project root (.../CPSC_440_Project) to import path
sys.path.append(str(Path(__file__).resolve().parents[2]))

def create_hole():
    green = HoleComponent(center=(55, 350), semi_major_axis=20, semi_minor_axis=15, rotation=-25, comp_type="green")
    tee = HoleComponent(center=(55, 25), semi_major_axis=15, semi_minor_axis=15, rotation=0, comp_type="tee")
    left_trees = HoleComponent(center=(-100, 100), semi_major_axis=40, semi_minor_axis=200, rotation=0, comp_type="tree")
    left_water = HoleComponent(center=(-75, 350), semi_major_axis=40, semi_minor_axis=100, rotation=-45, comp_type="water")
    left_bunker = HoleComponent(center=(-55, 300), semi_major_axis=30, semi_minor_axis=50, rotation=-55, comp_type="bunker")
    right_trees = HoleComponent(center=(110, 150), semi_major_axis=70, semi_minor_axis=30, rotation=-45, comp_type="tree")
    right_tree_2 = HoleComponent(center=(125, 325), semi_major_axis=40, semi_minor_axis=150, rotation=-15, comp_type="tree")
    pin = HoleComponent(center=(55, 350), semi_major_axis=3, semi_minor_axis=3, rotation=0, comp_type="pin")
    hole = Hole(size=(200, 400), components=[green, tee, left_trees, left_water, left_bunker, right_trees, right_tree_2, pin], pin_location=(55, 350), tee_location=(55, 25))
    hole.draw()




if __name__ == "__main__":
    from Simulation.holecomponent import HoleComponent
    from Simulation.golfhole import Hole
    
    create_hole()
