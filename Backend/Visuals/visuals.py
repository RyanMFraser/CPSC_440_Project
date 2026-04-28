from matplotlib import colors
from matplotlib.patches import Ellipse
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

X_MIN, X_MAX = -50, 50
Y_MIN, Y_MAX = 0, 250

def draw_ellipse(mean, cov, ax, color):
    # Eigen decomposition
    vals, vecs = np.linalg.eigh(cov)

    # Sort eigenvalues (largest first)
    order = vals.argsort()[::-1]
    vals, vecs = vals[order], vecs[:, order]

    # Angle of ellipse
    angle = np.degrees(np.arctan2(*vecs[:, 0][::-1]))

    # 1 standard deviation = sqrt(eigenvalues)
    width, height = 2 * np.sqrt(vals)  # factor 2 = full width

    ellipse = Ellipse(
        xy=mean,
        width=width,
        height=height,
        angle=angle,
        color=color,
        alpha=0.2  # shading
    )

    ax.add_patch(ellipse)


def plot_gmm_dispersion(gmm, data, name):
    """Save GMM dispersion plots for a single fitted model.

    Args:
        gmm: A fitted sklearn GaussianMixture model.
        data (DataFrame): Data containing X and Y columns used for plotting.
        name (str): Golfer name; outputs are saved under Visuals/<name>/.
    """
    if gmm is None:
        raise ValueError("gmm must be a fitted GaussianMixture model.")

    features = data[["X", "Y"]]

    output_dir = Path(__file__).resolve().parent / str(name)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Plot 1: One panel for the provided GMM.
    n_models = 1
    n_cols = min(4, n_models)
    n_rows = int(np.ceil(n_models / n_cols))
    fig, axes = plt.subplots(
        n_rows,
        n_cols,
        figsize=(5 * n_cols, 4 * n_rows),
        sharex=True,
        sharey=True,
    )
    axes = np.atleast_1d(axes).flatten()

    for i, model in enumerate([gmm]):
        ax = axes[i]
        n_components = model.n_components

        ax.scatter(
            features["X"],
            features["Y"],
            s=14,
            alpha=0.45,
            color="tab:blue",
        )

        colors = plt.cm.get_cmap("tab10", n_components)
        for j in range(n_components):
            color = colors(j)
            draw_ellipse(model.means_[j], model.covariances_[j], ax=ax, color=color)
            ax.scatter(
                model.means_[j, 0],
                model.means_[j, 1],
                color=color,
                marker="x",
                s=90,
                linewidths=2,
            )

        ax.set_title(f"{name} GMM ({n_components} component{'s' if n_components > 1 else ''})")
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_xlim(X_MIN, X_MAX)
        ax.set_ylim(Y_MIN, Y_MAX)
        ax.grid(alpha=0.2)

    for j in range(n_models, len(axes)):
        axes[j].set_visible(False)

    fig.suptitle(f"{name} Shot Distribution with GMM Overlays (All Models)", fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(output_dir / "gmm_all_models.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # Plot 2: Same model in a dedicated single-model view.
    best_gmm = gmm
    best_components = best_gmm.n_components
    fig_best, ax_best = plt.subplots(figsize=(8, 6))

    ax_best.scatter(
        features["X"],
        features["Y"],
        s=16,
        alpha=0.45,
        color="tab:blue",
    )

    best_colors = plt.cm.get_cmap("tab10", best_components)
    for j in range(best_components):
        color = best_colors(j)
        draw_ellipse(best_gmm.means_[j], best_gmm.covariances_[j], ax=ax_best, color=color)
        ax_best.scatter(
            best_gmm.means_[j, 0],
            best_gmm.means_[j, 1],
            color=color,
            marker="x",
            s=100,
            linewidths=2,
        )

    ax_best.set_title(
        f"{name} GMM (components={best_components})"
    )
    ax_best.set_xlabel("X")
    ax_best.set_ylabel("Y")
    ax_best.set_xlim(X_MIN, X_MAX)
    ax_best.set_ylim(Y_MIN, Y_MAX)
    ax_best.grid(alpha=0.2)
    fig_best.tight_layout()
    fig_best.savefig(output_dir / "gmm_best_model.png", dpi=200, bbox_inches="tight")
    plt.close(fig_best)

def plot_gmm_heat(gmm, data, name):
    """Save a single best-model GMM density heatmap over the shot scatter.

    Args:
        gmm: A fitted sklearn GaussianMixture model.
        data (DataFrame): Data containing X and Y columns used for plotting.
        name (str): Golfer name; outputs are saved under Visuals/<name>/.
    """
    if gmm is None:
        raise ValueError("gmm must be a fitted GaussianMixture model.")

    features = data[["X", "Y"]].copy()
    x = features["X"].to_numpy()
    y = features["Y"].to_numpy()

    output_dir = Path(__file__).resolve().parent / str(name)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Build a dense grid over the observed data range and evaluate model density.
    x_grid = np.linspace(X_MIN, X_MAX, 250)
    y_grid = np.linspace(Y_MIN, Y_MAX, 250)
    xx, yy = np.meshgrid(x_grid, y_grid)
    grid_points = np.column_stack([xx.ravel(), yy.ravel()])

    log_density = gmm.score_samples(grid_points)
    density = np.exp(log_density).reshape(xx.shape)

    fig, ax = plt.subplots(figsize=(8, 6))
    positive_density = density[density > 0]
    if positive_density.size == 0:
        raise ValueError("GMM density must contain positive values for heatmap plotting.")

    vmin = positive_density.min()
    vmax = positive_density.max()
    heat = ax.contourf(
        xx,
        yy,
        density,
        levels=np.geomspace(vmin, vmax, 30),
        norm=colors.LogNorm(vmin=vmin, vmax=vmax),
        cmap="coolwarm",
        alpha=0.7,
    )

    ax.scatter(
        x,
        y,
        s=18,
        alpha=0.55,
        color="black",
        edgecolors="white",
        linewidths=0.3,
    )

    cbar = fig.colorbar(heat, ax=ax)
    cbar.set_label("GMM density")

    ax.set_title(
        f"{name} Best GMM Density Heatmap (components={gmm.n_components})"
    )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(output_dir / "gmm_best_model_heat.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

def plot_gmm_samples(gmm, data, name, n_samples=100):
    """Save a sample-comparison figure from fitted GMM models.

    Args:
        gmm: A fitted sklearn GaussianMixture model.
        data (DataFrame): Data containing X and Y columns used for plotting.
        name (str): Golfer name; outputs are saved under Visuals/<name>/.
        n_samples (int): Number of points to sample from the GMM.
    """
    if gmm is None:
        raise ValueError("gmm must be a fitted GaussianMixture model.")

    features = data[["X", "Y"]].copy()
    x = features["X"].to_numpy()
    y = features["Y"].to_numpy()

    output_dir = Path(__file__).resolve().parent / str(name)
    output_dir.mkdir(parents=True, exist_ok=True)

    sampled_points, _ = gmm.sample(n_samples)

    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=True, sharey=True)
    ax_data, ax_samples = axes

    ax_data.scatter(
        x,
        y,
        s=18,
        alpha=0.55,
        color="tab:blue",
        edgecolors="white",
        linewidths=0.3,
    )
    ax_data.set_title(f"{name} Data Scatter")

    ax_samples.scatter(
        sampled_points[:, 0],
        sampled_points[:, 1],
        s=20,
        alpha=0.7,
        color="tab:orange",
        edgecolors="white",
        linewidths=0.3,
    )
    ax_samples.set_title(f"{name} GMM Samples (n={n_samples})")

    axes_to_format = (ax_data, ax_samples)

    for ax in axes_to_format:
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_xlim(X_MIN, X_MAX)
        ax.set_ylim(Y_MIN, Y_MAX)
        ax.grid(alpha=0.15)

    fig.suptitle(f"{name} Data vs. Best GMM Samples", fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(output_dir / "gmm_best_model_samples.png", dpi=200, bbox_inches="tight")
    plt.close(fig)