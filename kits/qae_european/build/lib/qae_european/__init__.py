"""qae_european: amplitude-estimation pricing of a European call, with its classical benchmarks.

Main objects
------------
Option                    contract and market inputs (spot, strike, rate, volatility, maturity)
LognormalGrid             discretisation of the terminal price on 2**n points
QuantumPricer             the circuit A, the Grover operator Q, and exact probabilities
MaximumLikelihoodAE       maximum-likelihood amplitude estimation (no phase estimation)
BlackScholes, MonteCarlo, QuasiMonteCarlo   classical benchmarks (qae_european.benchmarks)
"""
from .option import Option
from .grid import LognormalGrid
from .quantum import QuantumPricer
from .estimation import MaximumLikelihoodAE, Ladder
from .benchmarks import BlackScholes, MonteCarlo, QuasiMonteCarlo, Estimate

__all__ = ["Option", "LognormalGrid", "QuantumPricer", "MaximumLikelihoodAE", "Ladder",
           "BlackScholes", "MonteCarlo", "QuasiMonteCarlo", "Estimate"]
__version__ = "1.0.0"
