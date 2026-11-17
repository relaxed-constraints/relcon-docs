# /// script
# requires-python = ">=3.11"
# dependencies = ["matplotlib==3.10.8", "numpy==2.3.5"]
# ///
"""Regenerate the documentation plot: uv run scripts/generate_example_plot.py."""

import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.transforms import Bbox

OUTPUT = Path(__file__).resolve().parents[1] / "docs" / "images"


def main():
    plt.rcParams.update({"font.family": "DejaVu Sans", "svg.hashsalt": "relcon-poisson"})
    ink = "#24334b"
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(projection="3d")
    x = np.arange(0, 19)
    rates = np.arange(1, 9)
    colors = plt.colormaps["viridis"](np.linspace(0.1, 0.88, len(rates)))
    factorial = np.array([math.factorial(int(k)) for k in x], dtype=float)

    # Ribbons guide the eye; only integer outcomes carry probability mass.
    for rate, color in zip(rates, colors, strict=True):
        probability = float(rate) ** x * np.exp(-rate) / factorial
        vertices = [(x[0], 0), *zip(x, probability, strict=True), (x[-1], 0)]
        ribbon = PolyCollection([vertices], facecolors=[color], alpha=0.55, edgecolors="none")
        ax.add_collection3d(ribbon, zs=float(rate), zdir="y")
        ax.plot(x, np.full_like(x, rate), probability, color=color, linewidth=2)
        ax.scatter(x, np.full_like(x, rate), probability, color=color, s=12, depthshade=False)

    ax.set(xlim=(0, 18), ylim=(0.5, 8.5), zlim=(0, 0.4))
    ax.set_xlabel("Count, k", labelpad=10, color=ink)
    ax.set_ylabel("Mean rate, λ", labelpad=10, color=ink)
    ax.set_zlabel("Probability", labelpad=9, color=ink)
    ax.set_xticks([0, 4, 8, 12, 16])
    ax.set_yticks([1, 2, 4, 6, 8])
    ax.set_zticks([0, 0.1, 0.2, 0.3, 0.4])
    ax.tick_params(colors="#53627a", labelsize=9, pad=1)
    ax.view_init(elev=25, azim=-58)
    ax.set_box_aspect((1.6, 1.1, 0.8))
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.set_pane_color((1, 1, 1, 0))
        axis.line.set_color("#b6c0d0")

    # The 3D axes' tight bbox includes empty space above and below the plot.
    # Measure the rendered ink instead, and use the same crop for both formats.
    fig.set_dpi(200)
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    fig.canvas.draw()
    rgba = np.asarray(fig.canvas.buffer_rgba())
    rows, columns = np.nonzero(rgba[:, :, 3])
    height = rgba.shape[0]
    padding = 0.1
    crop = Bbox.from_extents(
        columns.min() / fig.dpi - padding,
        (height - rows.max() - 1) / fig.dpi - padding,
        (columns.max() + 1) / fig.dpi + padding,
        (height - rows.min()) / fig.dpi + padding,
    )

    OUTPUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        OUTPUT / "poisson-distributions.png",
        dpi=200,
        transparent=True,
        bbox_inches=crop,
    )
    fig.savefig(
        OUTPUT / "poisson-distributions.svg",
        transparent=True,
        bbox_inches=crop,
        metadata={"Date": None},
    )
    svg = OUTPUT / "poisson-distributions.svg"
    svg.write_text("\n".join(line.rstrip() for line in svg.read_text().splitlines()) + "\n")
    plt.close(fig)


if __name__ == "__main__":
    main()
