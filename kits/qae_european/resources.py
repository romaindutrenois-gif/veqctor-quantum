"""Resource count for the amplitude-estimation pricer.

Two questions: how big is the circuit (qubits, two-qubit gates, depth after compiling to a
standard gate set), and how many calls to it reach a target accuracy, compared with plain
Monte Carlo. The counts are for this simplest construction (exact state preparation, one
rotation per price point), whose cost grows exponentially with the number of qubits:
practical pricers need efficient loading (see the main README), which is the open problem.
"""
import numpy as np
from qiskit import transpile

from classical import Option, monte_carlo_call
from circuit import build_a, grover


def circuit_size(o: Option, n_qubits: int):
    a, _ = build_a(o, n_qubits)
    q = grover(a, n_qubits)
    out = {}
    for name, c in (("A", a), ("Q", q)):
        t = transpile(c, basis_gates=["cx", "rz", "sx", "x"], optimization_level=1)
        out[name] = {"qubits": t.num_qubits, "cx": t.count_ops().get("cx", 0), "depth": t.depth()}
    return out


def calls_for_accuracy(o: Option, eps: float):
    """A calls for a price error eps: Monte Carlo (sigma/eps)^2 against amplitude estimation ~ pi*payoff_max/eps."""
    _, se = monte_carlo_call(o, 200_000)
    sigma = se * np.sqrt(200_000)
    _, pmax = build_a(o, 5)
    return {"monte_carlo_paths": int(np.ceil((sigma / eps) ** 2)), "amplitude_estimation_calls": int(np.ceil(np.pi * pmax / eps))}


if __name__ == "__main__":
    o = Option()
    for n in (3, 4, 5, 6):
        s = circuit_size(o, n)
        print(f"{n} price qubits: A {s['A']['qubits']} qubits, {s['A']['cx']} CNOTs, depth {s['A']['depth']} | "
              f"Q {s['Q']['cx']} CNOTs, depth {s['Q']['depth']}")
    for eps in (0.1, 0.01, 0.001):
        c = calls_for_accuracy(o, eps)
        print(f"price error {eps}: Monte Carlo {c['monte_carlo_paths']:,} paths | amplitude estimation ~{c['amplitude_estimation_calls']:,} calls of A")
