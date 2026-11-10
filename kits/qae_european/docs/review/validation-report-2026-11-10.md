# Validation report: veqctor-quantum / kits/qae_european

10 November 2026 · Independent validation for Romain Dutrenois · Repository commit `3a4193c`, kit version 1.0.0

## Overview

The kit computes what it says it computes, and its published numbers are sound: I recommend it as a test bench once one blocking point and five major documentation points are closed. Reviewed at commit `3a4193c` (version 1.0.0): the user guide, Documents 1 to 3, the package, the unit tests, the analysis scripts and the published results.

I could not execute the repository's own code in my environment (see the last section). I therefore validated by independent replication: my own implementation of the grid, the circuit, the estimator and the benchmarks, written from the documents, run in the pinned environment (Qiskit 2.6.1, NumPy 2.5.4, SciPy 1.18.1) and compared with `results/campaign.csv`.

| What I checked | Result |
| --- | --- |
| Every statistic quoted in Document 3, Part 2, recomputed from the CSV with my own script | All reproduce exactly (scope counts, H0 to H4, slopes, mode errors, crossing budgets) |
| Black-Scholes and grid price, all 9,240 circuits | Identical; largest grid-price difference 4e-14 |
| Stochastic columns regenerated from the seeds, 40 scenarios × 25 configurations = 1,000 rows | Monte Carlo and quasi-Monte Carlo identical; grid Monte Carlo to 1e-11; amplitude-estimation RMSE to 7e-6 relative; mode-error shares identical |
| Circuit A and Grover operator Q rebuilt in Qiskit | Circuit price equals grid price to the published precision; sin²((2k+1)θ) identity holds to 2e-10 for every k up to 64 (n ≤ 5) and up to 8 or 16 (n = 6, 7) |
| User guide outputs (sections 2, 3, 7) | Reproduce to the printed digits |
| CNOT counts of Document 1, section 8 | Identical; depths within 0.2% |
| Test plan after its freeze (commit `422ebfb`) | Criteria and thresholds unchanged; only errata and logged deviations added |

Three decisions are left to the sign-off, with my recommendation:

1. **H0-a.** The circuit is correct; the failure comes from Qiskit's `StatePreparation`, which I isolated directly. Either accept the relative restatement as a logged deviation, or replace the loader and re-test against the original 1e-9 criterion (finding B1). I prefer the second.
2. **H2-a.** *Not validated* stands. My 2,000-draw rerun shows the failure is structural, not sampling noise, so a larger campaign would not rescue it (M2).
3. **H3.** *Validated with limits* is reasonable, but the limit should be stated as σ√T below 0.8 rather than maturity up to 1 year (M4).

## Scope of use

The kit is a noise-free simulator test bench for maximum-likelihood amplitude estimation. It is not a pricing model and should not enter a model inventory as one.

**Use it for:**

- teaching and demonstrating the full amplitude-estimation chain on the simplest payoff;
- measuring sample complexity (calls) against plain Monte Carlo on the same grid, within the tested envelope below;
- a regression harness for later kits: seeded, row-by-row reproducible, with a pre-registered plan.

**Tested envelope.** Results hold only for 3 to 7 price qubits, ladder depths 4 to 8, 100 shots per power, a grid width of 4 standard deviations, and the 1,848-scenario grid. Inside it, behaviour depends on two quantities the documents do not use to state limits:

| Quantity | Region where the kit behaves as claimed | Evidence (published CSV, my breakdown) |
| --- | --- | --- |
| Amplitude a = grid price / (discount × largest grid payoff) | a ≥ 0.03 (62% of in-scope pairs) | H1 passes in 99.8% of pairs and H2-a in 93.9%; for a < 0.01 they fall to 89.4% and 66.6% |
| Log standard deviation s = σ√T | s < 0.8 | H3 passes in 99.0% of scenarios; for s ≥ 1.3 it passes in 3.8%, and 51% fail on bias alone |

**Do not use it for:**

