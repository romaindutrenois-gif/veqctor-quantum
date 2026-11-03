# Tests and results

What the kit checks, what it finds, and what it would take to go further. How the circuit works is in [circuit.md](circuit.md). All numbers below are reproduced by `python docs/make_figures.py`.

Option used throughout: European call, spot 100, strike 105, rate 3%, volatility 20%, one year. Black-Scholes price: **7.1281**.

## Tests

Criteria were written before the results were known, except one tolerance noted below.

| # | Criterion | Result |
| --- | --- | --- |
| 1 | The circuit reproduces the discretised price to 1e-9, for 2 to 5 price qubits | Pass (difference below 1e-12) |
| 2 | With 6 price qubits, the discretised price is within 2% of Black-Scholes, and closer than with 3 | Pass (0.23%, against 2.16%) |
| 3 | Amplitude estimation lands within 1% of the exact circuit price | Pass (0.3%) |
| 4 | Sampling the circuit without amplitude estimation stays within 4 standard errors of the exact price | Pass |

Note on test 3: the first run used a smaller budget (powers up to 8, 100 measurements each), and the error was above the 2% first planned. The budget was raised to powers up to 32 and 200 measurements, and the tolerance tightened to 1%. Over 20 random seeds, the median error is then 0.2% to 0.3% and the largest 0.8%.

## Results

### 1. The circuit is exact; the grid sets the accuracy

| Price qubits | Grid points | Discretised price | Gap to Black-Scholes |
| --- | --- | --- | --- |
| 2 to 4 | 4 to 16 | 6.9740 | 2.16% |
| 5 to 6 | 32 to 64 | 7.1120 | 0.23% |
| 7 to 9 | 128 to 512 | 7.1243 | 0.05% |
| 10 | 1,024 | 7.1245 | 0.05% |

![Discretisation error](img/discretisation.png)

The error falls in steps, not smoothly. Each bin is priced exactly (conditional mean), so only the bin that straddles the strike carries an error. The error changes only when a refinement moves a bin edge past the strike. The remaining 0.05% comes from cutting the distribution at ±4 standard deviations. **Seven price qubits are enough for this option**: beyond that, extra qubits buy nothing.

### 2. Amplitude estimation: error falls like 1/N

![Error against number of calls](img/error_vs_calls.png)

| Calls of A | Amplitude estimation, RMS error (4 price qubits) | Monte Carlo, error with as many paths |
| --- | --- | --- |
| 800 | 0.52 | 0.44 |
| 3,600 | 0.17 | 0.21 |
| 7,000 | 0.094 | 0.15 |
| 13,600 | 0.052 | 0.11 |
| 26,600 | 0.024 | 0.077 |
| 52,400 | 0.011 | 0.055 |

- The fitted slope of the amplitude-estimation error is **−1.02** on a log-log scale, against −0.5 for Monte Carlo. That is the quadratic reduction in samples that amplitude estimation promises, observed in simulation.
- Amplitude estimation only wins **after about 1,500 calls**: with very few calls, its constant factor (π × the largest payoff) makes it worse than Monte Carlo.
- At a price error of 0.01 (one basis point of the spot), the fit gives about **60,000 calls of A, against 1.6 million Monte Carlo paths**: 26 times fewer. At 0.001, about 600,000 calls against 157 million paths: 260 times fewer.

### 3. But each call is expensive, and the circuit grows fast

| Price qubits | CNOTs in A | Depth of A | CNOTs in one Grover step Q | Depth of Q |
| --- | --- | --- | --- | --- |
| 3 | 84 | 290 | 182 | 606 |
| 4 | 203 | 387 | 442 | 852 |
| 5 | 626 | 1,037 | 1,334 | 2,178 |
| 6 | 1,737 | 2,548 | 3,596 | 5,230 |
| 7 | 5,000 | 12,155 | 10,170 | 24,491 |

![Circuit size](img/circuit_size.png)

With exact loading and one rotation per point, **the circuit roughly triples with each extra qubit**: exponential growth, which cancels the advantage beyond a handful of qubits. This is why efficient loading is the central research question.

## Discussion

- **The method works as theory says.** The circuit is exact, and amplitude estimation shows the 1/N convergence. As a teaching kit, it does its job: every number can be checked against the closed form.
- **Fewer calls does not mean faster.** One call of A here is thousands of gate layers. Even on an error-corrected machine running at the 10 MHz logical clock that published estimates require, 60,000 calls of a 5,000-layer circuit take on the order of 30 seconds. A GPU prices the same option to the same accuracy by Monte Carlo in milliseconds (order of magnitude). The advantage in call counts has to survive the cost per call.
- **The honest verdict.** For a European call, there is no case for quantum: the closed form is instant. The kit's value is the method and the benchmark, which carry over to the products where classical pricing is expensive.

