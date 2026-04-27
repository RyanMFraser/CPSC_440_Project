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
    GMMSampleRequest,
    GMMSampleResponse,
    MDPPolicyRequest,
    MDPPolicyResponse
)


app = FastAPI(
    title="CPSC 440 Golf API",
    version="0.1.0",
    description="API exposing core GMM functionality for golf shot dispersion.",
)


def _build_hole() -> Hole:
    
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

    


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/data/upload", response_model=DataUploadResponse)
def upload_data(request: DataUploadRequest) -> DataUploadResponse:
    try:
        save_data(request.gmm_id, request.rows, request.write_mode)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save data: {e}")

    return DataUploadResponse(
        gmm_id=request.gmm_id,
        write_mode=request.write_mode,
        saved_rows=len(request.rows),
        message="Data saved successfully.",
    )


@app.post("/gmm/fit", response_model=GMMFitResponse)
def fit_gmm(request: GMMFitRequest) -> GMMFitResponse:
    data = load_data(request.gmm_id)

    if data.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for id={request.gmm_id}",
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
            model.save(id=f"{request.gmm_id}_{club}", overwrite=True)
            ids.append(f"{request.gmm_id}_{club}")
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))


    return GMMFitResponse(
        n_models=int(len(ids)),
        gmm_ids = ids
    )


@app.post("/mdp/solve", response_model=MDPSolveResponse)
def solve_mdp(request: MDPSolveRequest) -> MDPSolveResponse:
    club_models = request.gmm_ids
    if not club_models:
        raise HTTPException(status_code=400, detail="gmm_ids cannot be empty")
    
    

    hole = _build_hole()

    try:
        mdp = GolfHoleMDP(hole, club_models, grid_step=10, device="cpu")
        mdp.solve(num_samples=100, max_iterations=50, gamma=0.98)
        mdp.save(request.mdp_id, overwrite=True)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MDP solve failed: {e}")
    

    return MDPSolveResponse(
        mdp_id = request.mdp_id,
        gmm_ids=club_models,
    )

@app.post("/gmm/sample", response_model=GMMSampleResponse)
def sample_gmm(request: GMMSampleRequest) -> GMMSampleResponse:
    model = GaussianMixtureModel()
    model.load(request.gmm_id)

    sample_points, _ = model.sample(n_samples=request.n_samples)

    return GMMSampleResponse(
        gmm_id=request.gmm_id,
        samples=sample_points.tolist(),
    )

@app.post("/mdp/policy")
def get_mdp_policy(request: MDPPolicyRequest) -> MDPPolicyResponse:
    if "x" not in request.state or "y" not in request.state:
        raise HTTPException(status_code=400, detail="state must include both 'x' and 'y'.")

    state = (float(request.state["x"]), float(request.state["y"]))

    # Load from persisted policy; hole and clubs are not used for policy lookup.
    mdp = GolfHoleMDP(_build_hole(), [], grid_step=10, device="cpu")
    mdp.load(request.mdp_id)
    try:
        action = mdp.get_policy_for_state(state)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    policy = None
    if action is not None:
        policy = {
            "club_idx": int(action[0]),
            "target_x": float(action[1]),
            "target_y": float(action[2]),
        }

    return MDPPolicyResponse(
        mdp_id=request.mdp_id,
        policy=policy,
        state={"x": state[0], "y": state[1]},
    )
