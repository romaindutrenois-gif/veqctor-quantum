"""Unit tests of the package (code correctness). The validation campaign itself is in docs/tests.md."""
import math
import numpy as np
import pytest

from qae_european import (Option, LognormalGrid, QuantumPricer, MaximumLikelihoodAE, Ladder,
                          BlackScholes, MonteCarlo, QuasiMonteCarlo)
from qae_european.campaign import run_scenario, scenarios

O = Option()


def test_option_rejects_bad_inputs():
    for bad in (dict(spot=0), dict(strike=-1), dict(vol=0), dict(maturity=0), dict(spot=float("nan"))):
        with pytest.raises(ValueError):
            Option(**bad)


def test_black_scholes_reference_values():
    # textbook value: S=K=100, r=5%, sigma=20%, T=1 -> 10.4506
    assert abs(BlackScholes.call(Option(100, 100, 0.05, 0.2, 1.0)) - 10.450583572185565) < 1e-9
    o = Option(100, 80, 0.01, 0.3, 2.0)
    c = BlackScholes.call(o)
    assert max(o.spot - o.strike * o.discount, 0) <= c <= o.spot     # no-arbitrage bounds


def test_grid_is_a_distribution_and_keeps_the_forward():
    for n in (2, 5, 8):
        g = LognormalGrid(O, n)
        assert abs(g.probs.sum() - 1) < 1e-12 and (g.probs >= 0).all()
        forward = O.spot * math.exp(O.rate * O.maturity)
        assert abs(np.dot(g.probs, g.prices) - forward) / forward < 1e-3


@pytest.mark.parametrize("opt", [O, Option(100, 80, -0.01, 0.6, 3.0), Option(100, 120, 0.01, 0.3, 1 / 12)])
@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_circuit_reproduces_grid_price(opt, n):
    g = LognormalGrid(opt, n)
    assert abs(QuantumPricer(g).price_exact() - g.price()) < 1e-9


def test_worthless_option_prices_zero():
    o = Option(100, 125, 0.0, 0.2, 1 / 52)          # strike far above the grid
    p = QuantumPricer(LognormalGrid(o, 3))
    assert p.worthless and p.price_exact() == 0.0


def test_grover_identity_statevector_equals_born():
    p = QuantumPricer(LognormalGrid(O, 3))
    lad = Ladder.exponential(6)
    sv = MaximumLikelihoodAE(lad, "statevector").probabilities(p)
    born = MaximumLikelihoodAE(lad, "born").probabilities(p)
    assert np.max(np.abs(sv - born)) < 1e-9


def test_ladder_calls():
    assert Ladder.exponential(4, 100).calls == 100 * (1 + 3 + 5 + 9)
    assert Ladder.exponential(8, 100).calls == 26200


def test_mlae_accuracy_and_reproducibility():
    p = QuantumPricer(LognormalGrid(O, 4))
    ae = MaximumLikelihoodAE(Ladder.exponential(8))
    a = ae.estimate_prices(p, np.random.default_rng(3), 20)
    b = ae.estimate_prices(p, np.random.default_rng(3), 20)
    assert np.array_equal(a, b)
    assert np.sqrt(np.mean((a - p.price_exact()) ** 2)) / p.price_exact() < 0.01


def test_monte_carlo_settings_are_unbiased():
    rng = np.random.default_rng(5)
    e = MonteCarlo().price(O, 200_000, rng)
    assert abs(e.value - BlackScholes.call(O)) < 4 * e.stderr
    g = LognormalGrid(O, 4)
    e = MonteCarlo("grid", 4).price(O, 200_000, rng)
    assert abs(e.value - g.price()) < 4 * e.stderr


def test_quasi_monte_carlo_uses_powers_of_two_and_converges():
    e = QuasiMonteCarlo().price(O, 5000, np.random.default_rng(1))
    assert e.calls == 4096
    assert abs(e.value - BlackScholes.call(O)) < 0.02


def test_campaign_grid_and_row():
    sc = scenarios()
    assert len(sc) == 1848
    rows = run_scenario(sc[100], qubits=(3,), depths=(4,), draws=3)
    r = rows[0]
    assert r["calls_qae"] == 1800 and abs(r["circuit_price"] - r["grid_price"]) < 1e-9
    assert run_scenario(sc[100], qubits=(3,), depths=(4,), draws=3) == rows      # seeded: identical


# ---------- added after the internal cold review ----------

