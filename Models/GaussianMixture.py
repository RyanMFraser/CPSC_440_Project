import json
from pathlib import Path

import numpy as np
from sklearn.mixture import GaussianMixture
from Models.EneryDistance import gmm_energy_distance
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "Persistence" / "Models"

class GaussianMixtureModel:
    def __init__(self, max_components = 10, num_components = None):
        self.max_components = max_components
        self.num_components = num_components
        self.gmm = None

    

    def fit(self, data):
        if not hasattr(data, "columns") or not {"X", "Y"}.issubset(data.columns):
            raise ValueError("Input data must contain 'X' and 'Y' columns.")

        features = data[["X", "Y"]].to_numpy()

        if self.num_components is not None:
            self.gmm = GaussianMixture(n_components=self.num_components, random_state=42)
            self.gmm.fit(features)
        else:
            features_train, features_val = train_test_split(
                features,
                test_size=0.10,
                random_state=42,
                shuffle=True
            )
            gmms = []
            model_scores = []

            for i in range(self.max_components):
                gmm = GaussianMixture(n_components=i + 1, random_state=42)
                gmm.fit(features_train)
                bic_value = gmm.bic(features_train)
                gmm_ed = gmm_energy_distance(gmm, features_val, n_samples=1000, random_state=42)
                gmms.append(gmm)
                model_scores.append((i, bic_value, gmm_ed))
            
            best_model_index = self.get_best_model(model_scores)
            self.num_components = best_model_index + 1
            self.fit(data)
            


    def get_best_model(self, model_scores):
        top_by_energy = sorted(model_scores, key=lambda x: x[2])[: min(3, len(model_scores))]
        best_model_index, _, _ = min(top_by_energy, key=lambda x: x[1])
        return best_model_index


    def get_parameters(self):
        if self.gmm is None:
            raise ValueError("Model has not been fitted yet.")
        return {
            "weights": self.gmm.weights_,
            "means": self.gmm.means_,
            "covariances": self.gmm.covariances_
        }
    
    def sample(self, n_samples=100):
        if self.gmm is None:
            raise ValueError("Model has not been fitted yet.")
        return self.gmm.sample(n_samples=n_samples)

    def save(self, id, overwrite=True):
        if self.gmm is None:
            raise ValueError("Model has not been fitted yet.")

        file_path = MODEL_DIR / f"{id}.json"
        if file_path.exists() and not overwrite:
            raise FileExistsError(f"Model file already exists: {file_path}")

        payload = {
            "id": id,
            "max_components": int(self.max_components),
            "num_components": int(self.num_components),
            "weights": self.gmm.weights_.tolist(),
            "means": self.gmm.means_.tolist(),
            "covariances": self.gmm.covariances_.tolist(),
        }

        MODEL_DIR.mkdir(parents=True, exist_ok=True)
        with file_path.open("w", encoding="utf-8") as json_file:
            json.dump(payload, json_file, indent=2)

    def load(self, id):
        file_path = MODEL_DIR / f"{id}.json"
        if not file_path.exists():
            raise FileNotFoundError(f"Model file not found: {file_path}")

        with file_path.open("r", encoding="utf-8") as json_file:
            payload = json.load(json_file)

        self.max_components = int(payload["max_components"])
        self.num_components = int(payload["num_components"])

        weights = np.asarray(payload["weights"], dtype=float)
        means = np.asarray(payload["means"], dtype=float)
        covariances = np.asarray(payload["covariances"], dtype=float)

        if means.ndim != 2:
            raise ValueError("Loaded means must be a 2D array.")

        n_components, n_features = means.shape
        gmm = GaussianMixture(n_components=n_components, covariance_type="full", random_state=42)
        gmm.weights_ = weights
        gmm.means_ = means
        gmm.covariances_ = covariances

        # Reconstruct precision cholesky used by sklearn internals.
        precisions_cholesky = []
        for covariance in covariances:
            cov_cholesky = np.linalg.cholesky(covariance)
            precision_cholesky = np.linalg.inv(cov_cholesky).T
            precisions_cholesky.append(precision_cholesky)

        gmm.precisions_cholesky_ = np.asarray(precisions_cholesky)
        gmm.n_features_in_ = n_features
        gmm.converged_ = True
        gmm.n_iter_ = 0
        gmm.lower_bound_ = float("nan")

        self.gmm = gmm
