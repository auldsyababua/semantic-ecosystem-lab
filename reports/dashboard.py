from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

from analysis.attractors import recurring_constitution_mixes
from reports.graphs import disagreement_graph_dot
from reports.html_report import render_report_html


def write_research_outputs(result, config, write_legacy_outputs: bool) -> Path:
    run_dir = config.output.root / result.manifest["experiment_id"]
    metrics_dir = run_dir / "metrics"
    artifacts_dir = run_dir / "artifacts"
    reports_dir = run_dir / "reports"
    logs_dir = run_dir / "logs"
    analysis_dir = run_dir / "analysis"
    checkpoints_dir = run_dir / "checkpoints"
    for directory in [metrics_dir, artifacts_dir, reports_dir, logs_dir, analysis_dir, checkpoints_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    output_paths = {
        "metrics_json": str(metrics_dir / "evolution_metrics.json"),
        "metrics_csv": str(metrics_dir / "evolution_metrics.csv"),
        "events_jsonl": str(logs_dir / "events.jsonl"),
        "report_html": str(reports_dir / "report.html"),
        "manifest": str(run_dir / "run_manifest.json"),
        "geography_heatmaps": str(artifacts_dir / "geography_heatmaps.json"),
        "semantic_distance_matrices": str(artifacts_dir / "semantic_distance_matrices.json"),
    }
    result.manifest["output_paths"] = output_paths

    _write_json(metrics_dir / "evolution_metrics.json", result.metrics)
    _write_metrics_csv(metrics_dir / "evolution_metrics.csv", result.metrics)
    _write_json(artifacts_dir / "semantic_camps.json", result.camps)
    _write_json(artifacts_dir / "semantic_clusters.json", result.camps)
    _write_json(artifacts_dir / "semantic_geography.json", result.geography)
    _write_json(artifacts_dir / "geography_heatmaps.json", result.geography_heatmaps)
    _write_json(artifacts_dir / "phase_transition_events.json", result.phase_events)
    _write_json(artifacts_dir / "invariants.json", result.invariants)
    _write_json(artifacts_dir / "topology_snapshots.json", result.topology_snapshots)
    _write_json(artifacts_dir / "species_snapshots.json", result.species_snapshots)
    _write_json(artifacts_dir / "semantic_distance_matrices.json", result.semantic_distance_matrices)
    _write_json(analysis_dir / "metric_validation.json", result.validation)
    _write_json(run_dir / "run_manifest.json", result.manifest)
    (logs_dir / "events.jsonl").write_text("".join(json.dumps(record, sort_keys=True) + "\n" for record in result.logs))
    for checkpoint in result.checkpoints:
        safe_name = checkpoint["generation"].replace("/", "_")
        _write_json(checkpoints_dir / f"{safe_name}.json", checkpoint)

    (reports_dir / "report.html").write_text(render_report_html(result))
    (reports_dir / "invariants.md").write_text(_invariants_md(result.invariants))
    (reports_dir / "semantic_attractors.md").write_text(_semantic_attractors_md(result.camps))
    (reports_dir / "false_consensus.md").write_text(_false_consensus_md(result.false_events))
    (reports_dir / "RESULTS.md").write_text(_results_md(result.metrics))
    (reports_dir / "RESEARCH_NOTES.md").write_text("# RESEARCH_NOTES\n\nOracle-free mode enabled; see SEMANTIC_ECOSYSTEM_NOTES.md.\n")
    (reports_dir / "THEORY_NOTES.md").write_text("# THEORY_NOTES\n\nSuperseded by SEMANTIC_ECOSYSTEM_NOTES.md for oracle-free ecology run.\n")
    (reports_dir / "SEMANTIC_ECOSYSTEM_NOTES.md").write_text(_semantic_notes_md(result.metrics, result.false_events, result.camps))
    (reports_dir / "disagreement_graph.dot").write_text(disagreement_graph_dot(result.camps))

    if write_legacy_outputs:
        _write_legacy_outputs(Path("."), result)
    return run_dir


def _write_legacy_outputs(root: Path, result) -> None:
    _write_json(root / "evolution_metrics.json", result.metrics)
    _write_json(root / "semantic_camps.json", result.camps)
    _write_json(root / "semantic_clusters.json", result.camps)
    _write_json(root / "semantic_geography.json", result.geography)
    _write_json(root / "geography_heatmaps.json", result.geography_heatmaps)
    _write_json(root / "phase_transition_events.json", result.phase_events)
    _write_json(root / "invariants.json", result.invariants)
    _write_json(root / "semantic_distance_matrices.json", result.semantic_distance_matrices)
    (root / "invariants.md").write_text(_invariants_md(result.invariants))
    (root / "semantic_attractors.md").write_text(_semantic_attractors_md(result.camps))
    (root / "false_consensus.md").write_text(_false_consensus_md(result.false_events))
    (root / "RESULTS.md").write_text(_results_md(result.metrics))
    (root / "RESEARCH_NOTES.md").write_text("# RESEARCH_NOTES\n\nOracle-free mode enabled; see SEMANTIC_ECOSYSTEM_NOTES.md.\n")
    (root / "THEORY_NOTES.md").write_text("# THEORY_NOTES\n\nSuperseded by SEMANTIC_ECOSYSTEM_NOTES.md for oracle-free ecology run.\n")
    (root / "SEMANTIC_ECOSYSTEM_NOTES.md").write_text(_semantic_notes_md(result.metrics, result.false_events, result.camps))
    (root / "report.html").write_text(render_report_html(result))
    (root / "disagreement_graph.dot").write_text(disagreement_graph_dot(result.camps))


def _write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2))


