"""Quasi-Monte Carlo with a scrambled Sobol sequence (Owen scrambling, scipy.stats.qmc.Sobol).

One-dimensional problem: u_j in (0,1) from the Sobol sequence, Z_j = Phi^{-1}(u_j), then S_T as in plain
Monte Carlo. The number of points is the largest power of two not above the budget (Sobol's balance
properties hold for powers of two), so `calls` can be below the budget; the campaign records it.

Each call uses a fresh scramble seeded from `rng`, so repeated runs are independent randomisations:
the campaign measures the error across repetitions. The method itself reports no standard error.
"""
import numpy as np
from scipy.stats import norm, qmc

from .base import Benchmark, Estimate


class QuasiMonteCarlo(Benchmark):
    name = "quasi_monte_carlo"

    def price(self, option, budget: int, rng: np.random.Generator) -> Estimate:
        if budget < 2:
            raise ValueError("budget must be at least 2")
        m = int(np.floor(np.log2(budget)))
        sobol = qmc.Sobol(d=1, scramble=True, seed=rng)
        u = sobol.random_base2(m).ravel()
        st = np.exp(option.log_mean + option.log_std * norm.ppf(u))
        pay = self._discounted_payoffs(option, st)
        return Estimate(float(pay.mean()), 2 ** m)
