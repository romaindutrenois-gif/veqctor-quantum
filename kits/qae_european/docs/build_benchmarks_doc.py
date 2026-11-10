"""Generate docs/benchmarks.md = benchmarks_head.md + the benchmark source files, verbatim.

Usage (from kits/qae_european):  python docs/build_benchmarks_doc.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src", "qae_european", "benchmarks")
FILES = [
    ("base.py", "Shared interface and result type"),
    ("black_scholes.py", "Black-Scholes closed form"),
    ("monte_carlo.py", "Plain Monte Carlo, continuous and on the grid"),
    ("quasi_monte_carlo.py", "Quasi-Monte Carlo, scrambled Sobol"),
]
TAIL = """
## 7. Parameters used in the campaign

| Parameter | Value | Where |
| --- | --- | --- |
| Budgets (calls) | 1,800 · 3,500 · 6,800 · 13,300 · 26,200 (equal to the amplitude-estimation ladders of depth 4 to 8) | `campaign.py` |
| Sobol points | largest power of two not above the budget | `quasi_monte_carlo.py` |
| Repetitions per configuration | 50, independent | `campaign.DRAWS` |
| Seeds | master seed 20261103; one stream per (scenario, qubits, depth, method) through `numpy.random.SeedSequence` | `campaign.rng_for` |
| Variance reduction | none in Monte Carlo; Owen scrambling in quasi-Monte Carlo | section 4 |
| Grid for Monte Carlo on the grid | the circuit's own `LognormalGrid(option, n)`, width 4 standard deviations | `monte_carlo.py`, `grid.py` |

Continuous Monte Carlo and quasi-Monte Carlo do not depend on the number of qubits. They are computed once per scenario and budget, and repeated on each qubit row of the results.

## 8. Unit tests of the benchmarks

`tests/test_package.py` checks:

- the Black-Scholes price against the textbook value (S₀ = K = 100, r = 5%, σ = 20%, T = 1: 10.4506) to 10⁻⁹, and the no-arbitrage bounds on a second case;
- that both Monte Carlo settings are unbiased: with 200,000 paths, within 4 standard errors of their own target (Black-Scholes, grid price);
- that quasi-Monte Carlo uses 4,096 points for a budget of 5,000 and lands within 0.02 of Black-Scholes;
- that a campaign row is identical when recomputed from its seed.

Run them with `pytest tests`.
"""


def main():
    with open(os.path.join(HERE, "benchmarks_head.md")) as f:
        out = [f.read().rstrip() + "\n"]
    for k, (name, title) in enumerate(FILES, 1):
        with open(os.path.join(SRC, name)) as f:
            code = f.read().rstrip()
        out.append(f"\n### 6.{k} `{name}`: {title}\n\n```python\n{code}\n```\n")
    out.append(TAIL)
    with open(os.path.join(HERE, "benchmarks.md"), "w") as f:
        f.write("".join(out))
    print("wrote benchmarks.md")


if __name__ == "__main__":
    main()
