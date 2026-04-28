from typing import Literal, Optional

from pydantic import BaseModel, Field


class GMMFitRequest(BaseModel):
    max_components: int = Field(10, ge=1, le=25)
    num_components: Optional[int] = Field(None, ge=1, le=25)
    gmm_id: str = Field(..., min_length=1, description="Dataset id to load for fitting the GMM")


class GMMFitResponse(BaseModel):
    n_models: int
    gmm_ids: list[str]


class MDPSolveRequest(BaseModel):
    mdp_id: str = Field(..., min_length=1, description="ID for saving the MDP solution output")
    gmm_ids: list[str] = Field(..., min_length=1, description="List of GMM model ids to load for solving the MDP")
    grid_step: int = Field(10, ge=1, le=50)


class MDPActionResponse(BaseModel):
    club: str
    target_x: float
    target_y: float


class MDPSolveResponse(BaseModel):
    gmm_ids: list[str]
    mdp_id: str


class DataUploadRequest(BaseModel):
    gmm_id: str = Field(..., min_length=1, description="Dataset id used for the output JSON filename")
    rows: list[dict] = Field(..., min_length=1, description="Array of JSON row objects")
    write_mode: Literal["overwrite", "append"] = Field(
        "overwrite",
        description="Whether to overwrite existing data or append to it",
    )


class DataUploadResponse(BaseModel):
    gmm_id: str
    write_mode: Literal["overwrite", "append"]
    saved_rows: int
    message: str

class GMMSampleRequest(BaseModel):
    gmm_id: str = Field(..., min_length=1, description="ID of the GMM model to sample from")
    n_samples: int = Field(100, ge=1, le=10000, description="Number of samples to generate")

class GMMSampleResponse(BaseModel):
    gmm_id: str
    samples: list[list[float]]


class GMMSpecRequest(BaseModel):
    gmm_id: str = Field(..., min_length=1, description="ID of the GMM model to get parameters for")


class GMMParamsResponse(BaseModel):
    gmm_id: str
    weights: list[float]
    means: list[list[float]]
    covariances: list[list[list[float]]]

class MDPPolicyRequest(BaseModel):
    mdp_id: str = Field(
        "Ryan_MDP",
        min_length=1,
        description="ID of the MDP solution to retrieve the policy for",
        examples=["Ryan_MDP"],
    )
    state: dict = Field(
        default_factory=lambda: {"x": 0.0, "y": 25.0},
        description="Current position on the hole. Must include numeric 'x' and 'y'.",
        examples=[{"x": 0.0, "y": 25.0}],
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "mdp_id": "Ryan_MDP",
                "state": {
                    "x": 0.0,
                    "y": 25.0,
                },
            }
        }
    }

class MDPPolicyResponse(BaseModel):
    mdp_id: str
    policy: Optional[dict] = None
    state: dict  


class MDPValueRequest(BaseModel):
    mdp_id: str = Field(
        "Ryan_MDP",
        min_length=1,
        description="ID of the MDP solution to retrieve the value for",
        examples=["Ryan_MDP"],
    )
    state: dict = Field(
        default_factory=lambda: {"x": 0.0, "y": 25.0},
        description="Current position on the hole. Must include numeric 'x' and 'y'.",
        examples=[{"x": 0.0, "y": 25.0}],
    )


class MDPValueResponse(BaseModel):
    mdp_id: str
    value: Optional[float] = None
    state: dict
