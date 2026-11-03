"""Shared engine of the benchmarks: the result type and the common interface."""
from dataclasses import dataclass
import numpy as np


@dataclass(frozen=True)
class Estimate:
    """Result of one pricing run.

    value : float         price estimate
    calls : int           number of payoff evaluations (paths or points) actually used; 0 for a closed form
    stderr : float        standard error reported by the method itself, if it has one (NaN otherwise)
    """
    value: float
    calls: int
    stderr: float = float("nan")


class Benchmark:
    """Interface: price(option, budget, rng) returns an Estimate using at most `budget` payoff evaluations."""
    name = "benchmark"

    def price(self, option, budget: int, rng: np.random.Generator) -> Estimate:  # pragma: no cover
        raise NotImplementedError

    @staticmethod
    def _discounted_payoffs(option, terminal_prices: np.ndarray) -> np.ndarray:
        """Shared step: discounted call payoffs for an array of terminal prices."""
        return option.discount * option.payoff(terminal_prices)