## Extending the exercise

### Accuracy and qubits for one option

For a single underlying and one maturity, 7 price qubits (0.05% grid error here) plus one objective qubit are enough. Efficient loading would add work qubits for arithmetic, roughly doubling or tripling the count, still well under 50 qubits.

### Repricing a portfolio of options, or an order book

This is where the comparison turns. **One Monte Carlo simulation prices every option on the same underlying at once**: the paths are shared. **Amplitude estimation estimates one number per run**, so N options need N runs. At a price error of 0.01 per option:

| Options on one underlying | Monte Carlo paths (shared) | Amplitude-estimation calls (one run per option) | Who needs fewer calls |
| --- | --- | --- | --- |
| 1 | 1.6 million | 60,000 | Quantum, 26 times fewer |
| 10 | 1.6 million | 600,000 | Quantum, 2.6 times fewer |
| 26 | 1.6 million | 1.6 million | Even |
| 100 | 1.6 million | 6 million | Classical, 4 times fewer |
| 1,000 (an order book) | 1.6 million | 60 million | Classical, 38 times fewer |

Orders of magnitude, assuming similar volatility of payoffs across options; per-call costs not included, which only widens the gap in favour of classical.

**What follows:**

- **For an order book**, where each strike and maturity needs its own price, amplitude estimation loses from a few dozen options, even before counting the cost per call. Loading the distribution once and reusing it does not change this: the estimation step is still one per price.
- **For a single aggregate number**, the picture reverses. The value of a whole book, a tail probability for VaR, or a CVA is one expectation: one amplitude-estimation run, with the quadratic gain intact. That is why the Veqctor map lists Monte Carlo VaR, exposure and CVA as candidates, rather than vanilla pricing.
- **Sensitivities** multiply the count again: each Greek is one more number to estimate, whereas classical adjoint methods (AAD) produce all Greeks for a small multiple of one price.

### Path-dependent and multi-asset products

| Product | Price qubits (7 per variable) | What else is needed |
| --- | --- | --- |
| European, 1 asset (this kit) | 7 | 1 objective qubit |
| Basket of 5 assets, one date | 35 | Arithmetic for the basket value and payoff |
| Autocall, 1 asset, 12 observation dates | 84 | Barrier tests on every date, coupon logic |
| Same with 3 underlyings (worst-of) | 252 | Minimum across assets on every date |

These are logical qubits before arithmetic and error correction. Published end-to-end estimates for path-dependent products (an autocallable and a target accrual redemption forward) put the requirement at:

- **7,500 logical qubits, a T-depth of 46 million, and a 10 MHz logical clock** (Chakrabarti et al., 2021);
- **4,700 logical qubits and about 10⁹ T gates at 45 MHz** with quantum signal processing (Stamatopoulos and Zeng, 2024), about 4 times fewer qubits and 16 times fewer T gates.

With surface-code error correction, each logical qubit needs on the order of hundreds to a thousand physical qubits: millions of physical qubits in total. Today's machines have hundreds to a few thousand noisy physical qubits.

### Next steps for this kit

1. Replace exact loading with an efficient one, and measure how the circuit size then grows with n.
2. Price an aggregate (the value of a small book of calls in one run) to show where the quadratic gain survives.
3. Run the 3-qubit circuit on cloud hardware and measure the effect of noise against the simulator.
4. Repeat the exercise for Heston, benchmarked against the Veqctor Heston validation kit.

## References

- Suzuki et al., *Amplitude estimation without phase estimation*, Quantum Information Processing, 2020. [arXiv:1904.10246](https://arxiv.org/abs/1904.10246)
- Stamatopoulos et al., *Option pricing using quantum computers*, Quantum, 2020. [arXiv:1905.02666](https://arxiv.org/abs/1905.02666)
- Chakrabarti et al., *A threshold for quantum advantage in derivative pricing*, Quantum, 2021. [arXiv:2012.03819](https://arxiv.org/abs/2012.03819)
- Vazquez and Woerner, *Efficient state preparation for quantum amplitude estimation*, Phys. Rev. Applied, 2021. [arXiv:2005.07711](https://arxiv.org/abs/2005.07711)
- Stamatopoulos and Zeng, *Derivative pricing using quantum signal processing*, Quantum, 2024. [arXiv:2307.14310](https://arxiv.org/abs/2307.14310)
