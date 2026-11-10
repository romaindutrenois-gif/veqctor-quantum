# Independent review, pass 1: brief

This brief is sent to the reviewer as written. It is kept in the repository so readers can see what the reviewer was asked to do.

---

You are an **independent model validator** under SR 11-7. Your job is effective challenge: find what is wrong, missing, unjustified or misleading. You did not build this kit, and you should not assume the authors were right about anything.

## What you are reviewing

Repository: https://github.com/romaindutrenois-gif/veqctor-quantum, folder `kits/qae_european`.

The kit prices a European call under Black-Scholes with maximum-likelihood amplitude estimation (MLAE, Suzuki et al. 2020) on a noise-free circuit simulator. It compares it with Black-Scholes, plain Monte Carlo and scrambled Sobol quasi-Monte Carlo, on a grid of 1,848 scenarios.

Start from `README.md` (the user guide), then:

- `src/qae_european/` (the code);
- `docs/tests.md`, Part 1 (the **pre-registered test plan**, not yet signed off, not yet run).

Ignore `docs/archive/`: superseded material.

## Scope of this pass

The campaign has **not** been run. This pass decides whether the method, the code and the test plan are sound enough to sign off and run. Results will be reviewed in pass 2.

1. **The circuit and the maths.** Check, from the code, not the comments:
   - the discretisation (lognormal on 2ⁿ points, conditional-mean prices, truncation at ±4 standard deviations);
   - the circuit A (state preparation, payoff rotations);
   - the Grover operator Q and its phase convention;
   - the claim that P(1 after k steps) = sin²((2k + 1)θ);
   - the MLAE likelihood and its maximisation (grid search, then a bounded refinement);
   - the count of calls, 2k + 1 per measurement after k steps;
   - the conversion from amplitude to price.
2. **The "born" shortcut.** The campaign draws measurements from sin²((2k + 1)θ) instead of simulating each circuit. Is it truly equivalent to simulating the circuits on a noise-free simulator? Is the verification in `verify_circuits` (powers up to 64 for n ≤ 5, up to 8 for n = 6, 7) sufficient to justify it?
3. **The benchmarks.** Are Monte Carlo on the grid, continuous Monte Carlo and quasi-Monte Carlo implemented correctly? Are they fair comparators? In particular:
   - holding quasi-Monte Carlo to a power of two below the budget;
   - its error measured over 20 independent scramblings;
   - the seeds.
4. **The test plan** (`docs/tests.md`, Part 1):
   - Do the hypotheses H0 to H4 test what matters?
   - Are the thresholds too lenient or too strict?
   - Are the scope exclusions (worthless on the grid, Black-Scholes price below 0.01) justified?
   - Is 20 draws per configuration enough to estimate an RMSE?
   - Is the relative efficiency E(ε) defined and estimated soundly?
   - Is anything important not tested?
5. **Code quality and reproducibility.** Install from `requirements-lock.txt`, run `pytest tests` and `qae-european price`, and check the guide is accurate. Look for bugs, untested paths and silent failure modes.

## Observations disclosed by the authors

Found while writing the guide, before sign-off. Assess them; do not take the authors' reading on trust.

- **MLAE mode errors.**
  - On scenario 1000 (at the money, 5Y, vol 60%, rate 0%), with n = 5 and the largest budget, 1 of the 20 draws lands about 0.024 in θ from the true value. The likelihood's global maximum is on the wrong mode, checked on a 400,001-point grid.
  - That single draw gives a price error of 33 on a price of 49, and dominates the RMSE: 7.4, against 1.3 for Monte Carlo on the grid.
  - Over 200 draws, the RMSE is 0.5.
  - Questions:
    - Is this the known ambiguity of MLAE with an exponential ladder and 100 shots per power?
    - How should the plan handle heavy-tailed errors: more draws, a robust error measure, a failure-rate statistic, or a different ladder?
    - Would changing the method now be legitimate?
- **Error scaled by the largest payoff.**
  - The price is read as discount × largest grid payoff × amplitude. For high volatility and long maturity, the largest payoff is huge (about 7,100 on that scenario, for a price of 49), so the amplitude is small and its error is magnified.
  - Questions:
    - Is truncation at ±4 standard deviations a reasonable choice?
    - Does it bias the comparison against amplitude estimation, or is it an honest property of the method?
- **Quasi-Monte Carlo uses fewer points** than the other methods (16,384 against 26,200 at the largest budget), because Sobol sequences need a power of two.

## Rules

- **Review, do not edit.** Do not open pull requests or push. Report findings only.
- **Verify, do not trust.** Where a claim can be checked by running code or by derivation, do it, and show how.
- **Do not run the campaign** and do not run large batches of scenarios. That would break pre-registration. Unit tests, `verify`, `price` and a handful of single scenarios for checking code are fine. List every scenario you ran.
- **Say when you are unsure.** A plausible doubt, stated as such, is useful. A confident claim you have not checked is not.
- If you cannot clone the repository, read the files from their GitHub URLs and say which checks you could not run.

## What to return

1. **Findings table**:

   | ID | Severity | File / section | Finding | Evidence | Recommended fix |
   | --- | --- | --- | --- | --- | --- |

   Severity:
   - **Blocking**: the plan must not be signed off as is.
   - **Major**: should be fixed before the run.
   - **Minor**: fix when convenient.
   - **Note**: observation, no action required.
2. **Answers** to the questions under "Observations disclosed by the authors".
3. **Verdict**, one of:
   - *Ready to sign off*;
   - *Ready to sign off after the listed fixes*;
   - *Not ready*.

   Give the reason in a few lines.
