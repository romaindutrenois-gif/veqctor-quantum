"""The quantum circuit: A (load the distribution, encode the payoff) and the Grover operator Q.

Register layout (Qiskit little-endian convention)
-------------------------------------------------
qubits 0 .. n-1 : price register; basis state |i> stands for grid point i (qubit 0 = least significant bit)
qubit n         : objective qubit; P(objective = 1) = a = E[payoff] / payoff_max on the grid

Price from the amplitude: price = discount * payoff_max * a.
"""
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import StatePreparation, RYGate
from qiskit.quantum_info import Statevector

from .grid import LognormalGrid


class QuantumPricer:
    """Builds the circuits for one option on one grid, and gives their exact probabilities.

    Parameters
    ----------
    grid : LognormalGrid   the discretised distribution (fixes the option and the number of price qubits)

    Attributes
    ----------
    n : int                number of price qubits; the circuits have n + 1 qubits
    payoff_max : float     largest payoff on the grid (0 if the option is worthless on the grid)
    f : ndarray            normalised payoffs f_i = payoff_i / payoff_max, in [0, 1]
    """

    def __init__(self, grid: LognormalGrid):
        self.grid = grid
        self.n = grid.n_qubits
        pay = grid.payoffs()
        self.payoff_max = float(pay.max())
        self.f = pay / self.payoff_max if self.payoff_max > 0 else np.zeros_like(pay)
        self._a = None
        self._amp = None   # cached exact amplitude

    @property
    def worthless(self) -> bool:
        """True when every grid point is out of the money: the circuit price is exactly 0."""
        return self.payoff_max <= 0

    # ---------- circuits ----------
    def circuit_a(self) -> QuantumCircuit:
        """Circuit A on n + 1 qubits.

        Block 1: StatePreparation loads sum_i sqrt(p_i) |i> on the price register.
        Block 2: for each grid point i with f_i > 0, an RY(theta_i) on the objective qubit,
                 controlled on the price register being exactly |i>, with theta_i = 2 arcsin(sqrt(f_i)).
                 Control on |i> is implemented by X gates on the qubits where bit i is 0, before and after.
        """
        if self._a is not None:
            return self._a
        n = self.n
        qc = QuantumCircuit(n + 1, name="A")
        qc.append(StatePreparation(np.sqrt(self.grid.probs)), range(n))
        for i, fi in enumerate(self.f):
            if fi <= 0:
                continue
            theta = 2.0 * np.arcsin(np.sqrt(min(fi, 1.0)))
            bits = format(i, f"0{n}b")[::-1]
            zeros = [q for q, b in enumerate(bits) if b == "0"]
            if zeros:
                qc.x(zeros)
            qc.append(RYGate(theta).control(n), list(range(n)) + [n])
            if zeros:
                qc.x(zeros)
        self._a = qc
        return qc

    def circuit_q(self) -> QuantumCircuit:
        """Grover operator Q = A S0 A^dagger S_chi (with a global phase of pi).

        S_chi: phase -1 on states with objective = 1 (a Z on the objective qubit).
        S0:    phase -1 on |0...0> (X on all qubits, multi-controlled Z, X on all qubits).
        If a = sin^2(theta), k applications of Q after A give P(objective = 1) = sin^2((2k+1) theta).
        """
        a = self.circuit_a()
        n = self.n
        q = QuantumCircuit(n + 1, name="Q")
        q.z(n)
        q.compose(a.inverse(), inplace=True)
        q.x(range(n + 1))
        q.h(n)
        q.mcx(list(range(n)), n)
        q.h(n)
        q.x(range(n + 1))
        q.compose(a, inplace=True)
        q.global_phase += np.pi
        return q

    # ---------- exact probabilities (noise-free simulator) ----------
    def amplitude(self) -> float:
        """a = P(objective = 1) after A, from the exact statevector."""
        if self.worthless:
            return 0.0
        if self._amp is None:
            self._amp = float(Statevector(self.circuit_a()).probabilities([self.n])[1])
        return self._amp

    def theta(self) -> float:
        """theta in [0, pi/2] with a = sin^2(theta)."""
        return float(np.arcsin(np.sqrt(min(max(self.amplitude(), 0.0), 1.0))))

    def probabilities_after_grover(self, powers) -> np.ndarray:
        """P(objective = 1) after A then k steps of Q, for each k in powers, by full statevector simulation."""
        if self.worthless:
            return np.zeros(len(powers))
        q = self.circuit_q()
        state = Statevector(self.circuit_a())
        out, done = {}, 0
        for k in sorted(set(powers)):
            while done < k:
                state = state.evolve(q)
                done += 1
            out[k] = float(state.probabilities([self.n])[1])
        return np.array([out[k] for k in powers])

    def price_from_amplitude(self, a) -> float:
        """Discounted price corresponding to an amplitude a."""
        v = self.grid.option.discount * self.payoff_max * np.asarray(a, dtype=float)
        return float(v) if v.ndim == 0 else v

    def price_exact(self) -> float:
        """Price from the exact amplitude: equals grid.price() up to floating point."""
        return self.price_from_amplitude(self.amplitude())