def test_mlae_finds_the_global_maximum():
    """The estimator must return the global maximum of the likelihood, checked on a 400,001-point grid,
    including deep ladders where nearly tied peaks occur (regression test for the single-candidate refinement)."""
    p = QuantumPricer(LognormalGrid(Option(100, 100, 0.0, 0.6, 5.0), 5))
    for depth in (8, 12):
        ae = MaximumLikelihoodAE(Ladder.exponential(depth))
        hits = ae.draw_hits(ae.probabilities(p), np.random.default_rng(7), 100)
        th = ae.estimate_theta(hits)
        m = np.array([2 * k + 1 for k in ae.ladder.powers])
        tt = np.linspace(0, np.pi / 2, 400_001)
        q = np.clip(np.sin(m[:, None] * tt) ** 2, 1e-15, 1 - 1e-15)
        ll = hits @ np.log(q) + (100 - hits) @ np.log(1 - q)
        fine = tt[np.argmax(ll, axis=1)]
        assert np.all(np.abs(fine - th) < np.pi / (2 * m.max()))


def test_mlae_on_a_worthless_option_returns_zero():
    p = QuantumPricer(LognormalGrid(Option(100, 1000, 0.0, 0.2, 1 / 52), 3))
    assert p.worthless
    assert np.all(MaximumLikelihoodAE(Ladder.exponential(4)).estimate_prices(p, np.random.default_rng(0), 3) == 0)


def test_inputs_accept_numpy_numbers_and_reject_bad_types():
    o = Option(np.float64(100), np.int64(105), np.float64(0.01), np.float64(0.2), np.int64(1))
    LognormalGrid(o, np.int64(3))
    with pytest.raises(ValueError):
        LognormalGrid(o, 3.0)
    with pytest.raises(ValueError):
        Option(True, 100, 0.0, 0.2, 1.0)
    with pytest.raises(ValueError):
        Ladder.exponential(17)


def test_cli_price_prints_valid_json(capsys):
    import json
    from qae_european.cli import main
    main(["price", "--qubits", "3", "--depth", "4"])
    out = json.loads(capsys.readouterr().out)          # strict JSON: no NaN
    assert out["calls"] == 1800 and out["quasi_monte_carlo"]["stderr"] is None


def test_campaign_resume_refuses_incomplete_scenarios(tmp_path):
    import csv
    from qae_european import campaign
    path = tmp_path / "c.csv"
    rows = run_scenario(scenarios()[0], qubits=(3,), depths=(4,), draws=2)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    with pytest.raises(RuntimeError):
        campaign.run(str(path), 0, 1, progress=False)


# ---------- added after the independent review ----------

@pytest.mark.parametrize("n", [3, 5, 7])
def test_loader_is_exact_to_rounding(n):
    """The explicit loader prepares the grid probabilities to rounding error, including at 7 qubits."""
    from qiskit.quantum_info import Statevector
    from qae_european.quantum import load_distribution
    g = LognormalGrid(Option(100, 100, 0.0, 0.6, 5.0), n)
    assert np.abs(Statevector(load_distribution(g.probs)).probabilities() - g.probs).max() < 1e-13


def test_circuit_price_matches_grid_at_seven_qubits():
    """H0-a at the largest size of the campaign, on the widest grid: within the original 1e-9."""
    g = LognormalGrid(Option(100, 100, 0.0, 0.8, 5.0), 7)
    assert abs(QuantumPricer(g).price_exact() - g.price()) <= 1e-9


def test_negative_payoffs_are_rejected():
    from dataclasses import dataclass

    @dataclass(frozen=True)
    class Forward(Option):
        def payoff(self, prices):
            return np.asarray(prices, dtype=float) - self.strike

    with pytest.raises(ValueError):
        QuantumPricer(LognormalGrid(Forward(100, 100, 0.0, 0.2, 1.0), 3))


@pytest.mark.parametrize("powers, shots", [((), 100), ((0, -1), 100), ((0, 1, 1), 100), ((0, 1), 0), ((0, 1.5), 100)])
def test_ladder_rejects_bad_inputs(powers, shots):
    with pytest.raises(ValueError):
        Ladder(powers, shots)


@pytest.mark.parametrize("width", [float("nan"), float("inf"), 0.0, -1.0])
def test_grid_rejects_bad_width(width):
    with pytest.raises(ValueError):
        LognormalGrid(Option(), 3, width)
