# Response to the independent review

**Review:** independent validation of `kits/qae_european` at commit `3a4193c` (version 1.0.0), 10 November 2026, by an AI reviewer working in a separate project, with no access to the build. The reviewer could not execute the repository's code in its environment. It validated by **independent replication**: its own implementation of the grid, the circuit, the estimator and the benchmarks, written from the documents and compared with the published results. Both the report (`validation-report-2026-11-10.md`) and the scorecard it contains refer to that commit, before corrections.

**This document:** what the developer did about each finding, and where. Status: *Done* (corrected and checked), *Done, differently* (the finding is addressed by another route, explained), or *Open* (left to the sign-off).

Where the review gave figures, the developer re-measured them with the kit's own code before acting. The figures in the documents are the developer's, produced by the scripts named.

| ID | Severity | Finding (short) | Action | Where | Status |
| --- | --- | --- | --- | --- | --- |
| B1 | Blocking | H0-a fails as pre-registered; cause is Qiskit's `StatePreparation` | Option B taken. `StatePreparation` replaced by an explicit loader (binary tree of controlled RY rotations); campaign re-run; H0-a tested against its **original** 1e-9 criterion; the post hoc relative restatement withdrawn | `quantum.py` (`load_distribution`); Document 1, section 4; Document 3, sections 1.9, 2.3, 2.4 | RESULT_B1 |
| M1 | Major | Mode-error measure misses most large errors | Two measures added to every campaign row: RMS error on θ over the Cramér-Rao bound, and the share of draws beyond 4 Cramér-Rao standard deviations. Section 2.9 and the limitation in Document 1 rewritten with them | `campaign.py`; Document 1, section 6; Document 3, sections 1.5, 2.9 | Done |
| M2 | Major | The reasons given for H2-a are untested; noise is not the cause | Tested: H2-a by amplitude, on the median absolute error, and a 2,000-draw rerun of 150 scenarios. The untested reasons removed | `docs/h2a_draws.py`; Document 3, section 2.6 | Done |
| M3 | Major | Truncation bias floor not documented | Floor measured, its forward formula given, the width trade-off quantified, the wrong sentences corrected | `docs/truncation.py`; Document 1, sections 3, 11; user guide, section 2; Document 3, section 2.7 | Done |
| M4 | Major | Limits stated by maturity, a proxy; the drivers are a and s = σ√T | a and s stored per row; H1, H2-a and H3 reported by both; limits restated in a and s, maturity kept as illustration | `campaign.py`, `analyse.py`; Document 3, sections 2.5 to 2.7, 2.10, 2.11; user guide, section 8 | Done |
| M5 | Major | The repository requires a resource estimate at a useful accuracy; the kit gives none | Estimate added for two scenarios (calls, ladder, largest Grover power, CNOTs at 1%, 0.1%, 0.01% statistical accuracy), with published fault-tolerant figures; `fit_power_law` now used; README section 9 added from the review's wording | `resources.py`, `docs/resource_estimate.py`; Document 1, section 12; user guide, section 9; repository README | Done |
| m1 | Minor | Two statements on the cause of H0-a do not hold | Rewritten from a direct test: loader alone, then rotations given the loaded state, for both loaders, plus the conditioning test | `docs/checks.py`; Document 3, section 2.4 | Done |
| m2 | Minor | "Bit-for-bit reproducible" unsafe for `circuit_price` at n ≥ 6 | Qualified; the explicit loader is well conditioned (measured) | Document 1, section 10 | Done |
| m3 | Minor | Sobol scrambling misnamed; unbounded integrand omitted | Corrected (linear matrix scramble with digital shift); tail caveat added with the measured slopes | Document 2, section 3.4; `quasi_monte_carlo.py` docstring | Done |
| m4 | Minor | Test count stale | Updated (41 cases after the additions) | User guide, section 1 | Done |
| m5 | Minor | Input-validation gaps | `Ladder` validated; `width` must be finite; at most 10 price qubits for the circuit; negative payoffs rejected; section 9 aligned; tests added | `estimation.py`, `grid.py`, `quantum.py`; Document 1, section 9; tests | Done |
| m6 | Minor | Repository README layout and Qiskit version out of date | Updated | Repository README | Done |
| m7 | Minor | `qae_mean` not described | Described, with the new columns | `campaign.py` header; Document 3, section 1.5 | Done |
| m8 | Minor | "Identifiable region" undefined, so *with limits* is post hoc | Rule proposed for the next campaign (named variable, fixed cut-offs, pass in every cell). For this campaign, verdicts with limits are labelled post hoc | Document 3, sections 2.6, 2.12 | Done for the next campaign; this campaign's limits remain post hoc |
| n1 | Note | H2-a also fails at other numbers of qubits | Reported for every n | Document 3, section 2.6 | Done |
| n2 | Note | Pre-registration rests on unsigned commit dates | Noted as a limitation; future plans to be frozen with an annotated tag and an external timestamp | Document 3, section 1.9 | Open (process) |
| n3 | Note | Relative efficiencies are extrapolated | "Indicative" kept wherever they are quoted | Document 3, sections 2.8, 2.10; user guide | Done |
| n4 | Note | Compiled depths can vary slightly between builds | Stated | Document 1, section 8 | Done |

**Not checked by the review, and still not checked by anyone other than the developer:** the kit's own code run end to end (tests, `verify`, `campaign`, analysis scripts and exports). The reviewer's environment blocked it. The internal review (a separate session working from a fresh clone) did run it, on the second campaign run.

**Left to the sign-off:**
1. The developer's reading of the limits rule (Document 3, section 2.6), now stated in a and s.
2. Whether H2-a calls for a follow-up campaign with a different ladder or shot allocation (the review's suggestion; Document 3, section 2.12).
