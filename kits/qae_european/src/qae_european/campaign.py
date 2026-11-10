"""Test campaign: the scenario grid, the runner, and the stored measures.

Grid (pre-registered in docs/tests.md)
--------------------------------------
moneyness K/S0 : 0.75 to 1.25 step 0.05 (11)    spot fixed at 100
maturity       : 1W, 2W, 1M, 3M, 6M, 1Y, 3Y, 5Y (8)
volatility     : 20% to 80% step 10% (7)
rate           : -1%, 0%, 1% (3)
=> 1,848 scenarios, each crossed with price qubits 3..7 and ladder depths 4..8 (100 shots per power), 50 draws.

For each (scenario, price qubits, budget) the runner records:
  bs                  Black-Scholes price
  grid_price          exact grid price (target of the circuit and of grid Monte Carlo)
  circuit_price       price from the exact statevector amplitude of A (must equal grid_price)
  worthless           all grid points out of the money (circuit price is exactly 0)
  calls_qae           applications of A used by amplitude estimation
  qae_rmse_grid       RMS error of amplitude estimation against grid_price over the draws
  qae_rmse_bs         RMS error of amplitude estimation against bs
  qae_medae_grid      median absolute error of amplitude estimation against grid_price (robust to rare large errors)
  qae_mode_errors     share of draws where the estimated theta is on the wrong mode of the likelihood:
                      |theta_hat - theta| > pi / (2 m_max), m_max = 2 k_max + 1 (half the period of the highest power)
  mc_rmse_bs          RMS error of plain Monte Carlo (continuous) against bs, same number of calls
  mcgrid_rmse_grid    RMS error of plain Monte Carlo on the grid against grid_price, same number of calls
  mcgrid_medae_grid   median absolute error of plain Monte Carlo on the grid against grid_price
  qmc_rmse_bs         RMS error of quasi-Monte Carlo against bs, with its own number of points
  calls_qmc           points used by quasi-Monte Carlo (largest power of two <= calls_qae)

Seeds: every random stream is derived from SEED and the indices of the scenario, qubits, budget and method
(numpy SeedSequence), so any single row can be recomputed on its own.
"""
from dataclasses import dataclass, asdict
import csv, itertools, os, time
import numpy as np

from .option import Option
from .grid import LognormalGrid
from .quantum import QuantumPricer
from .estimation import MaximumLikelihoodAE, Ladder
from .benchmarks import BlackScholes, MonteCarlo, QuasiMonteCarlo

SEED = 20261103
SPOT = 100.0
MONEYNESS = tuple(round(0.75 + 0.05 * i, 2) for i in range(11))
MATURITIES = {"1W": 1 / 52, "2W": 2 / 52, "1M": 1 / 12, "3M": 0.25, "6M": 0.5, "1Y": 1.0, "3Y": 3.0, "5Y": 5.0}
VOLS = tuple(round(0.2 + 0.1 * i, 2) for i in range(7))
RATES = (-0.01, 0.0, 0.01)
QUBITS = (3, 4, 5, 6, 7)
DEPTHS = (4, 5, 6, 7, 8)
SHOTS = 100
DRAWS = 50
METHOD_ID = {"qae": 0, "mc": 1, "mcgrid": 2, "qmc": 3}


@dataclass(frozen=True)
class Scenario:
    index: int
    moneyness: float
    maturity_label: str
    vol: float
    rate: float

    @property
    def option(self) -> Option:
        return Option(spot=SPOT, strike=SPOT * self.moneyness, rate=self.rate, vol=self.vol,
                      maturity=MATURITIES[self.maturity_label])


def scenarios() -> list:
    combos = itertools.product(MONEYNESS, MATURITIES, VOLS, RATES)
    return [Scenario(i, m, t, v, r) for i, (m, t, v, r) in enumerate(combos)]


def rng_for(scenario: int, qubits: int, depth: int, method: str) -> np.random.Generator:
    return np.random.default_rng(np.random.SeedSequence([SEED, scenario, qubits, depth, METHOD_ID[method]]))


def _rmse(x, target) -> float:
    x = np.asarray(x, float)
    return float(np.sqrt(np.mean((x - target) ** 2)))


def _medae(x, target) -> float:
    return float(np.median(np.abs(np.asarray(x, float) - target)))


