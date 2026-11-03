"""Classical benchmarks.

Black-Scholes closed form   the reference ("truth") every error is measured against
MonteCarlo                  plain Monte Carlo: the method amplitude estimation is meant to replace
QuasiMonteCarlo             scrambled Sobol quasi-Monte Carlo: the best classical sampling method for this problem

All three share one interface: price(option, budget, rng) -> Estimate.
"""
from .base import Estimate, Benchmark
from .black_scholes import BlackScholes
from .monte_carlo import MonteCarlo
from .quasi_monte_carlo import QuasiMonteCarlo

__all__ = ["Estimate", "Benchmark", "BlackScholes", "MonteCarlo", "QuasiMonteCarlo"]
