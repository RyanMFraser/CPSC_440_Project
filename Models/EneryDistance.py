import numpy as np


def _validate_2d_array(arr, name):
	arr = np.asarray(arr)
	if arr.ndim != 2:
		raise ValueError(f"{name} must be a 2D array of shape (n_samples, n_features).")
	if arr.shape[0] == 0:
		raise ValueError(f"{name} must contain at least one sample.")
	return arr


def _mean_pairwise_distance(X, Y):
	# Broadcasted Euclidean distance matrix for all sample pairs.
	diff = X[:, None, :] - Y[None, :, :]
	dists = np.sqrt(np.sum(diff * diff, axis=2))
	return float(np.mean(dists))


def energy_distance(X, Y):
	"""
	Compute multivariate energy distance between two sample sets.

	Parameters
	----------
	X : array-like of shape (n_samples_x, n_features)
		First sample set (e.g., real data).
	Y : array-like of shape (n_samples_y, n_features)
		Second sample set (e.g., generated samples).

	Returns
	-------
	float
		The energy distance. Lower means distributions are more similar.
	"""
	X = _validate_2d_array(X, "X")
	Y = _validate_2d_array(Y, "Y")

	if X.shape[1] != Y.shape[1]:
		raise ValueError("X and Y must have the same number of features.")

	exy = _mean_pairwise_distance(X, Y)
	exx = _mean_pairwise_distance(X, X)
	eyy = _mean_pairwise_distance(Y, Y)

	return 2.0 * exy - exx - eyy


def gmm_energy_distance(gmm, data, n_samples=None, random_state=None):
	"""
	Sample from a fitted GMM and compute energy distance to the given data.

	Parameters
	----------
	gmm : object
		Fitted model exposing ``sample(n_samples)`` as in sklearn GaussianMixture.
	data : array-like of shape (n_samples_data, n_features)
		Reference sample set.
	n_samples : int, optional
		Number of generated samples. Defaults to len(data).
	random_state : int, optional
		Random seed used for deterministic sampling when supported by the model.

	Returns
	-------
	float
		Energy distance between ``data`` and generated GMM samples.
	"""
	data = _validate_2d_array(data, "data")
	n = int(n_samples) if n_samples is not None else int(data.shape[0])
	if n <= 0:
		raise ValueError("n_samples must be a positive integer.")

	if random_state is not None and hasattr(gmm, "random_state"):
		gmm.random_state = random_state

	generated, _ = gmm.sample(n)
	generated = _validate_2d_array(generated, "generated")

	return energy_distance(data, generated)


