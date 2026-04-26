from sklearn.mixture import GaussianMixture
from Models.EneryDistance import gmm_energy_distance
from sklearn.model_selection import train_test_split

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