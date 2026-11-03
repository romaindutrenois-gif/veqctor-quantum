"""Resource counts: size of the circuits after compilation, and calls needed for a target accuracy."""
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