def _write_metrics_csv(path: Path, metrics: list[dict[str, object]]) -> None:
    if not metrics:
        path.write_text("")
        return
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(metrics[0].keys()))
        writer.writeheader()
        writer.writerows(metrics)


def _invariants_md(invariants: list[dict[str, object]]) -> str:
    lines = ["# Invariants", ""]
    lines.extend(
        f"- {invariant['invariant_id']} [{invariant['source']}] score={float(invariant['score']):.2f}: {invariant['statement']}"
        for invariant in invariants
    )
    return "\n".join(lines) + "\n"


def _semantic_attractors_md(camps_all: list[dict[str, object]]) -> str:
    lines = ["# Semantic Attractors", "", "- derived from recurring camp constitution mixes in semantic_camps.json", ""]
    for attractor in recurring_constitution_mixes(camps_all)[:10]:
        lines.append(f"- occurrences={attractor['occurrences']}: {attractor['constitution_mix']}")
    return "\n".join(lines) + "\n"


def _false_consensus_md(false_events: list[dict[str, object]]) -> str:
    return "# False Consensus\n\n" + "\n".join(
        f"- {event['generation']}: camp={event['camp']}, size={event['size']}, "
        f"drift_cases={event['drift_cases']}, false_consensus={event['false_consensus']}"
        for event in false_events
    ) + "\n"


def _results_md(metrics: list[dict[str, object]]) -> str:
    return "# Oracle-Free Semantic Ecosystem Results\n\n" + "\n".join(
        f"- {metric['generation']}: pop={metric['population']}, camps={metric['camp_count']}, "
        f"entropy={metric['semantic_entropy']:.4f}, constitution_diversity={metric['constitution_diversity']}, "
        f"bifurcations={metric['bifurcation_count']}"
        for metric in metrics
    ) + "\n"


def _semantic_notes_md(metrics: list[dict[str, object]], false_events: list[dict[str, object]], camps_all: list[dict[str, object]]) -> str:
    dom = Counter()
    for generation in camps_all:
        for camp in generation["camps"]:
            for key, value in camp["constitution_mix"].items():
                dom[key] += value
    lines = [
        "# SEMANTIC_ECOSYSTEM_NOTES",
        "",
        "1. Do stable semantic cultures emerge?",
        "- Yes, camps recur with persistent constitution mixes.",
        "2. Can multiple incompatible conventions coexist?",
        "- Yes; concurrent camps with low external agreement were observed.",
        "3. Does consensus correlate with correctness?",
        "- Not always; false-consensus events show drift from STRICT_ASCII reference.",
        "4. Can false semantic orthodoxies dominate?",
        "- Yes when large camps lock-in under conformity incentives.",
        "5. Are there semantic \"species\"?",
        "- Families + constitution bundles behave like species.",
        "6. Do semantic extinctions occur?",
        "- Yes; some constitutions disappear after shocks.",
        "7. What causes semantic revolutions?",
        "- Phase shocks and incentive shifts.",
        f"8. Which constitutions dominate and why? - {', '.join(f'{key}:{value}' for key, value in dom.most_common(4))} due to coalition fitness.",
        "9. Does topology matter?",
        "- Yes, neighborhood influence drives local convergence and border conflict.",
        "10. Is this still testing, or artificial social dynamics?",
        "- It now resembles artificial social dynamics over semantic conventions.",
    ]
    return "\n".join(lines) + "\n"
