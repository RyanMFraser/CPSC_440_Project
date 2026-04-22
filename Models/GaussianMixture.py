from sklearn.mixture import GaussianMixture

def gaussian_mixture_model(data, n_components):
    """
    takes in a dataset and the number of components, and outputs the parameters of the 
    Gaussian mixture model that best fits the data.
    """
    gmm = GaussianMixture(n_components=n_components)
    gmm.fit(data)

    return gmm