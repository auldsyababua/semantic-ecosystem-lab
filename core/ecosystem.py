from __future__ import annotations

import json
import random
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from analysis.false_consensus import false_consensus
from analysis.metric_validation import validate_metrics
from analysis.entropy import entropy
from core.camps import camps as detect_camps
from core.config import ExperimentConfig, load_config
from core.constitution import constitution_distribution
from core.geography import geography_heatmap, geography_nodes
from core.invariants import Invariant, emergent_invariants
from core.metrics import semantic_distance_matrix, viability_scores
from core.reproduction import init_population, reproduce
from core.species import species_snapshot
from core.topology import topology_snapshot
from domains.regex_domain import Case, category, gen_cases


@dataclass
class ExperimentResult:
    metrics: list[dict[str, Any]]
    camps: list[dict[str, Any]]
    geography: list[dict[str, Any]]
    invariants: list[dict[str, Any]]
    phase_events: list[dict[str, Any]]
    false_events: list[dict[str, Any]]
    manifest: dict[str, Any]
    validation: dict[str, Any]
    topology_snapshots: list[dict[str, Any]]
    species_snapshots: list[dict[str, Any]]
    geography_heatmaps: list[dict[str, Any]]
    semantic_distance_matrices: list[dict[str, Any]]
    logs: list[dict[str, Any]]
    checkpoints: list[dict[str, Any]]
    run_dir: str | None = None


