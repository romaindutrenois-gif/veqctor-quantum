"""Discretisation of the terminal price distribution on 2**n points (the input the circuit loads)."""
from dataclasses import dataclass, field
import math
import numbers
import numpy as np
from scipy.stats import norm

from .option import Option


@dataclass
class LognormalGrid:
    """Risk-neutral lognormal distribution of S_T, discretised on 2**n_qubits points.

    Construction
    ------------
    1. The log-price range [m - width*s, m + width*s] (m, s: mean and standard deviation of ln S_T)
       is cut into 2**n equal bins.
    2. Bin i carries its probability p_i = Phi(edge_{i+1}) - Phi(edge_i), renormalised to sum to 1
       (the mass outside the range, 2*Phi(-width), is redistributed proportionally).
    3. Bin i is represented by the conditional mean of S_T inside it, x_i = E[S_T | S_T in bin i],
       which is exact in closed form for a lognormal. The discretised forward then equals the
       true forward up to the truncated mass.

    Attributes (filled at construction)
    -----------------------------------
    edges : ndarray (2**n + 1,)  bin edges in log-price
    probs : ndarray (2**n,)      probabilities p_i, summing to 1
    prices : ndarray (2**n,)     representative prices x_i
    """
    option: Option
    n_qubits: int
    width: float = 4.0
    edges: np.ndarray = field(init=False, repr=False)
    probs: np.ndarray = field(init=False, repr=False)
    prices: np.ndarray = field(init=False, repr=False)

    def __post_init__(self):
        if isinstance(self.n_qubits, bool) or not (isinstance(self.n_qubits, numbers.Integral) and 1 <= self.n_qubits <= 10):
            raise ValueError("n_qubits must be an integer between 1 and 10 (the circuit uses one controlled rotation per grid point)")
        if isinstance(self.width, bool) or not (isinstance(self.width, numbers.Real) and math.isfinite(self.width) and self.width > 0):
            raise ValueError("width must be a positive finite number")
        m, s = self.option.log_mean, self.option.log_std
        self.edges = np.linspace(m - self.width * s, m + self.width * s, 2 ** self.n_qubits + 1)
        z = (self.edges - m) / s
        raw = np.diff(norm.cdf(z))
        # partial expectation of S_T on each bin: E[S_T 1{bin}] = F * (Phi(z_hi - s) - Phi(z_lo - s))
        forward_undiscounted = np.exp(m + 0.5 * s ** 2)
        partial = forward_undiscounted * np.diff(norm.cdf(z - s))
        self.prices = np.where(raw > 0, partial / np.where(raw > 0, raw, 1.0), np.exp(0.5 * (self.edges[:-1] + self.edges[1:])))
        self.probs = raw / raw.sum()

    @property
    def size(self) -> int:
        return 2 ** self.n_qubits

    def payoffs(self) -> np.ndarray:
        """Call payoff at each grid point."""
        return self.option.payoff(self.prices)

    def price(self) -> float:
        """Discounted expected payoff on the grid: the exact target of the circuit."""
        return float(self.option.discount * np.dot(self.probs, self.payoffs()))
