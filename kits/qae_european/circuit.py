"""The simplest amplitude-estimation pricer for a European call.

One circuit A on n + 1 qubits:
  1. load the discretised price distribution on n qubits (exact state preparation);
  2. for each price point, rotate one extra qubit so that P(extra qubit = 1) equals the
     normalised payoff at that point.
Then P(extra qubit = 1) = E[payoff] / payoff_max, and the price is that probability times
payoff_max, discounted.

The probability is read three ways:
  - exactly, from the statevector (checks the circuit itself);
  - by sampling the circuit, as a quantum computer would without amplitude estimation
    (error falls like 1/sqrt(shots), as in classical Monte Carlo);
  - by maximum-likelihood amplitude estimation (Suzuki et al., 2020): Grover powers of A,
    no phase estimation, error falling close to 1/(number of A calls).
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import StatePreparation, RYGate
from qiskit.quantum_info import Statevector
from scipy.optimize import minimize_scalar

from classical import Option, discretise


def build_a(o: Option, n_qubits: int):
    """Circuit A and the scale payoff_max that turns P(objective = 1) into an undiscounted price."""
    prices, probs = discretise(o, n_qubits)
    payoff = np.maximum(prices - o.strike, 0.0)
    pmax = float(payoff.max())
    if pmax <= 0:
        raise ValueError("the option is worthless on this grid")
    qc = QuantumCircuit(n_qubits + 1, name="A")
    qc.append(StatePreparation(np.sqrt(probs)), range(n_qubits))
    for i, f in enumerate(payoff / pmax):
        if f == 0:
            continue
        theta = 2 * np.arcsin(np.sqrt(f))
        bits = format(i, f"0{n_qubits}b")[::-1]      # qubit 0 is the least significant bit
        zeros = [q for q, b in enumerate(bits) if b == "0"]
        if zeros:
            qc.x(zeros)
        qc.append(RYGate(theta).control(n_qubits), list(range(n_qubits)) + [n_qubits])
        if zeros:
            qc.x(zeros)
    return qc, pmax


def _p_objective(state: Statevector, n_qubits: int) -> float:
    return float(state.probabilities([n_qubits])[1])


def price_exact(o: Option, n_qubits: int) -> float:
    """Price from the exact probability of the circuit."""
    a, pmax = build_a(o, n_qubits)
    return float(np.exp(-o.rate * o.maturity) * pmax * _p_objective(Statevector(a), n_qubits))


def price_sampled(o: Option, n_qubits: int, shots: int, seed: int = 11) -> float:
    """Price from measuring the circuit `shots` times (no amplitude estimation)."""
    a, pmax = build_a(o, n_qubits)
    p = _p_objective(Statevector(a), n_qubits)
    hits = np.random.default_rng(seed).binomial(shots, p)
    return float(np.exp(-o.rate * o.maturity) * pmax * hits / shots)


def grover(a: QuantumCircuit, n_qubits: int) -> QuantumCircuit:
    """Q = A S0 A^dagger S_chi: reflects about the 'good' states (objective = 1), then about A|0>."""
    q = QuantumCircuit(n_qubits + 1, name="Q")
    q.z(n_qubits)                                   # S_chi: phase -1 on objective = 1
    q.compose(a.inverse(), inplace=True)
    q.x(range(n_qubits + 1))                        # S0: phase -1 on |0...0>
    q.h(n_qubits)
    q.mcx(list(range(n_qubits)), n_qubits)
    q.h(n_qubits)
    q.x(range(n_qubits + 1))
    q.compose(a, inplace=True)
    q.global_phase += np.pi
    return q


def price_mlae(o: Option, n_qubits: int, powers=(0, 1, 2, 4, 8, 16, 32), shots: int = 200, seed: int = 11):
    """Maximum-likelihood amplitude estimation; returns (price, number of A calls)."""
    a, pmax = build_a(o, n_qubits)
    q = grover(a, n_qubits)
    rng = np.random.default_rng(seed)
    hits, calls = [], 0
    for k in powers:
        circ = a.copy()
        for _ in range(k):
            circ.compose(q, inplace=True)
        p = _p_objective(Statevector(circ), n_qubits)
        hits.append(rng.binomial(shots, p))
        calls += shots * (2 * k + 1)
    def nll(theta):
        ll = 0.0
        for k, h in zip(powers, hits):
            pk = np.clip(np.sin((2 * k + 1) * theta) ** 2, 1e-12, 1 - 1e-12)
            ll += h * np.log(pk) + (shots - h) * np.log(1 - pk)
        return -ll
    grid = np.linspace(0, np.pi / 2, 2001)
    t0 = grid[np.argmin([nll(t) for t in grid])]
    res = minimize_scalar(nll, bounds=(max(0, t0 - 1e-3), min(np.pi / 2, t0 + 1e-3)), method="bounded")
    return float(np.exp(-o.rate * o.maturity) * pmax * np.sin(res.x) ** 2), calls


if __name__ == "__main__":
    import warnings
    warnings.filterwarnings('ignore')
    from classical import black_scholes_call, discretised_call, monte_carlo_call
    o = Option()
    print(f"Black-Scholes closed form          {black_scholes_call(o):.4f}")
    for n in (3, 4, 5):
        est, calls = price_mlae(o, n)
        print(f"{n} qubits: discretised {discretised_call(o, n):.4f} | circuit exact {price_exact(o, n):.4f}"
              f" | MLAE {est:.4f} with {calls:,} calls of A")
    mc, se = monte_carlo_call(o, calls)
    print(f"Plain Monte Carlo with the same {calls:,} paths: {mc:.4f} +/- {se:.4f} (one standard error)")