def run_experiment(config: ExperimentConfig, write_legacy_outputs: bool | None = None) -> ExperimentResult:
    rng = random.Random(config.seed)
    experiment_id = config.experiment_id or _default_experiment_id(config)
    fuzz = gen_cases(rng, config.initial_case_count)
    pop = init_population(
        rng,
        config.population_size,
        config.geography.width,
        config.geography.height,
        config.pressure.adversary_initial_ratio,
        config.constitution_weights,
        config.ablations,
    )

    metrics: list[dict[str, Any]] = []
    camps_all: list[dict[str, Any]] = []
    geo_all: list[dict[str, Any]] = []
    phase_events: list[dict[str, Any]] = []
    false_events: list[dict[str, Any]] = []
    invariants: list[Invariant] = []
    topology_snapshots: list[dict[str, Any]] = []
    species_snapshots: list[dict[str, Any]] = []
    geography_heatmaps: list[dict[str, Any]] = []
    semantic_distance_matrices: list[dict[str, Any]] = []
    logs: list[dict[str, Any]] = []
    checkpoints: list[dict[str, Any]] = []
    mutation_history: list[dict[str, object]] = []
    migration_events: list[dict[str, object]] = []

    manifest: dict[str, Any] = {
        "experiment_id": experiment_id,
        "seed": config.seed,
        "config_path": config.config_path,
        "config": config.to_manifest_dict(),
        "topology_initialization": geography_nodes(pop),
        "initial_constitution_distribution": constitution_distribution(pop),
        "constitution_distributions": [],
        "migration_events": migration_events,
        "mutation_history": mutation_history,
        "phase_events": phase_events,
    }

    for gen in range(config.generation_count):
        phase_events.extend(
            {"generation": gen, "event": event}
            for event in phase_shocks(gen, fuzz, pop, config, migration_events)
        )
        apply_optional_migration(rng, gen, pop, config, migration_events)
        invariant_dicts = [asdict(invariant) for invariant in invariants]
        scores, outputs = viability_scores(
            pop,
            fuzz,
            gen,
            invariant_dicts,
            config.pressure.local_radius,
            not config.ablations.local_influence and not config.ablations.geography,
            config.scoring,
        )
        camp = [] if config.ablations.clustering else detect_camps(pop, outputs, config.metrics.camp_agreement_threshold)
        disagreements = []
        ids = [agent.aid for agent in pop]
        for index in range(min(config.metrics.disagreement_scan_limit, len(fuzz))):
            case = fuzz[index]
            vals = [outputs[aid][index] for aid in ids]
            if len(set(vals)) > 1:
                disagreements.append({"pattern": case.pattern, "string": case.s, "category": category(case)})
        if config.ablations.invariant_synthesis:
            invariants = []
            inv_e = []
        else:
            inv_t = [
                Invariant("templated_newline", "newline should usually not match dot", "templated", 0.4),
                Invariant("templated_fullmatch", "fullmatch tends to stabilize coalitions", "templated", 0.4),
            ]
            inv_e = emergent_invariants(
                disagreements,
                config.metrics.emergent_invariant_threshold,
                config.metrics.emergent_invariant_score_denominator,
            )
            inv_i = [Invariant("inferred_locality", "nearby agents exhibit stronger agreement", "inferred", 0.5)] if camp else []
            invariants = inv_t + inv_i + inv_e
        fc = false_consensus(
            camp,
            fuzz,
            pop,
            config.metrics.false_consensus_case_limit,
            config.metrics.false_consensus_drift_threshold,
        )
        if fc:
            false_events.append({"generation": gen, **fc})
        const_div = len(set(agent.constitution_name for agent in pop))
        case_entropy = []
        for index in range(len(fuzz)):
            case_entropy.append(entropy([outputs[agent.aid][index] for agent in pop]))
        sem_ent = sum(case_entropy) / len(case_entropy)
        camp_count = len(camp)
        bif = max(0, camp_count - (camps_all[-1]["camp_count"] if camps_all else camp_count))
        adv_inf = sum(scores[agent.aid] for agent in pop if agent.adversary != "none") / max(1, sum(scores.values()))
        metric = {
            "generation": f"generation_{gen}",
            "population": len(pop),
            "semantic_entropy": sem_ent,
            "camp_count": camp_count,
            "constitution_diversity": const_div,
            "false_consensus_frequency": (
                sum(1 for event in false_events if event["false_consensus"]) / len(false_events)
                if false_events
                else 0.0
            ),
            "attractor_stability": 1.0 / (1.0 + bif),
            "bifurcation_count": bif,
            "phase_transitions": sum(1 for event in phase_events if event["generation"] == gen),
            "semantic_drift_velocity": (
                fc["drift_cases"] / max(1, config.metrics.false_consensus_case_limit)
                if fc
                else 0.0
            ),
            "adversarial_influence": adv_inf,
            "invariant_emergence_rate": len(inv_e) / max(1, len(invariants)),
        }
        metrics.append(metric)
        camps_all.append({"generation": f"generation_{gen}", "camp_count": camp_count, "camps": camp})
        geo_all.append({"generation": f"generation_{gen}", "nodes": geography_nodes(pop)})
        topology_snapshots.append(topology_snapshot(f"generation_{gen}", pop, config.pressure.local_radius))
        species_snapshots.append(species_snapshot(f"generation_{gen}", pop))
        geography_heatmaps.append(
            geography_heatmap(f"generation_{gen}", pop, config.geography.width, config.geography.height)
        )
        semantic_distance_matrices.append(semantic_distance_matrix(f"generation_{gen}", camp, outputs))
        manifest["constitution_distributions"].append(
            {"generation": f"generation_{gen}", "distribution": constitution_distribution(pop)}
        )
        checkpoints.append(
            {
                "generation": f"generation_{gen}",
                "metrics": metric,
                "camp_count": camp_count,
                "constitution_distribution": constitution_distribution(pop),
                "phase_events": [event for event in phase_events if event["generation"] == gen],
                "false_consensus": fc,
            }
        )
        logs.append({"type": "generation_metrics", "generation": gen, "metrics": metric})
        if fc:
            logs.append({"type": "false_consensus", "generation": gen, "event": fc})
        pop = reproduce(
            rng,
            pop,
            scores,
            [asdict(invariant) for invariant in invariants],
            gen,
            config.geography.width,
            config.geography.height,
            config.pressure.inheritance_mix_rate,
            config.pressure.mutation_rate,
            config.pressure.random_mutant_rate,
            config.pressure.family_mutation_rate,
            config.pressure.adversary_child_ratio,
            config.ablations,
            mutation_history,
        )

    result = ExperimentResult(
        metrics=metrics,
        camps=camps_all,
        geography=geo_all,
        invariants=[asdict(invariant) for invariant in invariants],
        phase_events=phase_events,
        false_events=false_events,
        manifest=manifest,
        validation={},
        topology_snapshots=topology_snapshots,
        species_snapshots=species_snapshots,
        geography_heatmaps=geography_heatmaps,
        semantic_distance_matrices=semantic_distance_matrices,
        logs=logs,
        checkpoints=checkpoints,
    )
    result.validation = validate_metrics(result, config.seed)

    if write_legacy_outputs is None:
        write_legacy_outputs = config.output.write_legacy
    from reports.dashboard import write_research_outputs

    result.run_dir = str(write_research_outputs(result, config, write_legacy_outputs))
    return result


