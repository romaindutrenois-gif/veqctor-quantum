"""Command line: qae-european {price, verify, campaign} (see README)."""
import argparse, csv, json, warnings


def _plain(estimate):
    """Estimate as a dict for valid JSON: an undefined standard error (NaN) becomes null."""
    import math
    return {k: (None if isinstance(v, float) and math.isnan(v) else v) for k, v in estimate.__dict__.items()}


def _write_run_info(path, start=0, stop=None):
    """Append a record of the code and environment of this run (one entry per call, resumes included)."""
    import os, platform, subprocess, sys, datetime
    import numpy, scipy, qiskit
    from . import __version__, campaign
    here = os.path.dirname(os.path.abspath(__file__))
    try:
        commit = subprocess.run(["git", "-C", here, "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
        dirty = bool(subprocess.run(["git", "-C", here, "status", "--porcelain", "--", "."], capture_output=True, text=True).stdout.strip())
    except OSError:
        commit, dirty = "", None
    info = dict(scenarios=[start, stop], started=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
                package_version=__version__, package_path=here, git_commit=commit, uncommitted_changes=dirty,
                seed=campaign.SEED, draws=campaign.DRAWS, shots=campaign.SHOTS, qubits=campaign.QUBITS, depths=campaign.DEPTHS,
                python=sys.version.split()[0], platform=platform.platform(),
                qiskit=qiskit.__version__, numpy=numpy.__version__, scipy=scipy.__version__)
    log = []
    if os.path.exists(path):
        with open(path) as f:
            old = json.load(f)
        log = old if isinstance(old, list) else [old]
    log.append(info)
    with open(path, "w") as f:
        json.dump(log, f, indent=1)


def main(argv=None):
    warnings.filterwarnings("ignore", category=DeprecationWarning, module="qiskit")
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
            "monte_carlo": _plain(MonteCarlo().price(o, lad.calls, rng)),
            "quasi_monte_carlo": _plain(QuasiMonteCarlo().price(o, lad.calls, rng))}, indent=2))
    elif a.cmd == "verify":
        from .campaign import verify_circuits
        rows = verify_circuits(a.scenarios)
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        json.dump(rows, open(a.out, "w"), indent=1)
        print(f"{len(rows)} checks, largest difference {max(r['max_abs_diff'] for r in rows):.2e}")
    elif a.cmd == "campaign":
        from .campaign import run
        os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
        _write_run_info(os.path.join(os.path.dirname(a.out) or ".", "run_info.json"), a.start, a.stop)
        print(f"{run(a.out, a.start, a.stop, a.processes)} scenarios run")


if __name__ == "__main__":
    main()