def run_scenario(sc: Scenario, qubits=QUBITS, depths=DEPTHS, draws=DRAWS) -> list:
    """All measures for one scenario, as a list of dict rows."""
    o = sc.option
    bs = BlackScholes.call(o)
    mc, qmc = MonteCarlo("continuous"), QuasiMonteCarlo()
    rows = []
    # continuous Monte Carlo and quasi-Monte Carlo do not depend on the number of qubits: computed once per budget
    per_budget = {}
    for d in depths:
        calls = Ladder.exponential(d, SHOTS).calls
        r_mc, r_qmc = rng_for(sc.index, 0, d, "mc"), rng_for(sc.index, 0, d, "qmc")
        mcs = [mc.price(o, calls, r_mc).value for _ in range(draws)]
        qmcs = [qmc.price(o, calls, r_qmc) for _ in range(draws)]
        per_budget[d] = (calls, _rmse(mcs, bs), _rmse([e.value for e in qmcs], bs), qmcs[0].calls)
    for n in qubits:
        grid = LognormalGrid(o, n)
        pricer = QuantumPricer(grid)
        gp, cp = grid.price(), pricer.price_exact()
        mcg = MonteCarlo("grid", n)
        for d in depths:
            ladder = Ladder.exponential(d, SHOTS)
            mlae = MaximumLikelihoodAE(ladder, "born")
            if pricer.worthless:
                est, mode_err = np.zeros(draws), 0.0
            else:
                hits = mlae.draw_hits(mlae.probabilities(pricer), rng_for(sc.index, n, d, "qae"), draws)
                th = mlae.estimate_theta(hits)
                est = np.atleast_1d(pricer.price_from_amplitude(np.sin(th) ** 2))
                m_max = 2 * max(ladder.powers) + 1
                mode_err = float(np.mean(np.abs(th - pricer.theta()) > np.pi / (2 * m_max)))
            r_g = rng_for(sc.index, n, d, "mcgrid")
            mcgs = [mcg.price(o, ladder.calls, r_g).value for _ in range(draws)]
            calls, mc_rmse, qmc_rmse, qmc_calls = per_budget[d]
            rows.append(dict(
                scenario=sc.index, moneyness=sc.moneyness, maturity=sc.maturity_label, vol=sc.vol, rate=sc.rate,
                qubits=n, depth=d, bs=bs, grid_price=gp, circuit_price=cp, worthless=int(pricer.worthless),
                calls_qae=ladder.calls, qae_mean=float(np.mean(est)),
                qae_rmse_grid=_rmse(est, gp), qae_rmse_bs=_rmse(est, bs),
                qae_medae_grid=_medae(est, gp), qae_mode_errors=mode_err,
                mc_rmse_bs=mc_rmse, mcgrid_rmse_grid=_rmse(mcgs, gp), mcgrid_medae_grid=_medae(mcgs, gp),
                qmc_rmse_bs=qmc_rmse, calls_qmc=qmc_calls))
    return rows


def run(out_csv: str, start: int = 0, stop: int | None = None, processes: int = 1, progress: bool = True):
    """Run scenarios [start, stop) and append rows to out_csv. Scenarios already in the file are skipped (resumable)."""
    todo = scenarios()[start:stop]
    done = set()
    if os.path.exists(out_csv):
        with open(out_csv) as f:
            done = {int(r["scenario"]) for r in csv.DictReader(f)}
    todo = [s for s in todo if s.index not in done]
    if not todo:
        return 0
    write_header = not os.path.exists(out_csv)
    t0 = time.time()
    with open(out_csv, "a", newline="") as f:
        w = None
        if processes > 1:
            from multiprocessing import Pool
            with Pool(processes) as pool:
                it = pool.imap_unordered(run_scenario, todo)
                for k, rows in enumerate(it, 1):
                    w = w or csv.DictWriter(f, fieldnames=list(rows[0]))
                    if write_header:
                        w.writeheader(); write_header = False
                    w.writerows(rows); f.flush()
                    if progress and k % 50 == 0:
                        print(f"{k}/{len(todo)} scenarios, {time.time() - t0:.0f} s", flush=True)
        else:
            for k, sc in enumerate(todo, 1):
                rows = run_scenario(sc)
                w = w or csv.DictWriter(f, fieldnames=list(rows[0]))
                if write_header:
                    w.writeheader(); write_header = False
                w.writerows(rows); f.flush()
    return len(todo)


def verify_circuits(n_scenarios: int = 20, seed: int = SEED):
    """Full statevector simulation of A Q^k on a random subset of scenarios.

    Checks that P(objective = 1) after k Grover steps equals sin^2((2k+1) theta) - the identity the
    'born' backend relies on. Powers up to 64 for 3-5 price qubits, up to 8 for 6-7 (simulation cost).
    Returns rows with the largest absolute difference per (scenario, qubits).
    """
    rng = np.random.default_rng(seed)
    pick = rng.choice(len(scenarios()), n_scenarios, replace=False)
    out = []
    for idx in sorted(pick):
        sc = scenarios()[idx]
        for n in QUBITS:
            p = QuantumPricer(LognormalGrid(sc.option, n))
            if p.worthless:
                continue
            powers = Ladder.exponential(8 if n <= 5 else 5).powers
            sim = p.probabilities_after_grover(powers)
            th = p.theta()
            theory = np.array([np.sin((2 * k + 1) * th) ** 2 for k in powers])
            out.append(dict(scenario=int(idx), qubits=n, max_power=max(powers),
                            max_abs_diff=float(np.max(np.abs(sim - theory))),
                            grid_vs_circuit=abs(p.price_exact() - p.grid.price())))
    return out
