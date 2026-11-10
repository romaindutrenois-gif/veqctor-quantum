# Document 3: Tests

**Kit:** qae_european 1.0.0 · **Status of this document:** Part 1 (test plan) frozen by its commit before the campaign (422ebfb); Part 2 (results) written after the campaign. Sign-off of the whole kit by Romain Dutrenois at the end, after an independent review.

Part 1 is pre-registered: it is written and committed **before** the campaign runs, and the commit date is the proof. Any change made after that commit is recorded in the deviations table (section 1.9), with its reason.

---

## Part 1: Test plan

### 1.1 What we want to test, and why

The kit prices a European call with **maximum-likelihood amplitude estimation** (MLAE) on a quantum circuit simulator. The claim to test is the theoretical promise of amplitude estimation: **it needs fewer samples than Monte Carlo to reach the same accuracy**, quadratically fewer in the limit.

**Measure of performance: relative efficiency in number of calls.** Performance is measured by the error reached for a given number of calls (sample complexity, or *query complexity* for amplitude estimation, where a call is a query to the circuit A). Two methods are compared through their **relative efficiency** at a given RMSE ε:

  E(ε) = N_comparator(ε) / N_QAE(ε)

where N(ε) is the number of calls a method needs to reach RMSE ε. E > 1 means amplitude estimation needs fewer calls than the comparator; E < 1 means it needs more. Calls are counted as follows:

- For amplitude estimation, a call is one application of the circuit A. One Grover step contains A and its inverse, so a measurement after k Grover steps counts as 2k + 1 calls.
- For Monte Carlo, a call is one simulated path, i.e. one payoff evaluation.
- For quasi-Monte Carlo, a call is one point of the Sobol sequence.

**Out of scope:**
- **Speed (wall-clock time).** The campaign runs on a classical simulator, which is far slower than Monte Carlo. No current quantum machine can run the deeper circuits usefully. Speed is discussed only as a projection from published resource estimates, labelled as such.
- **Hardware noise.** The simulator is noise-free. No run on a real machine in this campaign.

**Accuracy is decomposed.** The circuit prices the option on a grid of 2ⁿ points, not on the continuous distribution. Its error against Black-Scholes therefore has two parts, measured separately:

- **discretisation bias** = grid price − Black-Scholes price (deterministic, depends on n);
- **statistical error** = estimate − grid price (random, depends on the number of calls).

### 1.2 Hypotheses

| # | Hypothesis | Type |
| --- | --- | --- |
| H0 | The circuit computes the grid price exactly, and the identity used to accelerate the campaign holds. | Prerequisite |
| H1 | At equal calls, the RMSE of amplitude estimation is below that of plain Monte Carlo sampling the same grid, i.e. a relative efficiency E > 1. | Relative efficiency against plain Monte Carlo |
| H2 | The query complexity of amplitude estimation is O(1/ε), against O(1/ε²) for plain Monte Carlo: its statistical error falls like 1/N, against 1/√N. | Query complexity (convergence rate) |
| H3 | With 7 price qubits and the largest budget, the total error against Black-Scholes is within tolerance. | Accuracy against the reference |
| H4 | Against quasi-Monte Carlo, the best classical sampling method for this one-dimensional problem, no relative efficiency above 1 is expected. | Descriptive: measured, no pass/fail |

H4 is stated in advance as an expected **absence** of gain (E ≤ 1). Quasi-Monte Carlo converges close to 1/N on smooth one-dimensional problems, the same rate as amplitude estimation.

### 1.3 Methods compared

| Method | Target | Role |
| --- | --- | --- |
| Black-Scholes closed form | Continuous price | Reference ("truth") |
| Exact circuit probability | Grid price | Checks the circuit (H0) |
| Amplitude estimation (MLAE) | Grid price | Method under test |
| Plain Monte Carlo on the grid | Grid price | Like-for-like comparator for H1, H2 |
| Plain Monte Carlo, continuous | Continuous price | What a desk would see with plain sampling |
| Quasi-Monte Carlo (scrambled Sobol), continuous | Continuous price | Best classical sampling method (H4) |

