# Golf Shot Dispersion & Strategy Optimization

A full-stack application that models golf shot dispersion patterns and computes optimal hole strategies using Gaussian Mixture Models and Markov Decision Processes.

---

## Overview

This project combines **shot dispersion modeling** with **decision optimization** to analyze golfer performance and recommend optimal strategies for completing golf holes.

**Key capabilities:**
- Fit Gaussian Mixture Models to real golf shot data
- Build Markov Decision Process models of hole layouts
- Solve for optimal shot strategies using value iteration
- Interactive web interface for visualization and analysis

For detailed methodology and results, see [Golf_Dispersion_Report.pdf](Golf_Dispersion_Report.pdf).

---

## Architecture

```
Frontend (React + Vite)
         ↓
    FastAPI Backend
         ↓
   Core Models (GMM, MDP)
         ↓
   Golf Hole Simulation
```

---

## Quick Start

### Backend Setup

```bash
cd Backend
pip install -r requirements.txt
uvicorn api.main:app --reload
```

The API will be available at `http://localhost:8000`

**API Endpoints:**
- `GET /health` — Health check
- `POST /gmm/fit` — Fit Gaussian Mixture Model to shot data
- `POST /mdp/solve` — Solve optimal strategy for a hole
- `POST /mdp/policy` — Get recommended action from a position
- `POST /mdp/score_distribution` — Simulate score outcomes

### Frontend Setup

```bash
cd Frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:5173`

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| **Backend** | FastAPI, PyTorch, NumPy |
| **Frontend** | React, Vite, Plotly.js |
| **ML Models** | Scikit-learn (GMM), PyTorch (GPU acceleration) |
| **Simulation** | Custom golf hole engine |

---

## Core Modules

- **`Models/GaussianMixture.py`** — Shot dispersion modeling
- **`Models/MDP.py`** — Hole strategy optimization via value iteration
- **`Simulation/`** — Golf hole geometry and shot physics
- **`api/`** — REST API endpoints
- **`Frontend/src/`** — React UI components

---

## Learn More

See **[Golf_Dispersion_Report.pdf](Golf_Dispersion_Report.pdf)** for:
- Mathematical formulation
- Experimental methodology
- Performance analysis
- Detailed results

---
