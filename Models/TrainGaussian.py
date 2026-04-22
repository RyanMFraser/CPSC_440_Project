"""Contains code for training the mixtrure model, includes finding the best mixture"""

from sklearn.model_selection import train_test_split

from Models.EneryDistance import gmm_energy_distance
from Models.GaussianMixture import gaussian_mixture_model


def train_gaussian_mixture(data, max_components=10):
    """Train GMMs and return all models plus the index of the best one.

    Best model selection rule:
    1) Take the 3 models with the lowest energy distance on validation data.
    2) Among those 3, choose the one with the lowest BIC on training data.

    Returns:
        tuple[int, list]: (best_model_index, gmms)
        - best_model_index is a 0-based index into gmms
        - gmms is a list of fitted GaussianMixture models
    """

    train_df, val_df = train_test_split(
        data,
        test_size=0.10,
        random_state=42,
        shuffle=True
    )

    features_train = train_df[["X", "Y"]]

    features_val = val_df[["X", "Y"]]

    gmms = []
    model_scores = []

    for i in range(max_components):
        gmm = gaussian_mixture_model(features_train, n_components=i + 1)
        bic_value = gmm.bic(features_train)
        gmm_ed = gmm_energy_distance(gmm, features_val, n_samples=1000, random_state=42)
        gmms.append(gmm)
        model_scores.append((i, bic_value, gmm_ed))

    top_by_energy = sorted(model_scores, key=lambda x: x[2])[: min(3, len(model_scores))]

    
    best_model_index, _, _ = min(top_by_energy, key=lambda x: x[1])

    return best_model_index, gmms, model_scores


    