# veqctor-quantum

Open-source quantum circuit kits for quantitative finance, each benchmarked against a validated classical model.

Part of [Veqctor](https://veqctor.com), a model roadmap for quants: from the conventional models banks run today, to their quantum adaptation, to quantum hardware. This repository holds the quantum adaptation layer. It is free and open source (Apache-2.0).

## The principle: no claim without a benchmark

Model validation teams accept nothing without an independent benchmark. The same rule applies here. Every kit:

- solves a standard finance problem with a quantum algorithm, on a simulator;
- compares the result with a validated classical model for the same problem;
- estimates the resources (qubits, circuit depth, calls) the algorithm would need at a useful accuracy, and points to published run-time estimates on fault-tolerant hardware, to show how far hardware is from making it competitive;
- states its assumptions and limits openly, including what it does not achieve today.

No quantum advantage has been demonstrated for any financial use case in production. These kits show what a quantum algorithm must beat, and how far the hardware still is.

## Kits

| Kit | Problem | Quantum algorithm | Classical benchmark | Status |
| --- | --- | --- | --- | --- |
| [`qae_european`](kits/qae_european) | European option price | Maximum-likelihood amplitude estimation (no phase estimation) | Black-Scholes closed form and Monte Carlo | Available |
| [`qaoa_portfolio`](kits/qaoa_portfolio) | Portfolio selection with a cardinality constraint | QAOA | Exact enumeration and a classical solver | Planned |
| [`born_machine`](kits/born_machine) | Generating a return distribution | Quantum circuit Born machine | Historical and parametric scenario generators | Planned |

Each kit is a Python package with its documentation and its published results:

```
kits/<kit>/
  README.md            user guide: install, run, reproduce, adapt; limits
  pyproject.toml       the package, with requirements-lock.txt for the frozen environment
  src/<kit>/           the quantum version, the classical benchmarks, the campaign, the resource estimate
  tests/               unit tests
  docs/                Document 1 (circuit), Document 2 (benchmarks), Document 3 (test plan and results),
                       the analysis scripts, the independent review and the exports (Word, LaTeX, PDF)
  results/             the published campaign
```

## From model to circuit

[`docs/from-model-to-circuit.md`](docs/from-model-to-circuit.md) explains the steps the kits follow: where the classical model spends its compute, loading the distribution into a circuit, encoding the payoff, estimating the amplitude, and estimating the resources.

## Requirements

Python 3.10 or later, Qiskit 1.2 or later (the published results use Qiskit 2.6.1), NumPy and SciPy. Each kit pins its exact environment in `requirements-lock.txt`.

## Contributing

Contributions are welcome, especially new kits that follow the principle above. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

Apache License 2.0, see [LICENSE](LICENSE).
