"""Analysis of the campaign against the pre-registered criteria of Document 3, Part 1.

Usage (from kits/qae_european, docs extra installed):
    python docs/analyse.py            # reads results/, writes results/summary.json and the figures in docs/img/

Every number quoted in Document 3, Part 2 comes from results/summary.json.
Criteria are implemented exactly as written in Document 3, section 1.7; scope rules as in section 1.6.
"""
import csv, json, os
from collections import defaultdict
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")
IMG = os.path.join(HERE, "img")
INK, BLUE, AMBER, GREEN, GREY = "#1b2a41", "#3b5bdb", "#d08a1f", "#2f9e44", "#8a94a6"
plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False})
DEPTHS, QUBITS, LARGEST = (4, 5, 6, 7, 8), (3, 4, 5, 6, 7), 8
MATS = ["1W", "2W", "1M", "3M", "6M", "1Y", "3Y", "5Y"]
FLOATS = ("moneyness", "vol", "rate", "bs", "grid_price", "circuit_price", "qae_mean", "qae_rmse_grid", "qae_rmse_bs",
          "qae_medae_grid", "qae_mode_errors", "mc_rmse_bs", "mcgrid_rmse_grid", "mcgrid_medae_grid", "qmc_rmse_bs")
INTS = ("scenario", "qubits", "depth", "worthless", "calls_qae", "calls_qmc")


def load():
    with open(os.path.join(RES, "campaign.csv")) as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in FLOATS: r[k] = float(r[k])
        for k in INTS: r[k] = int(r[k])
    return rows


def slope(calls, err):
    """Least-squares slope of log(err) against log(calls); None if any error is 0 (log undefined)."""
    calls, err = np.asarray(calls, float), np.asarray(err, float)
    if np.any(err <= 0):
        return None, None
    s, logc = np.polyfit(np.log(calls), np.log(err), 1)
    return float(s), float(logc)


def quart(x):
    x = np.asarray([v for v in x if v is not None and np.isfinite(v)], float)
    if not len(x):
        return None
    return {"n": int(len(x)), "q1": float(np.percentile(x, 25)), "median": float(np.median(x)),
            "q3": float(np.percentile(x, 75)), "min": float(x.min()), "max": float(x.max())}


def share(flags):
    flags = list(flags)
    return {"pass": int(sum(flags)), "of": len(flags), "share": (sum(flags) / len(flags)) if flags else None}


