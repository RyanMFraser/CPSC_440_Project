import numpy as np

def gaussian_model(x,y):
    """
    takes in x and y coordinates as vectors, and output the mean and covariance of the 
    2D Gaussian distribution that best fits the data.
    """
    mean = [x.mean(), y.mean()]
    covariance = np.cov(np.vstack([x, y]), ddof=0)
    return mean, covariance