Methods and code are described in Document 2 (Benchmarks).

### 1.4 Scenario grid

Spot fixed at 100. All combinations of:

| Dimension | Values | Count |
| --- | --- | --- |
| Moneyness K / S₀ | 0.75 to 1.25, step 0.05 | 11 |
| Maturity | 1W, 2W, 1M, 3M, 6M, 1Y, 3Y, 5Y | 8 |
| Volatility | 20% to 80%, step 10% | 7 |
| Rate | −1%, 0%, +1% | 3 |

That is **1,848 scenarios**. Each is crossed with:

- **price qubits** n = 3, 4, 5, 6, 7 (grids of 8 to 128 points);
- **5 budgets**: MLAE ladders of depth 4 to 8, i.e. Grover powers (0, 1, 2, 4, …, 2^(depth−2)), 100 measurements per power. That gives 1,800, 3,500, 6,800, 13,300 and 26,200 calls. Monte Carlo methods get the same number of calls; quasi-Monte Carlo uses the largest power of two not above it;
- **50 independent draws** of every random method.

In total: 1,848 × 5 × 5 = 46,200 configurations, about 9.2 million priced estimates. *[Erratum, see 1.9: 2.31 million amplitude-estimation estimates, about 5.5 million in all.]*

### 1.5 Measured quantities

For each scenario, number of qubits n and budget N, the campaign stores:

- the Black-Scholes price, the grid price and the exact circuit price;
- for each random method, the **root-mean-square error (RMSE)** over the 50 draws, against its own target (grid price or Black-Scholes, as in 1.3), and the RMSE of amplitude estimation against Black-Scholes;
- for amplitude estimation and Monte Carlo on the grid, the **median absolute error** against the grid price, which is not driven by a few large errors;
- for amplitude estimation, the **share of mode errors**: draws where the estimated θ is further than π / (2 m_max) from the true θ, with m_max = 2 k_max + 1 the multiplier of the highest Grover power. That is half the period of the most informative measurement, so such a draw has locked onto a wrong peak of the likelihood;
- the number of calls actually used;
- the mean amplitude-estimation price over the draws (`qae_mean`).

*Added after the independent review (section 1.9), descriptive only, no criterion attached:*
- the exact amplitude a and the log standard deviation s = σ√T of the scenario;
- the RMS error on θ divided by the Cramér-Rao bound 1 / (2 √(shots × Σ_k (2k + 1)²)), about 1 for an efficient estimator;
- the share of draws with |θ̂ − θ| beyond 4 Cramér-Rao standard deviations. This catches large errors that stay within one lobe of the likelihood, which the mode-error count misses.

Seeds are derived from a fixed master seed (20261103) and the indices of scenario, qubits, budget and method, so any row can be recomputed on its own.

### 1.6 Scope rules: decided before the run

- **Out-of-grid scenarios.** When every grid point is out of the money, the circuit price is exactly 0 and there is nothing to estimate. These are counted and reported, and excluded from H1 to H4.
- **Negligible prices.** Scenarios with a Black-Scholes price below 0.01 (one cent on a spot of 100) are reported separately and excluded from H1 to H4. Relative errors are meaningless there.
- **Everything else is in scope.** No scenario is excluded after the results are seen.

### 1.7 Acceptance criteria

| # | Criterion | Pass if |
| --- | --- | --- |
| H0-a | Circuit price against grid price, every scenario and every n | Absolute difference ≤ 1e-9 in **100%** of cases |
| H0-b | Full statevector simulation of A Qᵏ against sin²((2k + 1)θ), on 20 randomly drawn scenarios (powers up to 64 for n ≤ 5, up to 8 for n = 6, 7) | Absolute difference ≤ 1e-9 in **100%** of checks |
| H1 | At the largest budget (26,200 calls), RMSE of amplitude estimation < RMSE of Monte Carlo on the same grid | In **≥ 95%** of in-scope (scenario, n) pairs |
| H2-a | Fitted slope of log RMSE against log N over the 5 budgets, amplitude estimation, n = 5 | Slope ≤ −0.8 in **≥ 90%** of in-scope scenarios |
| H2-b | Same fit for Monte Carlo on the grid (checks the benchmark) | Slope between −0.65 and −0.35 in **≥ 90%** of in-scope scenarios |
| H3 | n = 7, largest budget: RMSE of amplitude estimation against Black-Scholes ≤ max(1% of the Black-Scholes price, 0.01) | In **≥ 95%** of in-scope scenarios |
| H4 | Ratio of RMSE against Black-Scholes, amplitude estimation (n = 7) over quasi-Monte Carlo, at each budget | Descriptive: distribution reported, no pass/fail |

