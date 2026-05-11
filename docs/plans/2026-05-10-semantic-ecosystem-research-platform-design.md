# Semantic Ecosystem Research Platform Design

## Goal

Refactor the current single-file semantic ecosystem simulation into a modular, reproducible research platform while preserving the default simulation behavior and generated findings as closely as possible.

## Architecture

The existing model remains the source of truth. Core simulation state and rules move into `core/`, domain primitives into `domains/`, engine variants into `implementations/`, metric validation into `analysis/`, and report writers into `reports/`. `experiment.py` stays as a compatibility entry point, while `run.py` becomes the configurable CLI.

Default configuration must reproduce the current run parameters: seed `1337`, population `80`, `1000` generated cases, `5` generations, `20x20` geography, original families, constitutions, phase shocks, scoring weights, and output names. New ablation flags are guarded so every mechanism remains enabled unless a config explicitly disables it.

## Data Flow

`run.py --config configs/strict.yaml` loads a standard-library YAML subset, creates an `ExperimentConfig`, then calls `core.ecosystem.run_experiment`. The run returns an `ExperimentResult` containing metrics, camps, geography snapshots, invariant snapshots, events, JSONL log records, and reproducibility metadata. Reports are written through `reports.html_report`, `reports.dashboard`, and `reports.graphs`.

Every run gets an experiment ID and writes to `data/runs/<experiment_id>/`. Legacy root artifacts are still written by default for compatibility, but the registry directory is the canonical research output.

## Reproducibility

The manifest records seed, config path, config values, constitution distributions, topology initialization, migration events, mutation history, phase events, and output paths. The simulation uses a single `random.Random(seed)` instance and avoids extra random draws in no-op instrumentation paths.

## Ablations

Ablation switches disable mechanisms at existing decision points without changing defaults: geography/local influence, adversaries, inheritance, constitutions, invariant synthesis, migration/geography shocks, and clustering/camp analysis. Disabled mechanisms should degrade gracefully to simple neutral behavior and remain explicit in the manifest.

## Metric Validation

Validation modules compute lightweight, standard-library-only diagnostics from already captured outputs: null-model camp comparisons, randomized baseline entropy, entropy sanity checks, cluster stability, topology sensitivity summaries, and false-consensus robustness. These are analysis artifacts and must not feed back into ecological dynamics.

## Testing

Use `unittest` only. Tests cover deterministic seed reproducibility, compatibility metrics, invariant consistency, species/camp sanity, entropy sanity, and serialization round trips. The main preservation test compares rounded default metrics rather than raw floating-point JSON text.
