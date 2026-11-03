"""Plain Monte Carlo, with two sampling settings.

sampling="continuous": draws S_T exactly from the lognormal, S_T = S0 exp((r - sigma^2/2) T + sigma sqrt(T) Z),
                       Z standard normal. Unbiased for the Black-Scholes price.
sampling="grid":       draws grid points with the probabilities of the circuit's LognormalGrid
                       (n price qubits). Unbiased for the grid price, i.e. the same target as the circuit:
                       it isolates statistical error from discretisation bias.

No variance reduction: plain sampling is exactly what amplitude estimation replaces.
Standard error = sample standard deviation / sqrt(budget).
"""
import numpy as np

from .base import Benchmark, Estimate
from ..grid import LognormalGrid


class MonteCarlo(Benchmark):
    def __init__(self, sampling: str = "continuous", n_qubits: int | None = None):
        if sampling not in ("continuous", "grid"):
            raise ValueError("sampling must be 'continuous' or 'grid'")
        if sampling == "grid" and n_qubits is None:
            raise ValueError("grid sampling needs n_qubits")
        self.sampling, self.n_qubits = sampling, n_qubits
        self.name = "monte_carlo" if sampling == "continuous" else f"monte_carlo_grid_{n_qubits}"

    def price(self, option, budget: int, rng: np.random.Generator) -> Estimate:
        if budget < 2:
            raise ValueError("budget must be at least 2")
        if self.sampling == "continuous":
            z = rng.standard_normal(budget)
            st = np.exp(option.log_mean + option.log_std * z)
            pay = self._discounted_payoffs(option, st)
            return Estimate(float(pay.mean()), budget, float(pay.std(ddof=1) / np.sqrt(budget)))
        g = LognormalGrid(option, self.n_qubits)
        counts = rng.multinomial(budget, g.probs)             # equivalent to drawing `budget` grid points
        pay = option.discount * g.payoffs()
        mean = float(np.dot(counts, pay) / budget)
        var = float(np.dot(counts, (pay - mean) ** 2) / (budget - 1))
        return Estimate(mean, budget, float(np.sqrt(var / budget)))
