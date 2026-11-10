"""Is the H2-a failure sampling noise? A rerun with 2,000 draws instead of 50 (Document 3, section 2.6).

Usage (from kits/qae_european, after the campaign):  python docs/h2a_draws.py  ->  results/h2a_draws.json

150 in-scope scenarios at n = 5, drawn at random with a fixed seed. For each, amplitude estimation is rerun at
the 5 budgets with 2,000 draws (separate random streams from the campaign's), and the slope of log RMSE
against log calls is fitted as in H2-a. If the 50-draw failures were noise, the share with slope <= -0.8
would rise towards 100% with 2,000 draws. Descriptive study, not part of the pre-registered plan.
"""
import csv, json, os, warnings
from multiprocessing import Pool
import numpy as np

from qae_european import LognormalGrid, QuantumPricer, MaximumLikelihoodAE, Ladder
from qae_european.campaign import scenarios, SEED, SHOTS, DEPTHS

warnings.filterwarnings("ignore", category=DeprecationWarning, module="qiskit")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
N, DRAWS, SAMPLE = 5, 2000, 150


def one(s):
    p = QuantumPricer(LognormalGrid(scenarios()[s].option, N))
    gp = p.grid.price()
    calls, rmse = [], []
    for d in DEPTHS:
        ae = MaximumLikelihoodAE(Ladder.exponential(d, SHOTS), "born")
        rng = np.random.default_rng(np.random.SeedSequence([SEED, 99, s, d]))     # distinct from the campaign
        est = ae.estimate_prices(p, rng, DRAWS)
        calls.append(ae.ladder.calls); rmse.append(float(np.sqrt(np.mean((est - gp) ** 2))))
    slope = float(np.polyfit(np.log(calls), np.log(rmse), 1)[0])
    return s, slope, p.amplitude()


def main():
    with open(os.path.join(RES, "campaign.csv")) as f:
        rows = [r for r in csv.DictReader(f) if int(r["qubits"]) == N]
    by = {}
    for r in rows:
        by.setdefault(int(r["scenario"]), []).append(r)
    in_scope = [s for s, rr in by.items() if float(rr[0]["bs"]) >= 0.01 and rr[0]["worthless"] == "0"]
    pick = sorted(np.random.default_rng(np.random.SeedSequence([SEED, 98])).choice(in_scope, SAMPLE, replace=False).tolist())
    slope50 = {}
    for s in pick:
        rr = sorted(by[s], key=lambda r: int(r["depth"]))
        slope50[s] = float(np.polyfit(np.log([int(r["calls_qae"]) for r in rr]),
                                      np.log([float(r["qae_rmse_grid"]) for r in rr]), 1)[0])
    with Pool(2) as pool:
        res = pool.map(one, pick)
    s2000 = {s: sl for s, sl, _ in res}
    amp = {s: a for s, _, a in res}
    fail50 = [s for s in pick if slope50[s] > -0.8]
    bins = (("a < 0.01", 0, 0.01), ("0.01 <= a < 0.03", 0.01, 0.03), ("a >= 0.03", 0.03, 2))
    out = {
        "scenarios": SAMPLE, "draws": DRAWS,
        "pass_share_50_draws": float(np.mean([slope50[s] <= -0.8 for s in pick])),
        "pass_share_2000_draws": float(np.mean([s2000[s] <= -0.8 for s in pick])),
        "failures_at_50": len(fail50),
        "of_which_still_fail_at_2000": sum(1 for s in fail50 if s2000[s] > -0.8),
        "median_slope_50": float(np.median(list(slope50.values()))),
        "median_slope_2000": float(np.median(list(s2000.values()))),
        "pass_share_2000_by_amplitude": {lab: {"pass": sum(1 for s in pick if lo <= amp[s] < hi and s2000[s] <= -0.8),
                                               "of": sum(1 for s in pick if lo <= amp[s] < hi)} for lab, lo, hi in bins},
        "slopes": {s: {"draws_50": slope50[s], "draws_2000": s2000[s], "amplitude": amp[s]} for s in pick},
    }
    with open(os.path.join(RES, "h2a_draws.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "slopes"}, indent=1))


if __name__ == "__main__":
    main()