**Verdict per hypothesis:** *Validated* if the criterion passes; *Not validated* otherwise. If a criterion fails only in an identifiable region of the grid (for example very short maturities), the verdict is *Validated with limits*, naming that region. Failure of H0 stops the campaign: nothing else is interpreted.

### 1.8 Reported analyses (in addition to the criteria)

- **Relative efficiency E at the largest budget**, per in-scope scenario, against Monte Carlo on the grid (n = 5 and n = 7) and against quasi-Monte Carlo (n = 7): median, first and third quartiles. E is estimated from the fitted error curves: E = N_comparator(ε) / N_QAE(ε), with ε the RMSE of amplitude estimation at its largest budget, and N_comparator(ε) read from the comparator's fitted log RMSE against log N (extrapolated beyond 26,200 calls where needed, flagged as such).
- Errors by dimension: moneyness, maturity, volatility, rate and number of qubits, to find where amplitude estimation works best and worst.
- The crossing budget N\*: the smallest budget where amplitude estimation beats Monte Carlo on the grid, for each scenario.
- Discretisation bias against Black-Scholes, as a function of n and of the scenario.
- The hard cases: deep out-of-the-money options (small amplitude), very short maturities, high volatility.
- Counts of out-of-grid and negligible-price scenarios.
- **Mode errors of amplitude estimation**: their share by scenario, number of qubits and budget, and where they concentrate. H1 is also reported on the median absolute error, as a sensitivity check. The criterion itself stays on the RMSE.

### 1.9 Deviations from the plan

