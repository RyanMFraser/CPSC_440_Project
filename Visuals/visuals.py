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


def plot_gmm_dispersion(gmms, best_idx, data, name):
    """Save GMM dispersion plots for all models and the best selected model.

    Args:
        gmms (list): List of fitted sklearn GaussianMixture models.
        best_idx (int): Index of the best model in gmms.
        data (DataFrame): Data containing X and Y columns used for plotting.
        name (str): Golfer name; outputs are saved under Visuals/<name>/.
    """
    if not gmms:
        raise ValueError("gmms must contain at least one fitted model.")
    if best_idx < 0 or best_idx >= len(gmms):
        raise IndexError("best_idx is out of range for gmms.")

    features = data[["X", "Y"]]

    output_dir = Path(__file__).resolve().parent / str(name)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Plot 1: One panel per GMM, sized by number of models.
    n_models = len(gmms)
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

    for i, gmm in enumerate(gmms):
        ax = axes[i]
        n_components = gmm.n_components

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
            draw_ellipse(gmm.means_[j], gmm.covariances_[j], ax=ax, color=color)
            ax.scatter(
                gmm.means_[j, 0],
                gmm.means_[j, 1],
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

    # Plot 2: Best model only.
    best_gmm = gmms[best_idx]
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
        f"{name} Best GMM (index={best_idx}, components={best_components})"
    )
    ax_best.set_xlabel("X")
    ax_best.set_ylabel("Y")
    ax_best.set_xlim(X_MIN, X_MAX)
    ax_best.set_ylim(Y_MIN, Y_MAX)
    ax_best.grid(alpha=0.2)
    fig_best.tight_layout()
    fig_best.savefig(output_dir / "gmm_best_model.png", dpi=200, bbox_inches="tight")
    plt.close(fig_best)

def plot_gmm_heat(gmms, best_idx, data, name):
    """Save a single best-model GMM density heatmap over the shot scatter.

    Args:
        gmms (list): List of fitted sklearn GaussianMixture models.
        best_idx (int): Index of the best model in gmms.
        data (DataFrame): Data containing X and Y columns used for plotting.
        name (str): Golfer name; outputs are saved under Visuals/<name>/.
    """
    if not gmms:
        raise ValueError("gmms must contain at least one fitted model.")
    if best_idx < 0 or best_idx >= len(gmms):
        raise IndexError("best_idx is out of range for gmms.")

    features = data[["X", "Y"]].copy()
    x = features["X"].to_numpy()
    y = features["Y"].to_numpy()

    output_dir = Path(__file__).resolve().parent / str(name)
    output_dir.mkdir(parents=True, exist_ok=True)

    best_gmm = gmms[best_idx]

    # Build a dense grid over the observed data range and evaluate model density.
    x_grid = np.linspace(X_MIN, X_MAX, 250)
    y_grid = np.linspace(Y_MIN, Y_MAX, 250)
    xx, yy = np.meshgrid(x_grid, y_grid)
    grid_points = np.column_stack([xx.ravel(), yy.ravel()])

    log_density = best_gmm.score_samples(grid_points)
    density = np.exp(log_density).reshape(xx.shape)

    fig, ax = plt.subplots(figsize=(8, 6))
    heat = ax.contourf(
        xx,
        yy,
        density,
        levels=30,
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
        f"{name} Best GMM Density Heatmap (index={best_idx}, components={best_gmm.n_components})"
    )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.grid(alpha=0.15)
    fig.tight_layout()
    fig.savefig(output_dir / "gmm_best_model_heat.png", dpi=200, bbox_inches="tight")
    plt.close(fig)