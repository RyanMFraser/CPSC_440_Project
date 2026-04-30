from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

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
    GMMSpecRequest,
    GMMParamsResponse,
    MDPPolicyRequest,
    MDPPolicyResponse,
    MDPValueRequest,
    MDPValueResponse,
)


app = FastAPI(
    title="CPSC 440 Golf API",
    version="0.1.0",
    description="API exposing core GMM functionality for golf shot dispersion.",
)

# Allow the frontend dev server and localhost origins for browser access
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent.parent
PERSISTENCE_DIR = BASE_DIR / "Persistence"
DATA_DIR = PERSISTENCE_DIR / "Data"
MODELS_DIR = PERSISTENCE_DIR / "Models"
MDP_DIR = PERSISTENCE_DIR / "MDP"


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


@app.get("/")
def root() -> dict[str, str]:
    # Provide a simple root endpoint for health checks and preflight requests
    return {"status": "ok", "message": "CPSC 440 Golf API"}


@app.get("/ids")
def list_persisted_ids() -> dict[str, list[str]]:
    def list_json_stems(directory: Path) -> list[str]:
        if not directory.exists():
            return []
        return sorted(
            path.stem
            for path in directory.glob("*.json")
            if path.is_file()
        )

    return {
        "data_ids": list_json_stems(DATA_DIR),
        "gmm_ids": list_json_stems(MODELS_DIR),
        "mdp_ids": list_json_stems(MDP_DIR),
    }


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
    data = load_data(request.data_id)

    if data.empty:
        raise HTTPException(
            status_code=404,
            detail=f"No data found for id={request.data_id}",
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
            model.save(id=f"{request.data_id}_{club}", overwrite=True)
            ids.append(f"{request.data_id}_{club}")
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


@app.post("/gmm/params", response_model=GMMParamsResponse)
def get_gmm_params(request: GMMSpecRequest) -> GMMParamsResponse:
    model = GaussianMixtureModel()
    try:
        model.load(request.gmm_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Model not found: {request.gmm_id}")

    params = model.get_parameters()

    weights = params["weights"].tolist()
    means = params["means"].tolist()
    covariances = params["covariances"].tolist()

    return GMMParamsResponse(
        gmm_id=request.gmm_id,
        weights=weights,
        means=means,
        covariances=covariances,
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
        club_ids=mdp.get_club_ids(),
    )


@app.post("/mdp/value", response_model=MDPValueResponse)
def get_mdp_value(request: MDPValueRequest) -> MDPValueResponse:
    if "x" not in request.state or "y" not in request.state:
        raise HTTPException(status_code=400, detail="state must include both 'x' and 'y'.")

    state = (float(request.state["x"]), float(request.state["y"]))

    mdp = GolfHoleMDP(_build_hole(), [], grid_step=10, device="cpu")
    mdp.load(request.mdp_id)

    if mdp.value_function is None:
        raise HTTPException(status_code=400, detail="Value function not available. Solve the MDP first.")

    value = mdp.value_function.get(state, None)

    return MDPValueResponse(
        mdp_id=request.mdp_id,
        value=value,
        state={"x": state[0], "y": state[1]},
        club_ids=mdp.get_club_ids(),
    )
