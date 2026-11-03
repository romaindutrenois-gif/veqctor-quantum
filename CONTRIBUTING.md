# Contributing

Thank you for considering a contribution. New kits, fixes and better benchmarks are all welcome.

## What a kit must include

1. **A standard finance problem**, stated precisely: inputs, output, units.
2. **A classical benchmark** that is independent of the quantum code: a closed form, a reference library value (for example QuantLib), or a well-documented Monte Carlo with its standard error.
3. **The quantum version**, runnable on a simulator with stable Qiskit APIs.
4. **Tests** that compare the two within tolerances stated in advance, before the results are known.
5. **A resource estimate** at a useful accuracy, with the assumptions behind it.
6. **A README** with assumptions, limits and what the kit does not show.

Claims of speed-up or advantage must come with the benchmark and the resource estimate that support them.

## How to propose a change

1. Open an issue describing the kit or the fix.
2. Fork the repository and create a branch.
3. Keep each kit self-contained in `kits/<kit_name>/`, using the layout in the README.
4. Make sure the tests pass, then open a pull request.

By contributing, you agree that your contribution is licensed under the Apache License 2.0.
