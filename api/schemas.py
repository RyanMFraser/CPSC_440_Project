from typing import Literal, Optional

from pydantic import BaseModel, Field


class GMMFitRequest(BaseModel):
    max_components: int = Field(10, ge=1, le=25)
    num_components: Optional[int] = Field(None, ge=1, le=25)
    id: str = Field(..., min_length=1, description="Dataset id to load for fitting the GMM")


class GMMFitResponse(BaseModel):
    n_models: int
    model_ids: list[str]


class MDPSolveRequest(BaseModel):
    id: str = Field(..., min_length=1, description="ID for saving the MDP solution output")
    models_list: list[str] = Field(..., min_length=1, description="List of GMM model ids to load for solving the MDP")
    grid_step: int = Field(10, ge=1, le=50)


class MDPActionResponse(BaseModel):
    club: str
    target_x: float
    target_y: float


class MDPSolveResponse(BaseModel):
    models_list: list[str]
    id: str
    value_function: Optional[list[float]] = None
    policy: Optional[list[MDPActionResponse]] = None


class DataUploadRequest(BaseModel):
    id: str = Field(..., min_length=1, description="Dataset id used for the output JSON filename")
    rows: list[dict] = Field(..., min_length=1, description="Array of JSON row objects")
    write_mode: Literal["overwrite", "append"] = Field(
        "overwrite",
        description="Whether to overwrite existing data or append to it",
    )


class DataUploadResponse(BaseModel):
    id: str
    write_mode: Literal["overwrite", "append"]
    saved_rows: int
    message: str
