"""Maximum-likelihood amplitude estimation (Suzuki et al., 2020), without quantum phase estimation.

For a ladder of Grover powers k_1 < ... < k_m and `shots` measurements at each power, the circuit
A Q^k is measured `shots` times; the number of ones h_k is binomial with probability
sin^2((2k+1) theta). theta is estimated by maximising the log-likelihood
    sum_k h_k log sin^2((2k+1) theta) + (shots - h_k) log cos^2((2k+1) theta)
on [0, pi/2]: a dense grid search, then a bounded refinement around the best grid point.

Cost: one measurement after k steps calls A once and Q k times, i.e. 2k + 1 applications of A
(Q contains A and its inverse). Total calls = shots * sum_k (2k + 1).
"""
from dataclasses import dataclass
import numpy as np
from scipy.optimize import minimize_scalar


@dataclass(frozen=True)
class Ladder:
    """Grover powers and measurements per power.

    The standard ladder of depth m is (0, 1, 2, 4, ..., 2**(m-2)): m powers, the largest 2**(m-2).
    """
    powers: tuple
    shots: int = 100

    @classmethod
    def exponential(cls, depth: int, shots: int = 100) -> "Ladder":
        if depth < 1:
            raise ValueError("depth must be at least 1")
        return cls(tuple([0] + [2 ** j for j in range(depth - 1)]), shots)

    @property
    def calls(self) -> int:
        """Total applications of A."""
        return int(self.shots * sum(2 * k + 1 for k in self.powers))


class MaximumLikelihoodAE:
    """Estimate theta (hence a = sin^2 theta) from simulated measurements.

    Two ways to obtain the measurement probabilities, which give identical results on a noise-free simulator:
      backend="statevector" : simulate the circuits A Q^k with Qiskit's Statevector (slow, used for verification)
      backend="born"        : use P_k = sin^2((2k+1) theta_exact), with theta_exact from the exact statevector
                              of A (fast, used for the campaign; equivalence verified in the test suite)
    """

    GRID_POINTS = 4001

    def __init__(self, ladder: Ladder, backend: str = "born"):
        if backend not in ("born", "statevector"):
            raise ValueError("backend must be 'born' or 'statevector'")
        self.ladder = ladder
        self.backend = backend
        self._grid = np.linspace(0.0, np.pi / 2, self.GRID_POINTS)
        m = np.array([2 * k + 1 for k in ladder.powers])[:, None]
        p = np.clip(np.sin(m * self._grid[None, :]) ** 2, 1e-15, 1 - 1e-15)
        self._logp, self._log1mp = np.log(p), np.log(1 - p)   # shape (powers, grid points)

    def probabilities(self, pricer) -> np.ndarray:
        """P(objective = 1) after k Grover steps, for each power of the ladder."""
        if self.backend == "statevector":
            return pricer.probabilities_after_grover(self.ladder.powers)
        th = pricer.theta()
        return np.array([np.sin((2 * k + 1) * th) ** 2 for k in self.ladder.powers])

    def draw_hits(self, probs: np.ndarray, rng: np.random.Generator, draws: int = 1) -> np.ndarray:
        """Simulated numbers of ones, shape (draws, powers)."""
        return rng.binomial(self.ladder.shots, np.broadcast_to(probs, (draws, len(probs))))

    def estimate_theta(self, hits: np.ndarray) -> np.ndarray:
        """Maximum-likelihood theta for each row of hits (shape (draws, powers))."""
        hits = np.atleast_2d(hits).astype(float)
        s = self.ladder.shots
        ll = hits @ self._logp + (s - hits) @ self._log1mp          # (draws, grid points)
        best = self._grid[np.argmax(ll, axis=1)]
        out = np.empty(len(hits))
        step = self._grid[1] - self._grid[0]
        m = np.array([2 * k + 1 for k in self.ladder.powers])
        for j, (h, t0) in enumerate(zip(hits, best)):
            def nll(t):
                p = np.clip(np.sin(m * t) ** 2, 1e-15, 1 - 1e-15)
                return -float(np.dot(h, np.log(p)) + np.dot(s - h, np.log(1 - p)))
            r = minimize_scalar(nll, bounds=(max(0.0, t0 - step), min(np.pi / 2, t0 + step)), method="bounded",
                                options={"xatol": 1e-12})
            out[j] = r.x
        return out

    def estimate_prices(self, pricer, rng: np.random.Generator, draws: int = 1) -> np.ndarray:
        """Price estimates for `draws` independent repetitions of the whole ladder."""
        if pricer.worthless:
            return np.zeros(draws)
        hits = self.draw_hits(self.probabilities(pricer), rng, draws)
        return np.atleast_1d(pricer.price_from_amplitude(np.sin(self.estimate_theta(hits)) ** 2))