def main():
    rows = load()
    by = {(r["scenario"], r["qubits"], r["depth"]): r for r in rows}
    scen = sorted({r["scenario"] for r in rows})
    meta = {r["scenario"]: r for r in rows if r["qubits"] == 3 and r["depth"] == 4}
    out = {"rows": len(rows), "scenarios": len(scen)}
    assert len(rows) == 1848 * 25 and len(scen) == 1848, "campaign incomplete"

    # ---------- scope (section 1.6) ----------
    negligible = {s for s in scen if meta[s]["bs"] < 0.01}
    worthless = {(s, n) for s in scen for n in QUBITS if by[(s, n, 4)]["worthless"]}
    in_scope = lambda s, n: s not in negligible and (s, n) not in worthless
    out["scope"] = {
        "negligible_scenarios": len(negligible),
        "worthless_pairs": len(worthless),
        "worthless_pairs_by_qubits": {n: sum(1 for (s, m) in worthless if m == n) for n in QUBITS},
        "worthless_and_not_negligible": sum(1 for (s, n) in worthless if s not in negligible),
        "in_scope_pairs": sum(in_scope(s, n) for s in scen for n in QUBITS),
        "in_scope_scenarios_n5": sum(in_scope(s, 5) for s in scen),
        "in_scope_scenarios_n7": sum(in_scope(s, 7) for s in scen),
        "negligible_by_maturity": {t: sum(1 for s in negligible if meta[s]["maturity"] == t) for t in MATS},
    }

    # ---------- H0 ----------
    d0 = [abs(r["circuit_price"] - r["grid_price"]) for r in rows]
    out["H0a"] = {"max_abs_diff": max(d0), **share(x <= 1e-9 for x in d0)}
    ver = json.load(open(os.path.join(RES, "verification.json")))
    out["H0b"] = {"checks": len(ver), "max_abs_diff": max(v["max_abs_diff"] for v in ver),
                  **share(v["max_abs_diff"] <= 1e-9 for v in ver)}

    # ---------- H1 (largest budget, every in-scope pair) ----------
    h1 = [(s, n) for s in scen for n in QUBITS if in_scope(s, n)]
    win = lambda s, n, key_q, key_m: by[(s, n, LARGEST)][key_q] < by[(s, n, LARGEST)][key_m]
    out["H1"] = share(win(s, n, "qae_rmse_grid", "mcgrid_rmse_grid") for s, n in h1)
    out["H1_by_qubits"] = {n: share(win(s, n, "qae_rmse_grid", "mcgrid_rmse_grid") for s, m in h1 if m == n) for n in QUBITS}
    out["H1_sensitivity_median_abs_error"] = share(win(s, n, "qae_medae_grid", "mcgrid_medae_grid") for s, n in h1)
    fails = [(s, n) for s, n in h1 if not win(s, n, "qae_rmse_grid", "mcgrid_rmse_grid")]
    out["H1_failures"] = {
        "count": len(fails),
        "by_maturity": {t: sum(1 for s, n in fails if meta[s]["maturity"] == t) for t in MATS},
        "by_vol": {v: sum(1 for s, n in fails if abs(meta[s]["vol"] - v) < 1e-9) for v in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)},
        "by_moneyness": {m: sum(1 for s, n in fails if abs(meta[s]["moneyness"] - m) < 1e-9)
                         for m in sorted({meta[s]["moneyness"] for s in scen})},
        "by_qubits": {n: sum(1 for s, m in fails if m == n) for n in QUBITS},
        "with_mode_errors": sum(1 for s, n in fails if by[(s, n, LARGEST)]["qae_mode_errors"] > 0),
    }

    # ---------- H2 (n = 5, slopes over the 5 budgets) ----------
    sq, sm, undefined = [], [], 0
    for s in scen:
        if not in_scope(s, 5):
            continue
        rr = [by[(s, 5, d)] for d in DEPTHS]
        a, _ = slope([r["calls_qae"] for r in rr], [r["qae_rmse_grid"] for r in rr])
        b, _ = slope([r["calls_qae"] for r in rr], [r["mcgrid_rmse_grid"] for r in rr])
        if a is None or b is None:
            undefined += 1
        sq.append(a); sm.append(b)
    out["H2a"] = {**share(x is not None and x <= -0.8 for x in sq), "slopes": quart(sq), "undefined": sum(x is None for x in sq)}
    out["H2b"] = {**share(x is not None and -0.65 <= x <= -0.35 for x in sm), "slopes": quart(sm), "undefined": sum(x is None for x in sm)}

    # ---------- H3 (n = 7, largest budget, against Black-Scholes) ----------
    h3 = [s for s in scen if in_scope(s, 7)]
    tol = lambda r: max(0.01 * r["bs"], 0.01)
    out["H3"] = share(by[(s, 7, LARGEST)]["qae_rmse_bs"] <= tol(by[(s, 7, LARGEST)]) for s in h3)
    f3 = [s for s in h3 if by[(s, 7, LARGEST)]["qae_rmse_bs"] > tol(by[(s, 7, LARGEST)])]
    out["H3_failures"] = {
        "by_maturity": {t: sum(1 for s in f3 if meta[s]["maturity"] == t) for t in MATS},
        "by_vol": {v: sum(1 for s in f3 if abs(meta[s]["vol"] - v) < 1e-9) for v in (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)},
        "bias_exceeds_tolerance": sum(1 for s in f3 if abs(by[(s, 7, LARGEST)]["grid_price"] - meta[s]["bs"]) > tol(by[(s, 7, LARGEST)])),
    }

    # ---------- H4 (descriptive: n = 7, ratio RMSE against BS, QAE / QMC, per budget) ----------
    out["H4_ratio_qae_over_qmc"] = {d: quart(by[(s, 7, d)]["qae_rmse_bs"] / by[(s, 7, d)]["qmc_rmse_bs"]
                                         for s in h3 if by[(s, 7, d)]["qmc_rmse_bs"] > 0) for d in DEPTHS}

    # ---------- relative efficiency at the largest budget (section 1.8) ----------
    def eff(s, n, comp_err, comp_calls, qae_err):
        rr = [by[(s, n, d)] for d in DEPTHS]
        sl, logc = slope([r[comp_calls] for r in rr], [r[comp_err] for r in rr])
        top = by[(s, n, LARGEST)]
        eps = top[qae_err]
        if sl is None or sl >= 0 or eps <= 0:
            return None, None
        n_comp = float(np.exp((np.log(eps) - logc) / sl))     # calls the comparator needs to reach RMSE eps, on its fitted line
        extrap = n_comp > max(r[comp_calls] for r in rr)
        return n_comp / top["calls_qae"], extrap

    E = {}
    for label, n, ce, cc, qe in (("vs_mc_grid_n5", 5, "mcgrid_rmse_grid", "calls_qae", "qae_rmse_grid"),
                                 ("vs_mc_grid_n7", 7, "mcgrid_rmse_grid", "calls_qae", "qae_rmse_grid"),
                                 ("vs_qmc_n7", 7, "qmc_rmse_bs", "calls_qmc", "qae_rmse_bs")):
        vals = [eff(s, n, ce, cc, qe) for s in scen if in_scope(s, n)]
        E[label] = {**(quart(v for v, _ in vals) or {}), "extrapolated": sum(1 for v, x in vals if x),
                    "above_1": sum(1 for v, _ in vals if v is not None and v > 1),
                    "undefined": sum(1 for v, _ in vals if v is None)}
    out["relative_efficiency_largest_budget"] = E

    # ---------- mode errors ----------
    out["mode_errors"] = {
        "share_of_draws_by_depth": {d: float(np.mean([by[(s, n, d)]["qae_mode_errors"] for s in scen for n in QUBITS if in_scope(s, n)])) for d in DEPTHS},
        "configs_with_any_by_depth": {d: share(by[(s, n, d)]["qae_mode_errors"] > 0 for s in scen for n in QUBITS if in_scope(s, n)) for d in DEPTHS},
        "share_of_draws_by_maturity_largest": {t: float(np.mean([by[(s, n, LARGEST)]["qae_mode_errors"] for s in scen for n in QUBITS
                                                                  if in_scope(s, n) and meta[s]["maturity"] == t])) for t in MATS},
    }

    # ---------- crossing budget N* and discretisation bias ----------
    nstar = defaultdict(int)
    for s in scen:
        if not in_scope(s, 5):
            continue
        k = next((by[(s, 5, d)]["calls_qae"] for d in DEPTHS if by[(s, 5, d)]["qae_rmse_grid"] < by[(s, 5, d)]["mcgrid_rmse_grid"]), "never")
        nstar[k] += 1
    out["crossing_budget_n5"] = dict(nstar)
    out["discretisation_bias_rel"] = {n: quart(abs(by[(s, n, 4)]["grid_price"] - meta[s]["bs"]) / meta[s]["bs"]
                                         for s in scen if in_scope(s, n)) for n in QUBITS}
    out["relative_rmse_largest_by_maturity_n5"] = {
        t: {"qae": quart(by[(s, 5, LARGEST)]["qae_rmse_grid"] / by[(s, 5, LARGEST)]["grid_price"] for s in scen if in_scope(s, 5) and meta[s]["maturity"] == t),
            "mc_grid": quart(by[(s, 5, LARGEST)]["mcgrid_rmse_grid"] / by[(s, 5, LARGEST)]["grid_price"] for s in scen if in_scope(s, 5) and meta[s]["maturity"] == t)}
        for t in MATS}

    json.dump(out, open(os.path.join(RES, "summary.json"), "w"), indent=1, default=str)
    figures(rows, by, scen, meta, in_scope, sq, sm)
    print(json.dumps({k: out[k] for k in ("scope", "H0a", "H0b", "H1", "H1_sensitivity_median_abs_error", "H2a", "H2b", "H3")}, indent=1, default=str))


