"""Rebuild the figures and numbers used in docs/results.md (run from the kit folder: python docs/make_figures.py)."""
import sys, pathlib, warnings
warnings.filterwarnings("ignore")
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from classical import Option, black_scholes_call, discretised_call, monte_carlo_call
from circuit import build_a, price_exact, price_mlae
from resources import circuit_size

IMG = HERE / "img"; IMG.mkdir(exist_ok=True)
o = Option(); bs = black_scholes_call(o)
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
INK, BLUE, GREY = "#1f2a3d", "#4f6ef7", "#8a96ab"

# 1. the circuit itself (3 price qubits)
a, _ = build_a(o, 3)
fig = a.draw("mpl", fold=-1, style={"name": "bw"}); fig.savefig(IMG / "circuit_a_3qubits.png", dpi=150, bbox_inches="tight"); plt.close(fig)

# 2. discretisation error against price qubits
ns = list(range(2, 11)); disc = [discretised_call(o, n) for n in ns]
err = [abs(d - bs) / bs * 100 for d in disc]
fig, ax = plt.subplots(figsize=(6, 3.4))
ax.semilogy(ns, err, "o-", color=INK)
ax.set_xlabel("Price qubits n (grid of 2^n points)"); ax.set_ylabel("Gap to Black-Scholes (%)")
ax.set_title("Discretisation error", loc="left")
fig.tight_layout(); fig.savefig(IMG / "discretisation.png", dpi=150); plt.close(fig)
print("discretisation", [(n, round(d, 4), round(e, 3)) for n, d, e in zip(ns, disc, err)])

# 3. error against number of calls: amplitude estimation vs Monte Carlo (median over seeds)
n = 4; exact = price_exact(o, n); ladders = [(0, 1), (0, 1, 2, 4), (0, 1, 2, 4, 8), (0, 1, 2, 4, 8, 16), (0, 1, 2, 4, 8, 16, 32), (0, 1, 2, 4, 8, 16, 32, 64)]
ae_calls, ae_err = [], []
for p in ladders:
    errs = []
    for s in range(30):
        est, calls = price_mlae(o, n, powers=p, shots=200, seed=s); errs.append(abs(est - exact))
    ae_calls.append(calls); ae_err.append(float(np.sqrt(np.mean(np.square(errs)))))
_, se1 = monte_carlo_call(o, 400_000); sigma = se1 * np.sqrt(400_000)
mc_calls = np.logspace(2.5, 6.5, 20); mc_err = sigma / np.sqrt(mc_calls)
fig, ax = plt.subplots(figsize=(6, 3.8))
ax.loglog(mc_calls, mc_err, "-", color=GREY, label="Monte Carlo: error ∝ 1/√N")
ax.loglog(ae_calls, ae_err, "o-", color=BLUE, label="Amplitude estimation (MLAE)")
ax.set_xlabel("Calls N (paths, or calls of the circuit A)"); ax.set_ylabel("Price error (RMS)")
ax.set_title("Accuracy against cost", loc="left"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(IMG / "error_vs_calls.png", dpi=150); plt.close(fig)
slope = np.polyfit(np.log(ae_calls[1:]), np.log(ae_err[1:]), 1)[0]
print("ae", list(zip(ae_calls, [round(e, 4) for e in ae_err])), "slope", round(slope, 2), "sigma", round(sigma, 2))

# 4. circuit size against price qubits
ns2 = [3, 4, 5, 6, 7]; sizes = [circuit_size(o, k) for k in ns2]
fig, ax = plt.subplots(figsize=(6, 3.4))
ax.semilogy(ns2, [s["A"]["cx"] for s in sizes], "o-", color=INK, label="CNOTs in A")
ax.semilogy(ns2, [s["Q"]["cx"] for s in sizes], "o-", color=BLUE, label="CNOTs in one Grover step Q")
ax.set_xlabel("Price qubits n"); ax.set_ylabel("CNOT gates"); ax.legend(frameon=False)
ax.set_title("Circuit size (exact loading, one rotation per point)", loc="left")
fig.tight_layout(); fig.savefig(IMG / "circuit_size.png", dpi=150); plt.close(fig)
print("sizes", [(k, s["A"]["cx"], s["A"]["depth"], s["Q"]["cx"], s["Q"]["depth"]) for k, s in zip(ns2, sizes)])
