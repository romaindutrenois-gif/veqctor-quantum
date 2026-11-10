"""Supporting checks quoted in Documents 1 and 3 that are not part of the campaign itself.

Usage (from kits/qae_european, after the campaign):  python docs/checks.py   ->  results/checks.json

1. Loading accuracy, separated from the payoff rotations, for 5, 6 and 7 price qubits on scenario 1000
   (at the money, 5Y, vol 60%, rate 0%), for two loaders: the kit's explicit loader (load_distribution) and
   Qiskit's generic StatePreparation (used up to the second campaign run). For each: the largest error on a
   loaded probability; the relative error of the amplitude computed exactly from the loaded probabilities
   (sum_i q_i f_i against sum_i p_i f_i: the loader's share of the error); and the relative error added by
   the payoff rotations given the loaded state (circuit amplitude against sum_i q_i f_i). Also the
   conditioning of StatePreparation: the change in loaded probabilities when the input is perturbed by a
   relative 1e-15. Document 3, section 2.4.
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
from qae_european.quantum import load_distribution
from qae_european.campaign import scenarios, rng_for, SHOTS, DRAWS

warnings.filterwarnings("ignore", category=DeprecationWarning, module="qiskit")
HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "..", "results")


def _qiskit_loader(probs):
    n = int(round(np.log2(len(probs))))
    qc = QuantumCircuit(n)
    qc.append(StatePreparation(np.sqrt(probs)), range(n))
    return qc


def _with_loader(loader, probs, f, n):
    """Circuit A built with a given loader, same payoff rotations as the kit."""
    from qiskit.circuit.library import RYGate
    qc = QuantumCircuit(n + 1)
    qc.compose(loader(probs), range(n), inplace=True)
    for i, fi in enumerate(f):
        if fi <= 0:
            continue
        zeros = [q for q, b in enumerate(format(i, f"0{n}b")[::-1]) if b == "0"]
        if zeros: qc.x(zeros)
        qc.append(RYGate(2.0 * np.arcsin(np.sqrt(min(fi, 1.0)))).control(n), list(range(n)) + [n])
        if zeros: qc.x(zeros)
    return qc


def loading(scenario=1000):
    o = scenarios()[scenario].option
    out = {}
    for name, loader in (("explicit loader (kit)", load_distribution), ("Qiskit StatePreparation", _qiskit_loader)):
        rec = {}
        for n in (5, 6, 7):
            g = LognormalGrid(o, n)
            f = QuantumPricer(g).f
            q = Statevector(loader(g.probs)).probabilities()
            a_true = float(np.dot(g.probs, f))
            a_loaded = float(np.dot(q, f))
            a_circ = float(Statevector(_with_loader(loader, g.probs, f, n)).probabilities([n])[1])
            pert = g.probs * (1 + 1e-15 * np.random.default_rng(0).standard_normal(len(g.probs)))
            q2 = Statevector(loader(pert / pert.sum())).probabilities()
            rec[n] = {"max_abs_prob_error": float(np.abs(q - g.probs).max()), "sum_minus_1": float(q.sum() - 1),
                      "rel_amplitude_error_from_loading": abs(a_loaded - a_true) / a_true,
                      "rel_amplitude_error_added_by_rotations": abs(a_circ - a_loaded) / a_true,
                      "prob_change_for_1e-15_input_perturbation": float(np.abs(q2 - q).max())}
        out[name] = rec
    return {"scenario": scenario, "by_loader": out}


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
    out = {"loading": loading(), "mlae_global_maximum": global_maximum()}
    with open(os.path.join(RES, "checks.json"), "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps(out, indent=1))