| Date | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 2026-11-10 | **Corrections after the independent review (third run of the campaign).** (1) Qiskit's generic `StatePreparation` replaced by an explicit loader (a binary tree of controlled RY rotations, Document 1, section 4), which loads the grid probabilities to rounding error. H0-a is then tested against its **original** criterion (absolute 1e-9), unchanged; the post hoc relative restatement proposed after the second run is withdrawn. (2) New stored measures, descriptive only: the exact amplitude a and s = σ√T per row; the RMS error on θ relative to the Cramér-Rao bound; the share of draws beyond 4 Cramér-Rao standard deviations. (3) Input validation tightened (ladder, grid width, at most 10 price qubits, negative payoffs rejected). Criteria and thresholds unchanged. The second run's results stay in the repository history (commit 3a4193c). | Findings B1, M1, M4 and m5 of the independent review (`docs/review/`) | Developer (Veqctor) |
| 2026-11-10 | **Corrections after an internal review, and the campaign re-run.** A review in a separate session, working from a fresh clone, found that the MLAE maximisation refined only the best grid point, so with two nearly tied likelihood peaks it could return the lower one (1 draw in 2.31 million in the first campaign; frequent at depths above 8). Corrected: denser grid for deep ladders, and refinement of the 5 highest grid peaks (Document 1, section 6). Because the code that produced the results changed, **the whole campaign was re-run** on the corrected code (commit 2d83462). At the same time, and before the re-run: H0-b was extended with the full ladder (powers up to 64) at n = 6 and 7 on one scenario; the campaign resume refuses incomplete scenarios; `run_info.json` became a log of every run; `docs/analyse.py` and `docs/checks.py` were extended so every number in Part 2 is computed by a script. Criteria unchanged. The first campaign's results stay in the repository history (commit 373e6a1). | Optimiser error and traceability gaps found in review | Developer (Veqctor) |
| 2026-11-10 | **Note on the pre-registration evidence** (independent review, n2). The freeze rests on the commit date of 422ebfb, which is not signed. The freeze, the three campaign runs and the corrections all took place on the same day. Part 1 can be compared with that commit to check that its criteria and thresholds are unchanged, and the independent review did so. Future plans will be frozen with an annotated tag and an external timestamp. | Limitation of the evidence | Developer (Veqctor) |
| 2026-11-10 | **Erratum to 1.4.** "About 9.2 million priced estimates" counted continuous Monte Carlo and quasi-Monte Carlo once per number of qubits. They are computed once per scenario and budget: 2.31 million amplitude-estimation estimates, about 5.5 million in all. | Counting error in the plan text | Developer (Veqctor) |
| 2026-11-10 | **Proposed, not applied: H0-a restated as a relative tolerance**, \|circuit − grid\| ≤ 1e-8 × grid price. Post hoc: made after seeing that H0-a fails as written (Part 2, section 2.4). | The absolute tolerance of 1e-9 did not allow for the floating-point error of Qiskit's state-preparation synthesis at 6 and 7 qubits (relative error up to 3.4e-9) | Pending: independent review and sign-off |
| 2026-11-10 | **First campaign run discarded, unread.** It ran on a stale installed copy of the package (20 draws, without the measures added above). Detected when the analysis script stopped on the missing columns, before computing any statistic. The run was moved aside without being analysed; the package was reinstalled in editable mode; the analysis script (`docs/analyse.py`) was committed before the rerun; each run now writes `results/run_info.json` (git commit, draws, versions) next to its results. | Execution error, recorded for transparency | Developer (Veqctor) |
| 2026-11-10 | **Draws raised from 20 to 50; median absolute error and share of mode errors added to the stored measures (1.5) and reported analyses (1.8).** Criteria unchanged. | While writing the user guide, one scenario was recomputed (scenario 1000: at the money, 5Y, vol 60%, rate 0%; n = 5, largest budget). One of its 20 draws had locked onto a wrong peak of the likelihood (θ off by about π/129), giving a price error of 33 on a price of 49; the RMSE over 20 draws was 7.4, against 0.5 over 200 draws. This is a known property of maximum-likelihood amplitude estimation: errors are mostly small, with rare large ones. With 20 draws the RMSE would depend on whether such a draw is in the sample. The method itself is left unchanged (the published one); the measurement is made more stable and the rare errors are counted rather than hidden. No other scenario was inspected. | Developer (Veqctor) |
| 2026-11-03 | Terminology: "superiority" replaced by **relative efficiency** and **query complexity** (sections 1.1, 1.2), and the distribution of E added to the reported analyses (1.8). Criteria and thresholds unchanged. Made before any run. | Standard statistical terms, measurable per scenario | Romain Dutrenois |
| 2026-11-03 | Before this campaign, in the exploratory version of the kit, the amplitude-estimation tolerance was tightened from 2% to 1% after a first run, and the budget increased. This plan replaces those exploratory tests; its criteria are set without reference to them. | Recorded for transparency | — |

### 1.10 Execution

- **Environment:** Python 3.13, Qiskit 2.6.1, NumPy 2.5.4, SciPy 1.18.1, all versions pinned in `requirements-lock.txt`. CPU: 2-core Intel Xeon at 2.8 GHz, Linux. Details in Document 1.
- **Commands:** `qae-european verify` (H0-b), then `qae-european campaign --processes 2` (resumable). Output: `results/verification.json`, `results/campaign.csv` and `results/run_info.json` (the git commit, parameters and library versions of the run). The analysis against the criteria is `docs/analyse.py`, committed before the run.
- **Acceleration (declared).** In the campaign, amplitude-estimation measurements are drawn from the exact probabilities sin²((2k + 1)θ), with θ taken from the exact statevector of the circuit A for each scenario. On a noise-free simulator, this is mathematically identical to simulating the circuits A Qᵏ. The identity is verified by H0-b.
- **Sizing.** Timing was measured on 3 scenarios, timing only, without inspecting results: about 1.5 s per scenario with 20 draws, so about 25 minutes in total. With 50 draws: about 1 hour on 2 cores.

### 1.11 Sign-off

| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Author | Veqctor (kit generation) | Submitted | 2026-11-03 |
| Internal review | Developer's reviewer (separate session, fresh clone) | Findings corrected (1.9) | 2026-11-10 |
| Independent review | AI reviewer (separate project, no access to the build) | | |
| Sign-off | Romain Dutrenois | | |

---

## Part 2: Results

Every number below is computed by a script in the kit:

- `docs/analyse.py` writes `results/summary.json` from `results/campaign.csv` and `results/verification.json`.
- `docs/checks.py` writes `results/checks.json`: the state-preparation accuracy and the global-maximum check of MLAE.

All of these files are in the repository. Where the text quotes a number, the key in the JSON file is given in brackets.

### 2.1 Execution record

| Item | Value |
| --- | --- |
| Code | commit 2d83462, no uncommitted changes in the package (`results/run_info.json`) |
| Plan | frozen at commit 422ebfb; criteria unchanged since |
| Environment | Python 3.13.17, Qiskit 2.6.1, NumPy 2.5.4, SciPy 1.18.1, Linux, 2 cores |
| Run | 2026-11-10: verification (100 checks), then 1,848 scenarios × 5 qubit counts × 5 budgets × 50 draws, in one call |
| Rows | 46,200 (complete) |
| Wall time | about 12 minutes for the verification and 25 minutes for the campaign, on 2 cores |

**Runs before this one** (section 1.9):

1. **A first run was discarded unread.** It ran on a stale copy of the package.
2. **A second run was complete and published** (commit 373e6a1). An internal review then found the MLAE optimiser could return the lower of two nearly tied peaks. The optimiser was corrected and the campaign re-run. That is this run.

Its results differ from the second run's in a handful of configurations:

| Statistic | Second run | This run |
| --- | --- | --- |
| H1 passes | 8,772 | 8,774 |
| H3 passes | 1,594 | 1,595 |
| Mode-error draws | 45 | 44 |

No verdict changes.

### 2.2 Scope

| Category | Count | Treatment |
| --- | --- | --- |
| Scenarios with a Black-Scholes price below 0.01 | 55 (30 at 1W, 19 at 2W, 6 at 1M) | Excluded from H1 to H4, as planned |
| (scenario, n) pairs worthless on the grid | 147 (42 at n = 3, falling to 24 at n = 7) | Excluded, as planned; all of them are also negligible-price scenarios |
| **In-scope (scenario, n) pairs** | **8,965** | 1,793 scenarios at each n |

### 2.3 Verdicts

| # | Criterion (section 1.7) | Result | Verdict |
| --- | --- | --- | --- |
| H0-a | Circuit price against grid price ≤ 1e-9 in 100% of cases | 89.4% (41,310 of 46,200 rows); largest difference 8.4e-9 | **Not validated** as written; see 2.4 |
| H0-b | Full simulation of A Qᵏ against sin²((2k + 1)θ) ≤ 1e-9 in 100% | 100% (100 of 100); largest difference 6.1e-10 | **Validated** |
| H1 | At 26,200 calls, RMSE of amplitude estimation < Monte Carlo on the grid, ≥ 95% | 97.9% (8,774 of 8,965) | **Validated**, conditional on 2.4 |
| H2-a | Slope ≤ −0.8 for amplitude estimation, n = 5, in ≥ 90% | 89.0% (1,595 of 1,793); median slope −0.98 | **Not validated**, conditional on 2.4; see 2.6 on the limits rule |
| H2-b | Slope between −0.65 and −0.35 for Monte Carlo on the grid, n = 5, in ≥ 90% | 99.8% (1,790 of 1,793); median slope −0.50 | **Validated**, conditional on 2.4 |
| H3 | n = 7, largest budget: RMSE against Black-Scholes ≤ max(1% of the price, 0.01), in ≥ 95% | 89.0% overall; 99.0% for maturities up to 1 year | **Validated with limits** (maturities up to 1 year), conditional on 2.4; see 2.6 on the limits rule |
| H4 | QAE against QMC, descriptive | Median RMSE ratio 18 to 20, at every budget | As expected: no gain over QMC |

