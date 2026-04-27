# CPSC_440_Project
Project Repository for UBC CPSC 440 Course

## API Scaffold

This repository now includes a FastAPI scaffold in `api/`.

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the API

```bash
uvicorn api.main:app --reload
```

### Available endpoints

- `GET /health`
- `POST /gmm/fit`
- `POST /mdp/solve`

### Example request for `POST /gmm/fit`

```json
{
	"name": "Ryan",
	"club": "I7",
	"max_components": 10,
	"num_components": 1,
	"sample_size": 100
}
```

The endpoint uses the existing preprocessing and GMM model flow:

- `Utils/preprocess.py` to load and filter data
- `Models/GaussianMixture.py` to fit and sample

### Example request for `POST /mdp/solve`

```json
{
	"name": "Ryan",
	"clubs": ["I7"],
	"hole_type": "simple",
	"gmm_components": 1,
	"grid_step": 20,
	"num_samples": 100,
	"max_iterations": 50,
	"gamma": 0.99,
	"epsilon": 0.000001,
	"device": null
}
```

This endpoint uses existing project modules:

- `Models/GaussianMixture.py` to fit one GMM per requested club
- `Models/MDP.py` to build transitions and run value iteration
- `Simulation/golfhole.py` and `Simulation/holecomponent.py` to construct the selected hole
