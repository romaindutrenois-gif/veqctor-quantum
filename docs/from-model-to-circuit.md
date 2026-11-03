# From model to circuit

How a classical pricing or risk model becomes a quantum algorithm, step by step. Each kit in this repository follows these steps.

1. **Find where the model spends its compute.** Quantum algorithms help with specific tasks. Monte Carlo sampling is the main candidate (amplitude estimation); combinatorial optimisation is another (QAOA). Models that are already fast, such as closed forms or curve bootstraps, are not candidates.
2. **Load the distribution.** The circuit must prepare a quantum state that encodes the model's distribution of outcomes. This step is often the bottleneck, and it decides whether any speed-up survives.
3. **Encode the payoff.** A rotation maps the payoff of each outcome to an amplitude, so that the quantity to estimate becomes a probability.
4. **Estimate the amplitude.** Amplitude estimation needs a number of circuit runs proportional to 1/ε for accuracy ε, against 1/ε² samples for classical Monte Carlo: a quadratic reduction, before overheads.
5. **Estimate the resources.** Count qubits, circuit depth and run time at a target accuracy, including error correction, to see when hardware could compete with a classical benchmark on a GPU.
6. **Compare with the validated classical model.** The classical kit remains the reference: the quantum version is accepted only within stated tolerances.

Further reading is listed on [veqctor.com/resources](https://veqctor.com/resources#adaptation).
