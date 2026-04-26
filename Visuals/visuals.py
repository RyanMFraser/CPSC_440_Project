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

def plot_gmm_samples(gmms, best_idx, data, name, n_samples=100, include_idx0_panel=False):
    """Save a sample-comparison figure from fitted GMM models.

    Args:
        gmms (list): List of fitted sklearn GaussianMixture models.
        best_idx (int): Index of the best model in gmms.
        data (DataFrame): Data containing X and Y columns used for plotting.
        name (str): Golfer name; outputs are saved under Visuals/<name>/.
        n_samples (int): Number of points to sample from the best GMM.
        include_idx0_panel (bool): If True, add a third subplot that shows
            samples from gmms[0] in the same figure.
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
    sampled_points, _ = best_gmm.sample(n_samples)

    if include_idx0_panel:
        idx0_points, _ = gmms[0].sample(n_samples)
        fig, axes = plt.subplots(1, 3, figsize=(18, 6), sharex=True, sharey=True)
        ax_data, ax_samples, ax_idx0 = axes
    else:
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
    ax_samples.set_title(f"{name} GMM Samples (index={best_idx}, n={n_samples})")

    if include_idx0_panel:
        ax_idx0.scatter(
            idx0_points[:, 0],
            idx0_points[:, 1],
            s=20,
            alpha=0.7,
            color="tab:green",
            edgecolors="white",
            linewidths=0.3,
        )
        ax_idx0.set_title(f"{name} GMM Samples (index=0, n={n_samples})")
        axes_to_format = (ax_data, ax_samples, ax_idx0)
    else:
        axes_to_format = (ax_data, ax_samples)

    for ax in axes_to_format:
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_xlim(X_MIN, X_MAX)
        ax.set_ylim(Y_MIN, Y_MAX)
        ax.grid(alpha=0.15)

    title_text = f"{name} Data vs. Best GMM Samples"
    if include_idx0_panel:
        title_text = f"{name} Data vs. GMM Samples (best index and index 0)"

    fig.suptitle(title_text, fontsize=16)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    if include_idx0_panel:
        fig.savefig(output_dir / "gmm_best_model_samples_with_idx0.png", dpi=200, bbox_inches="tight")
    elif best_idx == 0:
        fig.savefig(output_dir / "gmm_best_model_samples_1comp.png", dpi=200, bbox_inches="tight")
    else:
        fig.savefig(output_dir / "gmm_best_model_samples.png", dpi=200, bbox_inches="tight")
    plt.close(fig)