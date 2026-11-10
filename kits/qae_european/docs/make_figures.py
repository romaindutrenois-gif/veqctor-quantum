"""Figures for Document 1 (the figures of Document 3 are written by docs/analyse.py).

Usage (from kits/qae_european, with the docs extra installed: pip install -e ".[docs]"):
    python docs/make_figures.py
Figures are written to docs/img/.
"""
import os, warnings
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.stats import lognorm

from qae_european import Option, LognormalGrid, QuantumPricer
from qae_european.resources import circuit_size

warnings.filterwarnings("ignore", category=DeprecationWarning)
HERE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(HERE, "img")
os.makedirs(IMG, exist_ok=True)
REF = Option(spot=100, strike=105, rate=0.03, vol=0.2, maturity=1.0)   # reference option of the guide
INK, BLUE, AMBER, GREY = "#1b2a41", "#3b5bdb", "#d08a1f", "#8a94a6"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.edgecolor": INK, "axes.labelcolor": INK, "xtick.color": INK, "ytick.color": INK})


def save(fig, name):
    fig.savefig(os.path.join(IMG, name), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote", name)


def fig_discretisation():
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.2), sharey=True)
    s = REF.log_std
    x = np.linspace(40, 200, 600)
    dens = lognorm.pdf(x, s, scale=np.exp(REF.log_mean))
    for ax, n in zip(axes, (3, 5)):
        g = LognormalGrid(REF, n)
        widths = np.diff(np.exp(g.edges))
        ax.bar(g.prices, g.probs / widths, width=widths * 0.9, color=BLUE, alpha=.35, label=f"grid, {2**n} points")
        ax.plot(x, dens, color=INK, lw=1.4, label="lognormal density")
        ax.axvline(REF.strike, color=AMBER, ls="--", lw=1.2, label="strike 105")
        ax.set_title(f"n = {n} price qubits")
        ax.set_xlabel("terminal price $S_T$")
        ax.set_xlim(40, 200)
    axes[0].set_ylabel("density")
    axes[1].legend(frameon=False, fontsize=8)
    save(fig, "discretisation.png")


def fig_circuit():
    p = QuantumPricer(LognormalGrid(REF, 3))
    fig = p.circuit_a().decompose(reps=0).draw("mpl", fold=-1, style={"name": "bw"})
    fig.savefig(os.path.join(IMG, "circuit_a_3qubits.png"), dpi=200, bbox_inches="tight")
    plt.close(fig)
    print("wrote circuit_a_3qubits.png")


def fig_pipeline():
    fig, ax = plt.subplots(figsize=(9, 2.3))
    ax.axis("off")
    boxes = [("Option\n$S_0, K, r, \\sigma, T$", 0.0), ("LognormalGrid\n$2^n$ points $p_i$, $x_i$", 1.6),
             ("Circuit A\nload $\\sqrt{p_i}$,\nrotate by $f_i$", 3.2), ("$A\\,Q^k$, measure\n100 shots\nper power $k$", 4.8),
             ("MLAE\n$\\hat\\theta$ maximises\nthe likelihood", 6.4), ("Price\n$e^{-rT} g_{max}\\sin^2\\hat\\theta$", 8.0)]
    for text, x0 in boxes:
        ax.add_patch(plt.Rectangle((x0, 0), 1.35, 1, fc="#eef1fb", ec=BLUE, lw=1.2))
        ax.text(x0 + .675, .5, text, ha="center", va="center", fontsize=8.5, color=INK)
    for _, x0 in boxes[:-1]:
        ax.annotate("", xy=(x0 + 1.6, .5), xytext=(x0 + 1.35, .5), arrowprops=dict(arrowstyle="->", color=INK))
    ax.text(4.8 + .675, -.25, "k = 0, 1, 2, 4, ..., $2^{d-2}$", ha="center", fontsize=8, color=GREY)
    ax.set_xlim(-.1, 9.45); ax.set_ylim(-.4, 1.1)
    save(fig, "pipeline.png")


def fig_circuit_size():
    ns = [3, 4, 5, 6, 7]
    sizes = [circuit_size(REF, n) for n in ns]
    fig, ax = plt.subplots(figsize=(5, 3.2))
    ax.semilogy(ns, [s["A"]["cx"] for s in sizes], "o-", color=BLUE, label="A")
    ax.semilogy(ns, [s["Q"]["cx"] for s in sizes], "s-", color=AMBER, label="Q (one Grover step)")
    ax.set_xlabel("price qubits n"); ax.set_ylabel("CNOT gates after compilation")
    ax.set_xticks(ns); ax.legend(frameon=False)
    save(fig, "circuit_size.png")
    return sizes


if __name__ == "__main__":
    fig_discretisation(); fig_circuit(); fig_pipeline(); fig_circuit_size()
