"""Tuning sweep: both benches in one run.

    python tune.py [--runs 300] [--careers 300]
"""

import argparse

import bench_combat
import bench_expedition

if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--runs", type=int, default=300)
    p.add_argument("--careers", type=int, default=300)
    args = p.parse_args()
    print("== combat ==")
    bench_combat.bench(args.runs)
    print()
    print("== careers ==")
    bench_expedition.bench(args.careers, 10)
