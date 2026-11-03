"""Command line: qae-european {price, verify, campaign} (see README)."""
import argparse, csv, json, warnings


def main(argv=None):
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    ap = argparse.ArgumentParser(prog="qae-european")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("price", help="price one option with every method")
    for k, v in (("spot", 100.0), ("strike", 105.0), ("rate", 0.03), ("vol", 0.2), ("maturity", 1.0)):
        p.add_argument(f"--{k}", type=float, default=v)
    p.add_argument("--qubits", type=int, default=5)
    p.add_argument("--depth", type=int, default=8)
    p.add_argument("--seed", type=int, default=1)
    v = sub.add_parser("verify", help="full statevector check of the Grover identity on a random subset")
    v.add_argument("--scenarios", type=int, default=20)
    v.add_argument("--out", default="results/verification.json")
    c = sub.add_parser("campaign", help="run (or resume) the test campaign")
    c.add_argument("--out", default="results/campaign.csv")
    c.add_argument("--start", type=int, default=0)
    c.add_argument("--stop", type=int, default=None)
    c.add_argument("--processes", type=int, default=1)
    a = ap.parse_args(argv)

    import numpy as np, os
    from . import Option, LognormalGrid, QuantumPricer, MaximumLikelihoodAE, Ladder, BlackScholes, MonteCarlo, QuasiMonteCarlo
    if a.cmd == "price":
        o = Option(a.spot, a.strike, a.rate, a.vol, a.maturity)
        rng = np.random.default_rng(a.seed)
        g = LognormalGrid(o, a.qubits); q = QuantumPricer(g); lad = Ladder.exponential(a.depth)
        print(json.dumps({
            "black_scholes": BlackScholes.call(o), "grid_price": g.price(), "circuit_exact": q.price_exact(),
            "amplitude_estimation": float(MaximumLikelihoodAE(lad).estimate_prices(q, rng)[0]), "calls": lad.calls,
            "monte_carlo": MonteCarlo().price(o, lad.calls, rng).__dict__,
            "quasi_monte_carlo": QuasiMonteCarlo().price(o, lad.calls, rng).__dict__}, indent=2))
    elif a.cmd == "verify":
        from .campaign import verify_circuits
        rows = verify_circuits(a.scenarios)
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(rows, open(a.out, "w"), indent=1)
        print(f"{len(rows)} checks, largest difference {max(r['max_abs_diff'] for r in rows):.2e}")
    elif a.cmd == "campaign":
        from .campaign import run
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        print(f"{run(a.out, a.start, a.stop, a.processes)} scenarios run")


if __name__ == "__main__":
    main()
