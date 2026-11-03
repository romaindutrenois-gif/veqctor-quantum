"""Black-Scholes closed form for a European call: the reference price."""
import math
from scipy.stats import norm

from .base import Benchmark, Estimate


class BlackScholes(Benchmark):
    """C = S0 N(d1) - K exp(-rT) N(d2),
    d1 = [ln(S0/K) + (r + sigma^2/2) T] / (sigma sqrt T),  d2 = d1 - sigma sqrt T.

    Exact under the model; uses no samples (calls = 0). Implemented with scipy.stats.norm.cdf,
    which is accurate to machine precision across the parameter ranges of the campaign.
    """
    name = "black_scholes"

    @staticmethod
    def call(option) -> float:
        sq = option.log_std
        d1 = (math.log(option.spot / option.strike) + (option.rate + 0.5 * option.vol ** 2) * option.maturity) / sq
        d2 = d1 - sq
        return float(option.spot * norm.cdf(d1) - option.strike * option.discount * norm.cdf(d2))

    def price(self, option, budget: int = 0, rng=None) -> Estimate:
        return Estimate(self.call(option), 0, 0.0)
