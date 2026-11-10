"""Contract and market inputs."""
from dataclasses import dataclass
import math
import numbers


@dataclass(frozen=True)
class Option:
    """A European call on a non-dividend-paying underlying, under Black-Scholes dynamics.

    Attributes
    ----------
    spot : float      underlying price today, S0 > 0
    strike : float    strike K > 0
    rate : float      continuously compounded risk-free rate r (may be negative)
    vol : float       Black-Scholes volatility sigma > 0, annualised
    maturity : float  time to maturity T > 0, in years
    """
    spot: float = 100.0
    strike: float = 105.0
    rate: float = 0.03
    vol: float = 0.20
    maturity: float = 1.0

    def __post_init__(self):
        for name in ("spot", "strike", "vol", "maturity"):
            v = getattr(self, name)
            if isinstance(v, bool) or not (isinstance(v, numbers.Real) and math.isfinite(v) and v > 0):
                raise ValueError(f"{name} must be a positive finite number, got {v!r}")
        if isinstance(self.rate, bool) or not (isinstance(self.rate, numbers.Real) and math.isfinite(self.rate)):
            raise ValueError("rate must be finite")

    @property
    def discount(self) -> float:
        """Discount factor exp(-rT)."""
        return math.exp(-self.rate * self.maturity)

    @property
    def log_mean(self) -> float:
        """Mean of ln S_T under the risk-neutral measure: ln S0 + (r - sigma^2/2) T."""
        return math.log(self.spot) + (self.rate - 0.5 * self.vol ** 2) * self.maturity

    @property
    def log_std(self) -> float:
        """Standard deviation of ln S_T: sigma * sqrt(T)."""
        return self.vol * math.sqrt(self.maturity)

    def payoff(self, prices):
        """Call payoff max(S_T - K, 0), vectorised over an array of terminal prices."""
        import numpy as np
        return np.maximum(np.asarray(prices, dtype=float) - self.strike, 0.0)