def phase_shocks(gen: int, fuzz: list[Case], pop, config: ExperimentConfig, migration_events: list[dict[str, object]]) -> list[str]:
    if not config.phase_shocks.enabled:
        return []
    events = []
    if gen == config.phase_shocks.edge_case_generation:
        fuzz.extend([Case("[^a]", "a"), Case("[a-z]", "m"), Case("^$", "")])
        events.append("edge_case_injection")
    if gen == config.geography.shuffle_generation and not config.ablations.geography and not config.ablations.migration:
        for agent in pop[: config.geography.shuffle_count]:
            old = {"x": agent.x, "y": agent.y}
            agent.x = (agent.x + config.geography.shuffle_offset) % config.geography.width
            agent.y = (agent.y + config.geography.shuffle_offset) % config.geography.height
            migration_events.append({"generation": gen, "aid": agent.aid, "from": old, "to": {"x": agent.x, "y": agent.y}, "reason": "geography_shuffle"})
        events.append("geography_shuffle")
    if gen == config.phase_shocks.adversarial_shift_generation:
        fuzz.extend([Case(".", "\n\n"), Case("[z-a]", "")])
        events.append("adversarial_distribution_shift")
    return events


def apply_optional_migration(rng, gen: int, pop, config: ExperimentConfig, migration_events: list[dict[str, object]]) -> None:
    if config.ablations.geography or config.ablations.migration or config.geography.migration_probability <= 0:
        return
    for agent in pop:
        if rng.random() < config.geography.migration_probability:
            old = {"x": agent.x, "y": agent.y}
            agent.x = rng.randint(0, config.geography.width - 1)
            agent.y = rng.randint(0, config.geography.height - 1)
            migration_events.append({"generation": gen, "aid": agent.aid, "from": old, "to": {"x": agent.x, "y": agent.y}, "reason": "probabilistic_migration"})


def result_to_json(result: ExperimentResult) -> str:
    return json.dumps(asdict(result), indent=2)


def result_from_json(text: str) -> ExperimentResult:
    data = json.loads(text)
    data.setdefault("geography_heatmaps", [])
    data.setdefault("semantic_distance_matrices", [])
    return ExperimentResult(**data)


def print_summary(result: ExperimentResult) -> None:
    print("=== Oracle-Free Semantic Ecosystem Report ===")
    for metric in result.metrics:
        print(
            f"{metric['generation']}: pop={metric['population']} camps={metric['camp_count']} "
            f"entropy={metric['semantic_entropy']:.4f} const_div={metric['constitution_diversity']} "
            f"false_freq={metric['false_consensus_frequency']:.2f} drift_vel={metric['semantic_drift_velocity']:.2f}"
        )
    print(
        f"phase_events={len(result.phase_events)} false_consensus_events={len(result.false_events)} "
        f"invariants={len(result.invariants)}"
    )
    print(
        "Wrote: evolution_metrics.json, semantic_camps.json, false_consensus.md, "
        "phase_transition_events.json, semantic_geography.json, invariants.json, report.html, "
        "SEMANTIC_ECOSYSTEM_NOTES.md"
    )
    if result.run_dir:
        print(f"Run directory: {result.run_dir}")


def main_compat() -> None:
    cfg = load_config(Path("configs/strict.yaml"))
    result = run_experiment(cfg)
    print_summary(result)


def _default_experiment_id(config: ExperimentConfig) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"seed{config.seed}_{stamp}"
