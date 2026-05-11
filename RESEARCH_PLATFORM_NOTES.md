# Research Platform Notes

## 1. Metrics That Appear Trustworthy

The strongest metrics are direct structural counts: population size, camp count, constitution diversity, phase-event counts, species snapshots, and topology density. They are computed from captured state and are reproducible under a fixed seed.

Semantic entropy is useful as a diversity indicator because it is computed per case across population outputs and then averaged. Treat it as descriptive, not as proof of semantic richness.

The strict verification run `data/runs/full_refactor_verification/` preserved the baseline rounded metrics: camp counts `6, 9, 12, 7, 6`, entropy `0.4887, 0.4042, 0.3647, 0.2450, 0.1759`, three phase events, five false-consensus observations, and four final invariants.

## 2. Metrics That May Still Be Artifacts

False consensus depends on the retrospective `STRICT_ASCII` reference and the first 200 fuzz cases. It is useful for detecting drift from that reference, but it is not oracle-free in the final interpretation.

Camp significance is based on a fixed 0.93 agreement threshold. The null-model comparison now reports whether dominant camps are larger than a simple uniform expectation, but this is still a proxy rather than a formal statistical test.

The camp threshold, false-consensus case limit, drift threshold, disagreement scan limit, and emergent-invariant thresholds are now explicit config values. Sensitivity sweeps over those values are required before treating camps or false consensus as paper-grade effects.

## 3. Mechanisms That Most Strongly Affect Outcomes

The largest default pressures are local agreement, diversity/novelty cycling, inheritance crossover, mutation, phase shocks, and constitution semantics. Geography matters through neighborhood membership and the generation-3 shuffle.

## 4. Experimental Knobs That Matter Most

Start sweeps with seed, generation count, population size, mutation rate, inheritance mix rate, local radius, adversarial ratios, constitution weights, and geography density. These change outcomes without requiring new rules.

The scoring weights are also explicit in `configs/strict.yaml`. Change them only for controlled ablations or sweeps; the strict defaults preserve the original fitness incentives.

## 5. Dynamics That Appear Robust Across Seeds

The default run shows recurring camps, entropy decline after early diversity, false-consensus episodes after edge-case pressure, and constitution/species turnover. These are hypotheses until confirmed by multi-seed sweeps.

## 6. What Would Still Invalidate The Project Scientifically

The project would be weakened if camp structure disappears under threshold sensitivity, if entropy tracks only test-case mix rather than semantic diversity, if false consensus is driven by the strict reference choice, or if reported effects vanish across seeds/configurations.

## 7. Minimum Publishable Experiment

Run a grid over at least 30 seeds with the strict config and ablations for geography, adversaries, inheritance, invariant synthesis, local influence, migration, and clustering. Report default-vs-ablation deltas for entropy, camp count, false consensus, topology density, species survival, and cluster stability, with manifests and JSONL logs retained for every run.

For each run, retain `run_manifest.json`, `metrics/evolution_metrics.csv`, `logs/events.jsonl`, generation checkpoints, topology snapshots, species snapshots, geography heatmaps, semantic distance matrices, and `analysis/metric_validation.json` so conclusions can be audited without rerunning simulations.