**Conditional on 2.4** means: valid only if the restatement of H0-a proposed in 2.4 is accepted. Section 1.7 says that a failure of H0 stops interpretation, so without that restatement, H1 to H4 have no verdict.

### 2.4 H0-a: what failed, and what it means

**The facts** [`H0a`, `H0a_detail`].
- 978 of the 9,240 circuits differ from the grid price by more than 1e-9. All of them have 6 or 7 price qubits: 826 at n = 7 and 152 at n = 6.
- The largest absolute difference is 8.4e-9. The largest **relative** difference, over all circuits, is 3.4e-9.

**The cause: Qiskit's synthesis of the state preparation.**
- On the widest scenario (scenario 1000: at the money, 5Y, 60% volatility), the probabilities loaded by `StatePreparation` differ from the target p_i by at most [`checks.json: state_preparation`]:

  | Price qubits | Largest error on a loaded probability |
  | --- | --- |
  | 5 | 1.3e-13 |
  | 6 | 3.1e-11 |
  | 7 | 6.4e-10 |

  Their sum deviates from 1 by 2.5e-12 at n = 7.
- The payoff rotations and the Grover operator are not involved: H0-b passes. H0-b now includes the full ladder, up to k = 64, at n = 6 and 7.
- That the error accumulates in floating point over the thousands of gates of the synthesised circuit is the natural explanation. It is not proven here.

**Why the criterion failed.** The plan used an *absolute* tolerance of 1e-9, on prices up to a few hundred and circuits of up to 12,000 gates. A relative tolerance would have expressed what was meant: "the circuit computes the grid price up to numerical precision". This is an error in the plan, made before the run.

**The effect on the other results is negligible.** A relative error of 3.4e-9 is about five orders of magnitude below the smallest statistical error in the campaign: the smallest relative RMSE of amplitude estimation is 3.6e-4 [`smallest_relative_rmse_qae`].

**Proposed deviation (post hoc, not applied).** Restate H0-a as |circuit − grid| ≤ 1e-8 × grid price. Under it, H0-a passes in 100% of the 46,200 rows [`H0a_detail.relative_restatement_pass`].
- The proposal is made **after** seeing the results.
- Accepting or rejecting it is for the independent review and the sign-off.

### 2.5 H1: amplitude estimation against Monte Carlo on the same grid

At the largest budget, amplitude estimation has the lower RMSE in **97.9%** of in-scope (scenario, n) pairs. On the median absolute error, the share is 99.98% [`H1_sensitivity_median_abs_error`].

![Share of wins by maturity and volatility, all n](img/h1_heatmap.png)

**Where it loses** [`H1_failures`]: mostly at long maturity and high volatility.
- Of the 191 losses, 106 are at 5Y and 46 at 3Y, and 73 are at 80% volatility.
- Losses grow with n: 14 at n = 3, 63 at n = 7.

**Why.** The price is read as e^(−rT) × largest grid payoff × amplitude (Document 1, section 11). On a wide grid the largest payoff is many times the price, so the amplitude is small and its error is magnified. Monte Carlo on the grid has no such factor. Mode errors are present in 37 of the 191 losses.

**When amplitude estimation gets ahead (n = 5)** [`crossing_budget_n5`, `wins_from_budget_onwards_n5`]:

| Budget (calls) | 1,800 | 3,500 | 6,800 | 13,300 | 26,200 | Never |
| --- | --- | --- | --- | --- | --- | --- |
| First budget where it wins | 764 | 708 | 250 | 55 | 14 | 2 |
| First budget from which it wins at every larger budget | 657 | 637 | 297 | 119 | 50 | 33 |

- 82% of scenarios have a first win by 3,500 calls.
- 72% win at every budget from 3,500 onwards.

### 2.6 H2: convergence rate

![Error against calls, n = 5](img/error_vs_calls.png)

![Distribution of the fitted slopes, n = 5](img/slopes.png)

**Monte Carlo on the grid (H2-b) behaves as theory predicts.** The median slope is −0.50, with quartiles −0.53 and −0.47, and 99.8% of scenarios fall in the band. This confirms both the benchmark and the fitting procedure.