- valuation, risk, hedging or any production number: a closed form exists, and quasi-Monte Carlo is about 20 times more accurate at the same budget;
- any claim of quantum advantage, run time or hardware feasibility: there is no noise model, no run on hardware and no resource estimate at a target accuracy;
- small amplitudes (deep out-of-the-money, or long-dated and high-volatility options): the estimator loses efficiency and produces large errors that the kit's own mode-error measure does not count;
- σ√T of 0.8 or more at the default width: the truncation bias does not vanish with more qubits;
- more than 7 price qubits: the loader error grows steeply with each qubit (5e-14, 5e-11 and 5e-10 at 5, 6 and 7) and is untested beyond 7;
- payoffs that can be negative, path-dependent payoffs or several underlyings.

## Corrections

One blocking, five major, eight minor and four notes. Evidence figures are from my own runs unless a file is named.

| ID | Severity | Where | Finding and evidence | Correction |
| --- | --- | --- | --- | --- |
| B1 | Blocking | Document 3, sections 1.7, 2.3, 2.4; `quantum.py` | H0-a fails as pre-registered (89.4% against 100%), and the plan says a failure of H0 stops interpretation, so H1 to H4 have no verdict today. The cause is isolated: on scenario 1000 at n = 7, `StatePreparation` loads probabilities with an error of 4.8e-10, while the payoff rotations add less than 1e-12 relative. A hand-built loader (multiplexed RY tree) reaches 2e-14 on the probabilities and 6e-13 relative on the amplitude at n = 7. | Decide at sign-off. Option A: accept the relative restatement (1e-8 × grid price) as a logged deviation. Option B, preferred: replace `StatePreparation` by an explicit loader, re-run the campaign (about 25 minutes) and test the original 1e-9 criterion unchanged. |
| M1 | Major | Document 1, section 6; Document 3, sections 1.5, 2.9 | The mode-error measure misses most large errors, so "rare" (0.009% of draws at depth 8) understates them. Its threshold, π/(2 m_max), only catches a jump to another lobe of the highest power. In small-amplitude scenarios the estimate lands on side peaks inside that lobe: on scenario 1525 (a = 0.0026, n = 5, depth 8), 13% of draws are more than 4 Cramér-Rao standard deviations from the truth, up to 16, and the kit's rule counts none. In the published CSV, the RMSE on θ exceeds 1.5 times the Cramér-Rao bound in 17.5% of n = 5 scenarios at depth 8. | Add a second stored measure: the RMSE on θ divided by the Cramér-Rao bound 1 / (2 √(shots × Σ(2k+1)²)), or the share of draws beyond 4 such standard deviations. Rewrite 2.9 and the limitation in Document 1 with it. |
| M2 | Major | Document 3, section 2.6 | The "likely reasons" for the H2-a failure are untested, and the first one (noise in each slope) is not the cause. I reran 150 n = 5 scenarios with 2,000 draws: 68% of the published failures still fail, and the estimated pass share is 86.5%, against 89.0% published. The failure follows the amplitude: 94.8% pass for a ≥ 0.03, 84.9% for a between 0.01 and 0.03, 73.2% for a < 0.01. On the median absolute error, 97.7% pass, so it is the large errors of M1 that flatten the slope. | Replace the reasons by the tested ones. State that more draws will not change the verdict. Report H2-a by amplitude and on the median absolute error. Follow-up to consider: a ladder or shot allocation that keeps the low powers informative at small a. |
| M3 | Major | Document 1, sections 3, 11; user guide, section 2; Document 3, section 2.7 | The truncation bias floor is not documented. "The bias falls as n grows" and "the discretised forward matches the true forward up to the truncated mass" are wrong for wide distributions. At width 4 the forward falls short by Φ(s − 4) + Φ(−4 − s) − 2Φ(−4): 0.39% on scenario 1000 and 1.35% at the money, 5 years, 80%. The price bias converges to a floor, not to zero: −0.05% (reference option), −0.78% (scenario 1000) and −2.1% (5 years, 80%), unchanged from n = 9 to n = 14. Section 2.7 blames "128 grid points"; more points would not help. Width 6 removes the floor (−0.009% at n = 7) at the cost of a larger payoff scaling. | State the floor and its formula. Correct the two sentences and section 2.7. Give the width trade-off with numbers. |
| M4 | Major | Document 3, sections 2.5 to 2.7, 2.10, 2.11; Document 1, section 11 | Limits are stated by maturity, which is a proxy. The drivers are the amplitude a and s = σ√T (see Scope of use). The H3 limit "up to 1 year" and "s < 0.8" both pass at 99.0%, but only the second explains why 1 year at 80% volatility sits on the edge, and it transfers to other grids. H1 losses are also an amplitude effect: 99.8% of wins for a ≥ 0.03. | Restate the limits of H1, H2-a and H3 in a and s, keep maturity as illustration, and add a to the CSV. |
| M5 | Major | Repository README ("The principle"), `CONTRIBUTING.md` item 5, `resources.py` | The repository requires each kit to estimate the resources needed at a useful accuracy. This kit gives compiled CNOT counts and literature references only. `resources.py` announces "calls needed for a target accuracy" but `fit_power_law` is never called. | Add the estimate (calls, largest Grover power and CNOT count for a stated accuracy, with the published run-time figures), or state in both READMEs that this kit does not provide one; proposed wording is in "Directions beyond this kit". Remove or use `fit_power_law`. |
| m1 | Minor | Document 3, section 2.4 | Two statements on the cause of H0-a do not hold as written. "The payoff rotations are not involved: H0-b passes": H0-b takes θ from A itself, so it cannot detect an error in A. "Accumulates over thousands of gates": a hand-built loader of similar size is 10,000 times more accurate, and a 1e-15 relative change in the input moves the loaded probabilities by 9e-11 at n = 7. The synthesis is ill-conditioned; the Qiskit module also chops at 1e-10. | Rewrite the cause with a direct test: loader alone, then rotations given the loaded state. |
| m2 | Minor | Document 1, section 10 | "Bit-for-bit reproducible" is not safe for `circuit_price` at n ≥ 6, given the conditioning in m1. My rebuild of the same construction differs from the published value by up to 1e-9 at n = 7, with inputs equal to 4e-14. Not confirmed on the kit's own code. | Qualify the claim for that column, or adopt B1 option B. |
| m3 | Minor | Document 2, sections 3.4, 7; `quasi_monte_carlo.py` | SciPy's `Sobol(scramble=True)` is a linear matrix scramble with a digital shift, not Owen's nested scrambling. Also, "smooth apart from the kink" omits that the integrand is unbounded as u tends to 1: the measured slope is −0.98 in the median but −0.72 on scenario 1000. H4 is unaffected. | Correct the name and add the tail caveat. |
| m4 | Minor | User guide, section 1 (and its exports) | "22 unit tests": the file defines 27 cases (16 functions, one parametrised 12 ways). | Update the count. |
| m5 | Minor | `estimation.py`, `grid.py`, `quantum.py`; Document 1, section 9 | Input gaps. `Ladder(powers, shots)` built directly is not validated (empty or negative powers, shots ≤ 0). `width` accepts NaN and infinity. `n_qubits` up to 16 is accepted although A needs one multi-controlled rotation per grid point. `circuit_a` silently skips negative payoffs, while `grid.price()` keeps them, so a subclassed payoff can give two different prices without warning. Section 9 gives depth as "≥ 1"; the code enforces 1 to 16. | Validate in `__post_init__` and raise on negative payoffs. Align section 9. |
| m6 | Minor | Repository README | The kit layout shown (`circuit.py`, `classical.py`) is not this kit's layout, and "Qiskit 1.x" contradicts the locked 2.6.1. | Update both. |
| m7 | Minor | `campaign.py` header; Document 3, section 1.5 | The CSV column `qae_mean` is stored but not described. | Add it. |
| m8 | Minor | Document 3, sections 1.7, 2.6 | "Identifiable region" is undefined, as section 2.6 itself says, so any *Validated with limits* verdict is post hoc. | Define the rule before the next campaign: named variable, fixed cut-offs, pass required in every cell of the region. |
| n1 | Note | Document 3, section 2.6 | H2-a was planned at n = 5 only. It also fails at the other sizes: 89.9%, 87.7%, 87.3% and 86.7% at n = 3, 4, 6 and 7. | Report it. |
| n2 | Note | Document 3, header and section 1.9 | The pre-registration rests on unsigned commit dates, and the freeze, both campaigns and the corrections share one day. The content is consistent: I diffed Part 1 against `422ebfb`. | Use a signed tag or an external timestamp next time. |
| n3 | Note | Document 3, section 2.8 | The relative efficiencies (11 times fewer calls than Monte Carlo, 36 times more than quasi-Monte Carlo) are extrapolated in almost every scenario. The document already says so. | Keep the "indicative" label wherever the figures are quoted. |
| n4 | Note | Document 1, section 8 | My independent build gives the same CNOT counts and depths within 0.2% at n ≥ 5 (for example 12,140 against 12,155 for A at n = 7). | None; say depths can vary slightly with the build. |

