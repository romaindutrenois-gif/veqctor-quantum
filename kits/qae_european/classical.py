"""Classical benchmarks for a European call.

Two references:
- the Black-Scholes closed form, the validated model (the same formula as the Veqctor
  Black-Scholes validation kit);
- the same price computed on the discretised distribution the circuit uses. The circuit
  must match this one to machine precision; the gap between the two references is the
  discretisation error, which shrinks as qubits are added.
"""
from dataclasses import dataclass
import numpy as np
from scipy.stats import norm


@dataclass(frozen=True)
class Option:
    spot: float = 100.0
    strike: float = 105.0
    rate: float = 0.03
    vol: float = 0.20
    maturity: float = 1.0


def black_scholes_call(o: Option) -> float:
    """Black-Scholes price of a European call."""
    if min(o.spot, o.strike, o.vol, o.maturity) <= 0:
        raise ValueError("spot, strike, vol and maturity must be positive")
    sq = o.vol * np.sqrt(o.maturity)
    d1 = (np.log(o.spot / o.strike) + (o.rate + 0.5 * o.vol**2) * o.maturity) / sq
    d2 = d1 - sq
    return float(o.spot * norm.cdf(d1) - o.strike * np.exp(-o.rate * o.maturity) * norm.cdf(d2))


def discretise(o: Option, n_qubits: int, width: float = 4.0):
    """Terminal prices on 2**n points and their probabilities (risk-neutral lognormal).

    The log-price range is mean +/- width standard deviations, cut into 2**n equal bins;
    each point carries the probability of its bin, renormalised to sum to one.
    """
    if n_qubits < 1:
        raise ValueError("n_qubits must be at least 1")
    m = np.log(o.spot) + (o.rate - 0.5 * o.vol**2) * o.maturity
    s = o.vol * np.sqrt(o.maturity)
    edges = np.linspace(m - width * s, m + width * s, 2**n_qubits + 1)
    probs = np.diff(norm.cdf(edges, loc=m, scale=s))
    probs = probs / probs.sum()
    # each bin is represented by the conditional mean of the price inside it (exact for a lognormal),
    # which keeps the discretised forward close to the true one
    lo, hi = edges[:-1], edges[1:]
    cond = np.exp(m + 0.5 * s**2) * (norm.cdf((hi - m - s**2) / s) - norm.cdf((lo - m - s**2) / s))
    raw = np.diff(norm.cdf(edges, loc=m, scale=s))
    prices = np.where(raw > 0, cond / np.where(raw > 0, raw, 1), np.exp((lo + hi) / 2))
    return prices, probs


def discretised_call(o: Option, n_qubits: int) -> float:
    """Discounted call price on the discretised distribution (what the circuit computes)."""
    prices, probs = discretise(o, n_qubits)
    return float(np.exp(-o.rate * o.maturity) * np.sum(probs * np.maximum(prices - o.strike, 0.0)))


def monte_carlo_call(o: Option, n_paths: int, seed: int = 7):
    """Plain Monte Carlo price and its standard error: the classical method amplitude estimation targets."""
    z = np.random.default_rng(seed).standard_normal(n_paths)
    st = o.spot * np.exp((o.rate - 0.5 * o.vol**2) * o.maturity + o.vol * np.sqrt(o.maturity) * z)
    pay = np.exp(-o.rate * o.maturity) * np.maximum(st - o.strike, 0.0)
    return float(pay.mean()), float(pay.std(ddof=1) / np.sqrt(n_paths))
