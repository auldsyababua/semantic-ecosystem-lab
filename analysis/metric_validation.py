from __future__ import annotations

import math
import random
from statistics import mean

from analysis.clustering import camp_null_model, cluster_stability
from analysis.false_consensus import robustness_summary
from analysis.phase_transitions import summarize_phase_transitions


def validate_metrics(result, seed: int) -> dict[str, object]:
    entropies = [metric["semantic_entropy"] for metric in result.metrics]
    entropy_deltas = [
        entropies[index + 1] - entropies[index]
        for index in range(len(entropies) - 1)
    ]
    rng = random.Random(seed + 999)
    randomized_entropy_baseline = []
    for metric in result.metrics:
        synthetic = [rng.randrange(max(1, metric["camp_count"])) for _ in range(metric["population"])]
        counts = {value: synthetic.count(value) for value in set(synthetic)}
        n = len(synthetic)
        entropy = 0.0
        for count in counts.values():
            p = count / n
            entropy -= p * math.log2(p)
        randomized_entropy_baseline.append(entropy)

    topology_density = [
        snapshot.get("density", 0.0)
        for snapshot in result.topology_snapshots
    ]
    return {
        "null_model_comparisons": camp_null_model(result.camps),
        "randomized_baselines": {
            "entropy_by_generation": randomized_entropy_baseline,
            "mean_entropy": mean(randomized_entropy_baseline) if randomized_entropy_baseline else 0.0,
        },
        "entropy_sanity_checks": {
            "values": entropies,
            "deltas": entropy_deltas,
            "monotonic_nonincreasing": all(delta <= 0 for delta in entropy_deltas),
            "nonnegative": all(value >= 0 for value in entropies),
        },
        "cluster_stability_tests": cluster_stability(result.camps),
        "topology_sensitivity_analysis": {
            "density_by_generation": topology_density,
            "mean_density": mean(topology_density) if topology_density else 0.0,
            "range": (max(topology_density) - min(topology_density)) if topology_density else 0.0,
        },
        "false_consensus_robustness": robustness_summary(result.false_events),
        "phase_transition_summary": summarize_phase_transitions(result.phase_events),
    }