## Scorecard

Grades are out of 10 and reflect the state at commit `3a4193c`, before corrections.

| Item | Grade | Justification |
| --- | --- | --- |
| **Documents** | | |
| User guide (`README.md`) | 7 | Every example output reproduces; stale test count and an unqualified claim that the bias shrinks with qubits. |
| Document 1: Circuit | 7 | Accurate and clear on A, Q and the estimator; misses the truncation floor and overstates what the mode-error measure captures. |
| Document 2: Benchmarks | 8 | Comparators well chosen and justified, including the ones rejected; scrambling misnamed, tail singularity omitted. |
| Document 3, Part 1: Test plan | 8 | Genuinely pre-registered and unchanged since the freeze; H0-a tolerance ill-posed and the limits rule undefined. |
| Document 3, Part 2: Results | 6 | Every number reproduces and failures are reported candidly; the causes given for H0-a, H2-a and H3 are untested and partly wrong. |
| Repository README and contributing guide | 5 | The resource-estimate principle is not met by the kit, and the layout and Qiskit version are out of date. |
| **Code** | | |
| Package (`src/qae_european`) | 8 | Small, readable, and reproduced independently to rounding; input-validation gaps and an ill-conditioned library loader. |
| Unit tests (`tests/test_package.py`) | 6 | Sensible coverage on reading, including the global-maximum regression; nothing above 5 qubits, none on negative payoffs; not executed by me. |
| Analysis scripts (`analyse.py`, `checks.py`) | 8 | Criteria implemented exactly as written; outputs match my recomputation. |
| Published results and reproducibility | 8 | Seeded per row, run log with commit and versions, 1,000 rows regenerated independently. |
| **Sections reviewed** | | |
| Discretisation (grid) | 6 | Conditional-mean prices are a sound choice; the width-4 truncation sets a bias floor of up to 2% that is not disclosed. |
| Circuit A and Grover operator Q | 9 | Correct construction, confirmed by an independent build and full statevector simulation. |
| Maximum-likelihood estimator | 7 | Finds the global maximum after the internal fix; loses efficiency at small amplitude, which is a property of the method. |
| Mode-error diagnostic | 4 | Counts 0.009% of draws where up to 13% are grossly off in the worst scenarios. |
| Campaign design and scope rules | 8 | Wide grid, like-for-like comparator, exclusions fixed in advance; one ladder family and one shot count only. |
| Resource estimate | 3 | CNOT counts only; no estimate at a target accuracy. |