**Amplitude estimation (H2-a) shows the 1/N rate in the bulk of scenarios.** The median slope is −0.98, with quartiles −1.04 and −0.90. But 11.0% of scenarios have a slope above −0.8, against the 10% the criterion allows.

**The limits rule, applied to H2-a and H3 alike.** Section 1.7 allows *Validated with limits* "if a criterion fails only in an identifiable region of the grid". The plan does not define "identifiable region", so any region is chosen after seeing the results. Both hypotheses are reported the same way [`H2a_by_maturity`, `H3_by_maturity`]:

| | Pass rate, maturities 1W to 1Y | Pass rate at 3Y | Pass rate at 5Y | Restricted to maturities up to 1Y |
| --- | --- | --- | --- | --- |
| H2-a (needs 90%) | 88% to 93% | 84% | 81% | 91.2%: passes |
| H3 (needs 95%) | 98% to 100% | 70% | 50% | 99.0%: passes |

- **H3 failures are concentrated:** 185 of the 198 failures are at 3Y and 5Y, and every maturity up to 1Y passes on its own.
- **H2-a failures are spread out:** they appear at every maturity and every volatility. Pass rates by volatility run from 85% to 91%, and two maturities within the "up to 1Y" region fail on their own (3M at 88.3%, 1Y at 89.6%). Restricting to maturities up to 1Y lifts H2-a just above 90% by averaging, not by removing the failures.

**The developer's reading:**
- H3 is *Validated with limits* (maturities up to 1 year);
- H2-a is *Not validated*.

This reading treats "only in an identifiable region" as requiring the criterion to hold for each maturity inside the region. That condition is not in the plan, so the reading is a judgement. It is left to the review and the sign-off.

**Likely reasons for the H2-a dispersion (not tested):**
- **Noise in each slope.** Each slope is fitted on 5 RMSEs, each estimated from 50 draws, so each RMSE carries a relative standard error of about 10%. Over this range of budgets, that moves the slope by several hundredths.
- **The low budgets are not asymptotic.** At depth 4 (powers 0, 1 and 2 only), MLAE is not yet in its asymptotic regime, so the fitted slope mixes two regimes.
- **Follow-ups.** A longer ladder or more draws would sharpen the estimate. Neither was planned.

### 2.7 H3: accuracy against Black-Scholes, n = 7

Against Black-Scholes, the RMSE is within max(1% of the price, 0.01) in 89.0% of scenarios overall, and in **99.0%** of the 1,331 scenarios with maturity up to 1 year [`H3`, `H3_up_to_1Y`]. Failures grow with volatility: 70 of them are at 80% [`H3_failures`].

**Two causes:**
- **Discretisation bias, in 67 of the 198 failures.** There, the bias alone exceeds the tolerance: no amount of sampling can bring those scenarios within 1% with 128 grid points.
- **The payoff scaling described in 2.5,** in the rest.

![Discretisation bias against the number of price qubits](img/discretisation_bias.png)

The median relative discretisation bias falls from 2.9% at n = 3 to 0.11% at n = 7 [`discretisation_bias_rel`].

### 2.8 H4 and relative efficiency

**Against quasi-Monte Carlo** (n = 7, both against Black-Scholes), amplitude estimation's RMSE is a median **18 to 20 times larger**, at every budget [`H4_ratio_qae_over_qmc`]. Amplitude estimation has the lower RMSE in only 4 to 9 of the 1,793 scenarios, depending on the budget [`H4_qae_wins`].
- The ratio is roughly constant across budgets, so both methods converge at about the same rate, as stated in advance.
- The constant favours quasi-Monte Carlo, because amplitude estimation carries the discretisation bias and the payoff scaling, and quasi-Monte Carlo carries neither.

![RMSE ratio, amplitude estimation over quasi-Monte Carlo](img/qae_vs_qmc.png)

**Relative efficiency at the largest budget**, E = N_comparator(ε) / N_QAE(ε) [`relative_efficiency_largest_budget`]:

