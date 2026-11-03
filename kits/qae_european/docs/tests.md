# Document 3: Tests

**Kit:** qae_european 1.0.0 · **Status of this document:** Part 1 (test plan) submitted for sign-off; Part 2 (results) to be written after the campaign.

Part 1 is pre-registered: it is written, approved and committed **before** the campaign runs. Any change made after approval is recorded in the deviations table (section 1.9), with its reason.

---

## Part 1: Test plan

### 1.1 What we want to test, and why

The kit prices a European call with **maximum-likelihood amplitude estimation** (MLAE) on a quantum circuit simulator. The claim to test is the theoretical promise of amplitude estimation: **it needs fewer samples than Monte Carlo to reach the same accuracy**, quadratically fewer in the limit.

**What "superiority" means in this campaign.** Superiority is measured as **sample complexity**: the error reached for a given number of calls.

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
| H1 | For the same number of calls, amplitude estimation has a smaller statistical error than plain Monte Carlo sampling the same grid. | Superiority over plain Monte Carlo |
| H2 | The statistical error of amplitude estimation falls like 1/N, against 1/√N for plain Monte Carlo. | Convergence rate |
| H3 | With 7 price qubits and the largest budget, the total error against Black-Scholes is within tolerance. | Accuracy against the reference |
| H4 | Against quasi-Monte Carlo, the best classical sampling method for this one-dimensional problem, amplitude estimation shows no superiority. | Descriptive: measured, no pass/fail |

H4 is stated in advance as an expected **absence** of superiority. Quasi-Monte Carlo converges close to 1/N on smooth one-dimensional problems, the same rate as amplitude estimation.

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
- **20 independent draws** of every random method.

In total: 1,848 × 5 × 5 = 46,200 configurations, about 3.7 million priced estimates.

### 1.5 Measured quantities

For each scenario, number of qubits n and budget N, the campaign stores:

- the Black-Scholes price, the grid price and the exact circuit price;
- for each random method, the **root-mean-square error (RMSE)** over the 20 draws, against its own target (grid price or Black-Scholes, as in 1.3), and the RMSE of amplitude estimation against Black-Scholes;
- the number of calls actually used.

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

- Errors by dimension: moneyness, maturity, volatility, rate and number of qubits, to find where amplitude estimation works best and worst.
- The crossing budget N\*: the smallest budget where amplitude estimation beats Monte Carlo on the grid, for each scenario.
- Discretisation bias against Black-Scholes, as a function of n and of the scenario.
- The hard cases: deep out-of-the-money options (small amplitude), very short maturities, high volatility.
- Counts of out-of-grid and negligible-price scenarios.

### 1.9 Deviations from the plan

| Date | Deviation | Reason | Approved by |
| --- | --- | --- | --- |
| 2026-11-03 | Before this campaign, in the exploratory version of the kit, the amplitude-estimation tolerance was tightened from 2% to 1% after a first run, and the budget increased. This plan replaces those exploratory tests; its criteria are set without reference to them. | Recorded for transparency | — |

### 1.10 Execution

- **Environment:** Python 3.13, Qiskit 2.6.1, NumPy 2.5.4, SciPy 1.18.1, all versions pinned in `requirements-lock.txt`. CPU: 2-core Intel Xeon at 2.8 GHz, Linux. Details in Document 1.
- **Commands:** `qae-european verify` (H0-b), then `qae-european campaign --processes 2` (resumable). Output: `results/verification.json` and `results/campaign.csv`.
- **Acceleration (declared).** In the campaign, amplitude-estimation measurements are drawn from the exact probabilities sin²((2k + 1)θ), with θ taken from the exact statevector of the circuit A for each scenario. On a noise-free simulator, this is mathematically identical to simulating the circuits A Qᵏ. The identity is verified by H0-b.
- **Sizing.** Timing was measured on 3 scenarios, timing only, without inspecting results: about 1.5 s per scenario, so about 25 minutes in total.

### 1.11 Sign-off

| Role | Name | Decision | Date |
| --- | --- | --- | --- |
| Author | Veqctor (kit generation) | Submitted | 2026-11-03 |
| Reviewer | Romain Dutrenois | | |

---

## Part 2: Results

*To be written after the campaign, against the criteria above.*