def figures(rows, by, scen, meta, in_scope, sq, sm):
    os.makedirs(IMG, exist_ok=True)
    calls = [by[(scen[0], 3, d)]["calls_qae"] for d in DEPTHS]
    # 1. median RMSE against calls, n = 5, relative to the grid price
    fig, ax = plt.subplots(figsize=(5.4, 3.6))
    for key, lab, col in (("qae_rmse_grid", "amplitude estimation", BLUE), ("mcgrid_rmse_grid", "Monte Carlo on the grid", AMBER)):
        med = [np.median([by[(s, 5, d)][key] / by[(s, 5, d)]["grid_price"] for s in scen if in_scope(s, 5)]) for d in DEPTHS]
        q1 = [np.percentile([by[(s, 5, d)][key] / by[(s, 5, d)]["grid_price"] for s in scen if in_scope(s, 5)], 25) for d in DEPTHS]
        q3 = [np.percentile([by[(s, 5, d)][key] / by[(s, 5, d)]["grid_price"] for s in scen if in_scope(s, 5)], 75) for d in DEPTHS]
        ax.loglog(calls, med, "o-", color=col, label=lab)
        ax.fill_between(calls, q1, q3, color=col, alpha=.15)
    ax.loglog(calls, [0.02 * (c / calls[0]) ** -1 for c in calls], ":", color=GREY, label="slope −1")
    ax.loglog(calls, [0.02 * (c / calls[0]) ** -0.5 for c in calls], "--", color=GREY, label="slope −1/2")
    ax.set_xticks(calls, [f"{c:,}" for c in calls]); ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("calls"); ax.set_ylabel("RMSE / grid price")
    ax.set_title("n = 5, all in-scope scenarios (median, quartiles)", fontsize=9)
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(os.path.join(IMG, "error_vs_calls.png"), dpi=200, bbox_inches="tight"); plt.close(fig)
    # 2. histogram of slopes
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    ax.hist([x for x in sq if x is not None], bins=60, range=(-1.6, 0.2), color=BLUE, alpha=.7, label="amplitude estimation")
    ax.hist([x for x in sm if x is not None], bins=60, range=(-1.6, 0.2), color=AMBER, alpha=.7, label="Monte Carlo on the grid")
    ax.axvline(-0.8, color=BLUE, ls=":"); ax.axvline(-0.65, color=AMBER, ls=":"); ax.axvline(-0.35, color=AMBER, ls=":")
    ax.set_xlabel("fitted slope of log RMSE against log calls (n = 5)"); ax.set_ylabel("scenarios")
    ax.legend(frameon=False, fontsize=8)
    fig.savefig(os.path.join(IMG, "slopes.png"), dpi=200, bbox_inches="tight"); plt.close(fig)
    # 3. heatmap: share of H1 wins by maturity x vol (all n)
    vols = (0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8)
    M = np.full((len(MATS), len(vols)), np.nan)
    for i, t in enumerate(MATS):
        for j, v in enumerate(vols):
            fl = [by[(s, n, LARGEST)]["qae_rmse_grid"] < by[(s, n, LARGEST)]["mcgrid_rmse_grid"]
                  for s in scen for n in QUBITS if in_scope(s, n) and meta[s]["maturity"] == t and abs(meta[s]["vol"] - v) < 1e-9]
            if fl: M[i, j] = np.mean(fl)
    fig, ax = plt.subplots(figsize=(5.4, 3.8))
    im = ax.imshow(M, cmap="Blues", vmin=0.5, vmax=1, aspect="auto")
    for i in range(len(MATS)):
        for j in range(len(vols)):
            if np.isfinite(M[i, j]):
                ax.text(j, i, f"{100*M[i, j]:.0f}", ha="center", va="center", fontsize=7, color="white" if M[i, j] > .8 else INK)
    ax.set_xticks(range(len(vols)), [f"{int(v*100)}%" for v in vols]); ax.set_yticks(range(len(MATS)), MATS)
    ax.set_xlabel("volatility"); ax.set_ylabel("maturity")
    ax.set_title("H1: % of in-scope (scenario, n) where amplitude estimation wins", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=.04)
    fig.savefig(os.path.join(IMG, "h1_heatmap.png"), dpi=200, bbox_inches="tight"); plt.close(fig)
    # 4. discretisation bias against n
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    data = [[abs(by[(s, n, 4)]["grid_price"] - meta[s]["bs"]) / meta[s]["bs"] for s in scen if in_scope(s, n)] for n in QUBITS]
    ax.boxplot(data, tick_labels=[str(n) for n in QUBITS], showfliers=False)
    ax.set_yscale("log"); ax.set_xlabel("price qubits n"); ax.set_ylabel("|grid price − BS| / BS")
    fig.savefig(os.path.join(IMG, "discretisation_bias.png"), dpi=200, bbox_inches="tight"); plt.close(fig)
    # 5. QAE vs QMC ratio, n = 7
    fig, ax = plt.subplots(figsize=(5.4, 3.2))
    data = [[by[(s, 7, d)]["qae_rmse_bs"] / by[(s, 7, d)]["qmc_rmse_bs"] for s in scen if in_scope(s, 7) and by[(s, 7, d)]["qmc_rmse_bs"] > 0] for d in DEPTHS]
    ax.boxplot(data, tick_labels=[f"{c:,}" for c in calls], showfliers=False)
    ax.axhline(1, color=GREY, ls="--"); ax.set_yscale("log")
    ax.set_xlabel("budget (calls of amplitude estimation)"); ax.set_ylabel("RMSE ratio QAE / QMC (vs BS)")
    fig.savefig(os.path.join(IMG, "qae_vs_qmc.png"), dpi=200, bbox_inches="tight"); plt.close(fig)
    print("figures written")


if __name__ == "__main__":
    main()
