import pandas as pd
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
path_ryan_griffin = BASE_DIR / "Data" / "RG_Data.csv"
path_caddie_set = BASE_DIR / "Data" / "CaddieSet.csv"

def preprocess_data():
    "Uses the data from caddieSet and ryan and griffin collection."
    "Combines the data into a single set with 4 columns, Name,Club,X,Y"

    ryan_griffin_data = pd.read_csv(path_ryan_griffin)
    caddie_set_data = pd.read_csv(path_caddie_set)

    # Keep only the columns needed to align with the Ryan Griffin schema.
    caddie_set_data = caddie_set_data[
        ["GolferId", "ClubType", "LrDistanceOut", "Carry"]
    ].rename(
        columns={
            "GolferId": "Name",
            "ClubType": "Club",
            "LrDistanceOut": "X",
            "Carry": "Y",
        }
    )

    combined_data = pd.concat([ryan_griffin_data, caddie_set_data], ignore_index=True)
    combined_data["Club"] = combined_data["Club"].replace("7i", "I7")

    # Keep only Name-Club pairings with more than 50 shots.
    pair_counts = combined_data.groupby(["Name", "Club"])["Club"].transform("size")
    combined_data = combined_data[pair_counts > 50].reset_index(drop=True)
    print(f"Combined dataset shape: {combined_data.shape}")

    return combined_data

preprocess_data()