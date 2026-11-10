"""Truncation bias floor and the width trade-off (Document 1, sections 3 and 11; Document 3, section 2.7).

Usage (from kits/qae_european):  python docs/truncation.py   ->  results/truncation.json

For a few options, the grid price against Black-Scholes for growing numbers of qubits (classical computation,
no circuit), at grid widths of 4 (the default) and 6 standard deviations, with the largest grid payoff and the
amplitude a at n = 7. The bias converges to a floor set by the width, not to zero; a wider grid removes the
floor but scales the payoff up and the amplitude down.

The forward shortfall of the grid has a closed form: the grid keeps E[S_T 1{in range}] and renormalises the
in-range probability, so  forward_grid / forward = (Phi(w - s) - Phi(-w - s)) / (1 - 2 Phi(-w)).
"""
import json, os
import numpy as np
from scipy.stats import norm

from qae_european import Option, LognormalGrid, BlackScholes

HERE = os.path.dirname(os.path.abspath(__file__))
CASES = {
    "reference option (K 105, 1Y, 20%, r 3%)": Option(100, 105, 0.03, 0.2, 1.0),
    "at the money, 1Y, 80%": Option(100, 100, 0.0, 0.8, 1.0),
    "scenario 1000: at the money, 5Y, 60%": Option(100, 100, 0.0, 0.6, 5.0),
    "at the money, 5Y, 80%": Option(100, 100, 0.0, 0.8, 5.0),
}
QUBITS = (5, 7, 9, 12, 14)


def main():
    out = {}
    for name, o in CASES.items():
        s, bs = o.log_std, BlackScholes.call(o)
        rec = {"log_std": s, "black_scholes": bs, "widths": {}}
        for w in (4.0, 6.0):
            ratio = (norm.cdf(w - s) - norm.cdf(-w - s)) / (1 - 2 * norm.cdf(-w))
            g7 = LognormalGrid(o, 7, w)
            fwd = float(np.dot(g7.probs, g7.prices) / (o.spot * np.exp(o.rate * o.maturity)))
            gmax = float(g7.payoffs().max())
            rec["widths"][w] = {
                "forward_error_formula": ratio - 1, "forward_error_grid_n7": fwd - 1,
                "relative_bias_by_qubits": {n: LognormalGrid(o, n, w).price() / bs - 1 for n in QUBITS},
                "largest_payoff_n7": gmax, "amplitude_n7": g7.price() / (o.discount * gmax),
            }
        out[name] = rec
    with open(os.path.join(HERE, "..", "results", "truncation.json"), "w") as f:
        json.dump(out, f, indent=1)
    for name, rec in out.items():
        print(name, f"s = {rec['log_std']:.2f}")
        for w, r in rec["widths"].items():
            b = "  ".join(f"n={n}: {100 * v:+.3f}%" for n, v in r["relative_bias_by_qubits"].items())
            print(f"  width {w:g}: forward {100 * r['forward_error_formula']:+.3f}% | {b} | "
                  f"largest payoff {r['largest_payoff_n7']:,.0f}, a = {r['amplitude_n7']:.4f}")


if __name__ == "__main__":
    main()