| Comparison | Median E | Quartiles | E > 1 | Comparator's N(ε) outside the budgets run |
| --- | --- | --- | --- | --- |
| vs Monte Carlo on the grid, n = 5 | 11.2 | 6.7 – 18.1 | 1,759 of 1,793 | above 26,200 calls in 1,759; below 1,800 in 2 |
| vs Monte Carlo on the grid, n = 7 | 10.4 | 6.0 – 17.3 | 1,732 of 1,793 | above 26,200 calls in 1,732 |
| vs quasi-Monte Carlo, n = 7 | 0.028 | 0.014 – 0.050 | 2 of 1,793 | below 1,024 points in 1,155; above in 3 |

At the largest budget, plain Monte Carlo would need about **11 times more calls** than amplitude estimation to reach the same error on the grid. Quasi-Monte Carlo would need about **36 times fewer**.

Both figures come from extrapolating each comparator's fitted line outside the budgets actually run, in almost every scenario. They are indicative, not measured.

### 2.9 Mode errors of MLAE

**Mode errors are rare** [`mode_errors`]:

| | Depths 4 to 6 | Depth 7 | Depth 8 |
| --- | --- | --- | --- |
| Share of draws affected | 0% | 0.0007% | 0.009% |
| Configurations with at least one | 0 of 8,965 | 3 | 40 |

The 0% at depths 4 to 6 is partly a consequence of the definition: the threshold is wider for short ladders (Document 1, section 6).

**They come from the method, not the optimiser.** For all 43 configurations with a mode error, the draws were regenerated from their seeds and compared with a 400,001-point grid. The estimator agrees with the fine grid in all 2,150 draws [`checks.json: mlae_global_maximum`].

**A single one can still dominate an RMSE.** Mode errors are present in 37 of the 191 H1 losses. The scenario that revealed them (section 1.9) is among the 40 at depth 8.

### 2.10 Conclusions

These conclusions hold **if the restatement of H0-a in 2.4 is accepted**. Without it, the plan gives no verdict on H1 to H4.

1. **The circuit does what it claims, up to numerical precision.**
   - It reproduces the grid price to a relative 3.4e-9.
   - The Grover identity behind the fast simulation holds to 6.1e-10, up to the largest power used.
   - H0-a failed as written because its absolute tolerance was too tight for 7-qubit synthesis, not because of an error in the circuit.
2. **Amplitude estimation beats plain Monte Carlo at equal calls on the same grid, at the budgets tested.** It does so in 97.9% of cases at 26,200 calls. This is the advantage measured. The quadratic rate behind the textbook claim is seen in the bulk (median slope −0.98) but **not certified** at the planned threshold (conclusion 3). The figure of 11 times fewer calls is extrapolated.
3. **The 1/N rate is not certified scenario by scenario.** 11% of scenarios have a fitted slope above −0.8, against 10% allowed, and they are not confined to one region.
4. **Against Black-Scholes, the kit is accurate to 1% for maturities up to 1 year** with 7 price qubits. Beyond that, both the discretisation and the payoff scaling degrade it.
5. **There is no gain over the best classical sampler.** Quasi-Monte Carlo is about 20 times more accurate at the same budget on this one-dimensional problem. That was expected, and it is why a European call is a test bench, not a use case.

### 2.11 Overall verdict (developer)

The stated purpose is a reproducible, documented test bench for amplitude estimation on the simplest option. **For that purpose, the kit is fit, with limits, conditional on accepting the restatement of H0-a.**

| Point | Status |
| --- | --- |
| Correctness of the circuit and the simulation | Established up to numerical precision; the restatement of H0-a is needed for the plan's criterion to pass |
| Fewer calls than plain Monte Carlo on the same grid, at the budgets tested | Established (H1), conditional on H0-a |
| The 1/N rate, scenario by scenario at the planned threshold | Not established (H2-a) |
| Accuracy against Black-Scholes | Up to 1 year only (H3), conditional on H0-a |
| Advantage over quasi-Monte Carlo | None, as expected |

**For the independent review and the sign-off to decide:**
1. Accept or reject the restatement of H0-a.
2. Accept or reject the developer's reading of the limits rule for H2-a and H3.
3. Decide whether H2-a calls for a follow-up campaign: a longer ladder, more draws, or both.
