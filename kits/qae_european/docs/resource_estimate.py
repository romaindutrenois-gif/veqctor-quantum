"""Resource estimate at a target accuracy (Document 1, section 12).

Usage (from kits/qae_european, after the campaign):  python docs/resource_estimate.py  ->  results/resources.json

For two scenarios at n = 7 price qubits, fit the campaign's error curves (RMSE against the grid price over the
5 budgets) and extrapolate to a relative statistical error of 1%, 0.1% and 0.01% of the grid price:
  - amplitude estimation: calls, ladder depth, largest Grover power, CNOTs of the deepest circuit, CNOTs executed;
  - plain Monte Carlo on the grid: paths.
Noise-free, error-free machine: no error correction, no run time (see the published estimates quoted in
Document 1, section 12). Targets beyond 26,200 calls are extrapolations of the fitted rate.
"""
import csv, json, os, warnings

from qae_european.campaign import scenarios
from qae_european.resources import circuit_size, estimate_at_accuracy, fit_power_law

warnings.filterwarnings("ignore", category=DeprecationWarning, module="qiskit")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
N = 7
TARGETS = (1e-2, 1e-3, 1e-4)


def pick(moneyness, maturity, vol, rate):
    for sc in scenarios():
        if (abs(sc.moneyness - moneyness) < 1e-9 and sc.maturity_label == maturity
                and abs(sc.vol - vol) < 1e-9 and abs(sc.rate - rate) < 1e-9):
            return sc
    raise KeyError((moneyness, maturity, vol, rate))


def main():
    with open(os.path.join(RES, "campaign.csv")) as f:
        rows = list(csv.DictReader(f))
    out = {}
    for label, sc in (("K/S 1.05, 1Y, 20%, r 1%", pick(1.05, "1Y", 0.2, 0.01)),
                      ("scenario 1000: at the money, 5Y, 60%, r 0%", scenarios()[1000])):
        rr = sorted((r for r in rows if int(r["scenario"]) == sc.index and int(r["qubits"]) == N), key=lambda r: int(r["depth"]))
        calls = [int(r["calls_qae"]) for r in rr]
        price = float(rr[0]["grid_price"])
        size = circuit_size(sc.option, N)
        mc_slope, mc_c = fit_power_law(calls, [float(r["mcgrid_rmse_grid"]) for r in rr])
        rec = {"scenario": sc.index, "grid_price": price, "amplitude": float(rr[0]["amplitude"]), "circuit": size, "targets": {}}
        for t in TARGETS:
            q = estimate_at_accuracy(calls, [float(r["qae_rmse_grid"]) for r in rr], t * price,
                                     size["A"]["cx"], size["Q"]["cx"])
            q["mc_grid_paths"] = float((t * price / mc_c) ** (1.0 / mc_slope))
            rec["targets"][t] = q
        out[label] = rec
    with open(os.path.join(RES, "resources.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
