# veqctor-quantum

Open-source quantum circuit kits for quantitative finance, each benchmarked against a validated classical model.

Part of [Veqctor](https://veqctor.com), a model roadmap for quants: from the conventional models banks run today, to their quantum adaptation, to quantum hardware. This repository holds the quantum adaptation layer. It is free and open source (Apache-2.0).

## The principle: no claim without a benchmark

Model validation teams accept nothing without an independent benchmark. The same rule applies here. Every kit:

- solves a standard finance problem with a quantum algorithm, on a simulator;
- compares the result with a validated classical model for the same problem;
- estimates the resources (qubits, circuit depth, run time) the algorithm would need at a useful accuracy, and therefore when hardware could make it competitive;
- states its assumptions and limits openly, including what it does not achieve today.

No quantum advantage has been demonstrated for any financial use case in production. These kits show what a quantum algorithm must beat, and how far the hardware still is.

## Kits

| Kit | Problem | Quantum algorithm | Classical benchmark | Status |
| --- | --- | --- | --- | --- |
| [`qae_european`](kits/qae_european) | European option price | Amplitude estimation (iterative, no phase estimation) | Black-Scholes closed form and Monte Carlo | In progress |
| [`qaoa_portfolio`](kits/qaoa_portfolio) | Portfolio selection with a cardinality constraint | QAOA | Exact enumeration and a classical solver | Planned |
| [`born_machine`](kits/born_machine) | Generating a return distribution | Quantum circuit Born machine | Historical and parametric scenario generators | Planned |

Each kit follows the same layout:

```
kits/<kit>/
  README.md            what it does, assumptions, limits, how to run
  circuit.py           the quantum version (Qiskit)
  classical.py         the classical benchmark
  resources.py         resource estimate at a target accuracy
  tests/               tests comparing the two within stated tolerances
```

## From model to circuit

[`docs/from-model-to-circuit.md`](docs/from-model-to-circuit.md) explains the steps the kits follow: where the classical model spends its compute, loading the distribution into a circuit, encoding the payoff, estimating the amplitude, and estimating the resources.

## Requirements

Python 3.10 or later, Qiskit 1.x, NumPy and SciPy. Each kit lists its exact requirements.

## Contributing

Contributions are welcome, especially new kits that follow the principle above. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Licence

Apache License 2.0, see [LICENSE](LICENSE).
