"""Acceptance criteria, stated before running:
1. the circuit reproduces the discretised price to 1e-9 (the circuit is correct);
2. with 6 price qubits the discretised price is within 2% of Black-Scholes (the grid is fine enough);
3. maximum-likelihood amplitude estimation (7 Grover powers, 200 shots each) lands within 1% of the exact circuit price;
4. sampling the circuit without amplitude estimation behaves like Monte Carlo: within 4 standard errors.
"""
import sys, pathlib
import numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from classical import Option, black_scholes_call, discretised_call
from circuit import price_exact, price_mlae, price_sampled, build_a

O = Option()


def test_circuit_matches_discretised_price():
    for n in (2, 3, 4, 5):
        assert abs(price_exact(O, n) - discretised_call(O, n)) < 1e-9


def test_grid_converges_to_black_scholes():
    bs = black_scholes_call(O)
    assert abs(discretised_call(O, 6) - bs) / bs < 0.02
    assert abs(discretised_call(O, 6) - bs) < abs(discretised_call(O, 3) - bs)


def test_mlae_close_to_exact():
    exact = price_exact(O, 4)
    est, calls = price_mlae(O, 4)
    assert abs(est - exact) / exact < 0.01
    assert calls > 0


def test_sampling_behaves_like_monte_carlo():
    n, shots = 4, 20_000
    exact = price_exact(O, n)
    _, pmax = build_a(O, n)
    p = exact / (np.exp(-O.rate * O.maturity) * pmax)
    se = np.exp(-O.rate * O.maturity) * pmax * np.sqrt(p * (1 - p) / shots)
    assert abs(price_sampled(O, n, shots) - exact) < 4 * se
