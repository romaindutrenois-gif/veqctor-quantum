"""Resource counts: size of the circuits after compilation, and what a target accuracy would cost.

The estimate is for a noise-free, error-free machine: it counts calls of A, Grover powers and CNOT gates,
and says nothing about error correction or run time (see Document 1, section 12).
"""
import numpy as np
from qiskit import transpile

from .grid import LognormalGrid
from .quantum import QuantumPricer

BASIS = ("cx", "rz", "sx", "x")   # a standard hardware-like gate set


def circuit_size(option, n_qubits: int, optimization_level: int = 1, seed: int = 0) -> dict:
    """Qubits, CNOT count and depth of A and of one Grover step Q, compiled to BASIS."""
    p = QuantumPricer(LognormalGrid(option, n_qubits))
    out = {}
    for name, c in (("A", p.circuit_a()), ("Q", p.circuit_q())):
        t = transpile(c, basis_gates=list(BASIS), optimization_level=optimization_level, seed_transpiler=seed)
        out[name] = {"qubits": t.num_qubits, "cx": int(t.count_ops().get("cx", 0)), "depth": int(t.depth())}
    return out


def fit_power_law(calls, errors):
    """Least-squares fit of log(error) = log(c) + slope * log(calls); returns (slope, c)."""
    x, y = np.log(np.asarray(calls, float)), np.log(np.asarray(errors, float))
    slope, logc = np.polyfit(x, y, 1)
    return float(slope), float(np.exp(logc))


def ladder_calls(depth: int, shots: int = 100) -> int:
    """Calls of the exponential ladder of a given depth: shots * (2^depth + depth - 2)."""
    return int(shots * (2 ** depth + depth - 2))


def estimate_at_accuracy(calls, rmse, target_rmse, cx_a: int, cx_q: int, shots: int = 100) -> dict:
    """Extrapolate a fitted error curve of amplitude estimation to a target RMSE.

    calls, rmse      measured RMSE of amplitude estimation at each ladder of the campaign
    target_rmse      RMSE to reach (same units as rmse)
    cx_a, cx_q       compiled CNOT counts of A and of one Grover step Q

    Returns the calls the fitted line needs, the smallest exponential ladder that provides them, its
    largest Grover power, the CNOT count of its deepest circuit A Q^k, and the CNOTs executed over all
    shots. Extrapolation beyond the measured budgets assumes the fitted rate holds: flagged in the output.
    """
    slope, c = fit_power_law(calls, rmse)
    if slope >= 0:
        raise ValueError("error does not decrease with calls: no extrapolation")
    needed = (target_rmse / c) ** (1.0 / slope)
    depth = 1
    while ladder_calls(depth, shots) < needed:
        depth += 1
        if depth > 40:
            raise ValueError("target out of reach of any reasonable ladder")
    powers = [0] + [2 ** j for j in range(depth - 1)]
    k_max = powers[-1]
    executed = shots * sum(cx_a + k * cx_q for k in powers)
    return {"slope": slope, "calls_fitted": float(needed), "depth": depth, "calls_ladder": ladder_calls(depth, shots),
            "largest_power": k_max, "cx_deepest_circuit": int(cx_a + k_max * cx_q), "cx_executed": int(executed),
            "extrapolated": bool(needed > max(calls))}
