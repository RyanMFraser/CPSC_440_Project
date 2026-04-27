from fastapi import FastAPI, HTTPException

from Models.GaussianMixture import GaussianMixtureModel
from Models.MDP import GolfHoleMDP
from Simulation.golfhole import Hole
from Simulation.holecomponent import HoleComponent
from Utils.DataManager import save_data, load_data

from .schemas import (
    DataUploadRequest,
    DataUploadResponse,
    GMMFitRequest,
    GMMFitResponse,
    MDPActionResponse,
    MDPSolveRequest,
    MDPSolveResponse,
)


app = FastAPI(
    title="CPSC 440 Golf API",
    version="0.1.0",
    description="API exposing core GMM functionality for golf shot dispersion.",
)


def _build_hole(hole_name: str) -> Hole:
    if hole_name == "simple":
        return Hole(
            size=(300, 400),
            components=[
                HoleComponent(center=(0, 350), semi_major_axis=40, semi_minor_axis=30, rotation=-25, comp_type="green"),
                HoleComponent(center=(0, 25), semi_major_axis=15, semi_minor_axis=15, rotation=0, comp_type="tee"),
                HoleComponent(center=(0, 350), semi_major_axis=3, semi_minor_axis=3, rotation=0, comp_type="pin"),
            ],
            pin_location=(0, 350),
            tee_location=(0, 25),
            name="hole_simple",
        )

    raise HTTPException(status_code=400, detail=f"Unsupported hole_name: {hole_name}")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/data/upload", response_model=DataUploadResponse)
def upload_data(request: DataUploadRequest) -> DataUploadResponse:
    try:
        save_data(request.id, request.rows, request.write_mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save data: {e}")

    return DataUploadResponse(
        id=request.id,
        write_mode=request.write_mode,
        saved_rows=len(request.rows),
        message="Data saved successfully.",
    )


@app.post("/gmm/fit", response_model=GMMFitResponse)
def fit_gmm(request: GMMFitRequest) -> GMMFitResponse:
    data = load_data(request.id)

    if data.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for id={request.id}",
        )
    
    ids = []

    for club in data["Club"].unique():
        if not isinstance(club, str):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid club value in data: {club}. All club values must be strings.",
            )
        club_data = data[data["Club"] == club]

        model = GaussianMixtureModel(
            max_components=request.max_components,
            num_components=request.num_components,
        )
        try:
            model.fit(club_data)
            model.save(id=f"{request.id}_{club}", overwrite=True)
            ids.append(f"{request.id}_{club}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


    return GMMFitResponse(
        n_models=int(len(ids)),
        model_ids = ids
    )


@app.post("/mdp/solve", response_model=MDPSolveResponse)
def solve_mdp(request: MDPSolveRequest) -> MDPSolveResponse:
    data = preprocess_data()

    fitted_clubs = []
    used_clubs = []

    player_df = data[data["Name"] == request.name].copy()

    if player_df.empty:
        raise HTTPException(
                status_code=404,
                detail=f"No rows found for name={request.name}",
            )

    for club, club_df in sorted(player_df.groupby("Club"), key=lambda x: x[0]):

        model = GaussianMixtureModel(
            max_components=request.gmm_components,
            num_components=request.gmm_components,
        )

        try:
            model.fit(club_df)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        fitted_clubs.append(model)
        used_clubs.append(club)

    hole = _build_hole(request.hole_type)

    try:
        mdp = GolfHoleMDP(hole, fitted_clubs, grid_step=10, device="cpu")

        value_function, policy = mdp.solve(num_samples=100, max_iterations=50, gamma=0.98)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MDP solve failed: {e}")
    

    return MDPSolveResponse(
        name=request.name,
        hole_type=request.hole_type,
        clubs=used_clubs,
        value_function=value_function.tolist() if value_function is not None else None,
        policy=[MDPActionResponse(club=used_clubs[action["club_index"]], target_x=action["target"][0], target_y=action["target"][1]) for action in policy] if policy is not None else None,
    )
