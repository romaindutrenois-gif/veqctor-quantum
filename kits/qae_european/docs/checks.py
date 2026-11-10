"""Supporting checks quoted in Documents 1 and 3 that are not part of the campaign itself.

Usage (from kits/qae_european, after the campaign):  python docs/checks.py   ->  results/checks.json

1. State-preparation accuracy: how far the probabilities loaded by Qiskit's StatePreparation are from the
   target p_i, for 5, 6 and 7 price qubits, on the widest-grid scenario of the guide (scenario 1000:
   at the money, 5Y, vol 60%, rate 0%). Explains the H0-a deviations (Document 3, section 2.4).
2. Global maximum of the MLAE likelihood: for every campaign configuration with at least one mode error,
   the draws are regenerated from their seeds and the estimator is compared with a 400,001-point grid.
   A mode error is a property of MLAE only if the fine grid agrees with the estimator.
"""
import csv, json, os, warnings
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import StatePreparation
from qiskit.quantum_info import Statevector

from qae_european import LognormalGrid, QuantumPricer, MaximumLikelihoodAE, Ladder
from qae_european.campaign import scenarios, rng_for, SHOTS, DRAWS

warnings.filterwarnings("ignore", category=DeprecationWarning, module="qiskit")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")


def state_preparation(scenario=1000):
    o = scenarios()[scenario].option
    out = {}
    for n in (5, 6, 7):
        g = LognormalGrid(o, n)
        qc = QuantumCircuit(n)
        qc.append(StatePreparation(np.sqrt(g.probs)), range(n))
        sp = Statevector(qc).probabilities()
        p = QuantumPricer(g)
        a_exact = float(np.dot(g.probs, p.f))
        out[n] = {"max_abs_prob_error": float(np.abs(sp - g.probs).max()), "sum_minus_1": float(sp.sum() - 1),
                  "relative_amplitude_error": abs(p.amplitude() - a_exact) / a_exact}
    return {"scenario": scenario, "by_qubits": out}


def global_maximum():
    with open(os.path.join(RES, "campaign.csv")) as f:
        rows = [r for r in csv.DictReader(f) if float(r["qae_mode_errors"]) > 0]
    tt = np.linspace(0, np.pi / 2, 400_001)
    checked, draws_checked, disagreements, mode_draws = 0, 0, 0, 0
    for r in rows:
        s, n, d = int(r["scenario"]), int(r["qubits"]), int(r["depth"])
        p = QuantumPricer(LognormalGrid(scenarios()[s].option, n))
        ae = MaximumLikelihoodAE(Ladder.exponential(d, SHOTS), "born")
        hits = ae.draw_hits(ae.probabilities(p), rng_for(s, n, d, "qae"), DRAWS)   # same stream as the campaign
        th = ae.estimate_theta(hits)
        m = np.array([2 * k + 1 for k in ae.ladder.powers])
        q = np.clip(np.sin(m[:, None] * tt) ** 2, 1e-15, 1 - 1e-15)
        fine = tt[np.argmax(hits @ np.log(q) + (SHOTS - hits) @ np.log(1 - q), axis=1)]
        half = np.pi / (2 * m.max())
        disagreements += int(np.sum(np.abs(fine - th) > half))
        mode_draws += int(np.sum(np.abs(th - p.theta()) > half))
        checked += 1; draws_checked += len(th)
    return {"configurations_with_mode_errors": checked, "draws_checked": draws_checked,
            "mode_error_draws": mode_draws, "estimator_differs_from_fine_grid": disagreements}


if __name__ == "__main__":
    out = {"state_preparation": state_preparation(), "mlae_global_maximum": global_maximum()}
    with open(os.path.join(RES, "checks.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