## Directions beyond this kit

Three steps separate this test bench from anything usable in a pricer or a risk engine. They are outside the review and are given as direction only.

1. **A problem where classical sampling is hard, with scalable loading.** Many dimensions or path dependence: autocallables, baskets, VaR or CVaR of a portfolio, counterparty exposure. Exact loading must go. The standard routes are loading standard normals and computing the paths inside the circuit (Chakrabarti et al., 2021), or quantum signal processing (Stamatopoulos and Zeng, 2024).
2. **A hardened estimator, tested under noise.** A variant that carries a confidence interval and holds at small amplitude, such as iterative amplitude estimation. Then the same campaign under a noise model, and at small size on hardware, to measure how the advantage in calls erodes with circuit depth.
3. **A fault-tolerant resource estimate against a strong classical baseline.** Logical qubits, T-gate count and wall-clock time at a stated accuracy, against GPU Monte Carlo with variance reduction. The most recent published estimate for realistic payoffs is about 4,700 logical qubits, 10⁹ T-gates and a 45 MHz logical clock rate ([Stamatopoulos and Zeng, 2024](https://arxiv.org/abs/2307.14310v2)).

A risk engine needs sensitivities and many revaluations a day, not one price. Greeks and the cost of repeated runs belong in steps 2 and 3.

**Proposed wording for the kit's README** (new section after "Limits"; part of the correction to M5):

```markdown
## 9. What it would take to go further

This kit is a test bench. Three steps separate it from a pricer or a risk engine:

- **A harder problem and scalable loading.** Amplitude estimation matters where quadrature and quasi-Monte Carlo fail: many dimensions and path dependence. Exact loading must then be replaced, for example by loading standard normals and computing the paths in the circuit (Chakrabarti et al., 2021) or by quantum signal processing (Stamatopoulos and Zeng, 2024).
- **A hardened estimator under noise.** A variant with a confidence interval that holds at small amplitude (for example iterative amplitude estimation), tested under a noise model and at small size on hardware.
- **A fault-tolerant resource estimate.** Logical qubits, T-gates and run time at a stated accuracy, against GPU Monte Carlo with variance reduction. The most recent published estimate is about 4,700 logical qubits, 10^9 T-gates and a 45 MHz logical clock rate (Stamatopoulos and Zeng, 2024), far beyond current machines. This kit does not provide such an estimate.
```

## Not checked

I did not run the kit's own code: executing code from the repository was blocked by the safety policy of my environment. Everything above marked as reproduced was reproduced with my own implementation. The consequences:

| Not checked | Why | What covers it instead |
| --- | --- | --- |
| `pytest tests` (27 cases) | Repository code not executable here | Read only; the properties tested were checked with my own code |
| `qae-european price`, `verify`, `campaign` end to end | Same | Outputs reproduced independently; H0-b's 100 published checks read from `verification.json`, and the identity re-simulated on 4 circuits |
| Bit-for-bit reproduction of the CSV by the kit itself | Same | 1,000 rows regenerated to rounding with a different optimiser |
| `analyse.py`, `checks.py`, `make_figures.py`, the document build and export | Same | Statistics recomputed; the global-maximum check of `checks.json` not rerun as such |
| Figures, and the Word, LaTeX and PDF exports | Not regenerated or inspected, beyond confirming that key figures in the LaTeX match the Markdown | None |
| The first two campaign runs and the fault of the earlier optimiser | The discarded run is not in the repository; the old code was not run | Diff of the fix read at commit `2d83462` |
| Hardware behaviour, noise, error mitigation, run time | Out of the kit's scope: simulator only | None; see Scope of use |
| Depths above 8, shot counts other than 100, more than 7 qubits, widths other than 4 in the campaign | Not in the campaign | Width and qubit sensitivity of the bias only (M3) |
| Root cause inside Qiskit's `StatePreparation` | I measured the error and its conditioning, not the library internals | B1 option B removes the dependency |

My 2,000-draw study covers 150 scenarios at n = 5 with a grid-and-interpolation optimiser. I checked it against a refined optimiser on 5 scenarios (largest difference 6e-7 on θ).
