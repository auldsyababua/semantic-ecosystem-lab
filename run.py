#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from core.config import load_config
from core.ecosystem import print_summary, run_experiment


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a semantic ecosystem experiment.")
    parser.add_argument("--config", default="configs/strict.yaml", help="Path to experiment config.")
    parser.add_argument("--experiment-id", default=None, help="Override experiment ID.")
    parser.add_argument("--seed", type=int, default=None, help="Override random seed.")
    parser.add_argument("--generations", type=int, default=None, help="Override generation count.")
    parser.add_argument("--no-legacy-outputs", action="store_true", help="Only write to data/runs/<experiment_id>.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config(Path(args.config))
    if args.experiment_id:
        cfg.experiment_id = args.experiment_id
    if args.seed is not None:
        cfg.seed = args.seed
    if args.generations is not None:
        cfg.generation_count = args.generations
    if args.no_legacy_outputs:
        cfg.output.write_legacy = False
    result = run_experiment(cfg)
    print_summary(result)


if __name__ == "__main__":
    main()
