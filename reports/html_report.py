from __future__ import annotations

import html
import json


def render_report_html(result) -> str:
    metrics_rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(metric['generation']))}</td>"
        f"<td>{metric['camp_count']}</td>"
        f"<td>{metric['constitution_diversity']}</td>"
        f"<td>{metric['semantic_entropy']:.4f}</td>"
        f"<td>{metric['false_consensus_frequency']:.2f}</td>"
        f"<td>{metric['adversarial_influence']:.2f}</td>"
        "</tr>"
        for metric in result.metrics
    )
    entropies = [metric["semantic_entropy"] for metric in result.metrics]
    max_entropy = max([0.0001] + entropies)
    bars = "".join(
        f"<rect x='{20 + index * 55}' y='{180 - int(140 * entropy / max_entropy)}' width='35' "
        f"height='{int(140 * entropy / max_entropy)}' fill='#2f7d68'/>"
        f"<text x='{22 + index * 55}' y='198' font-size='9'>g{index}</text>"
        for index, entropy in enumerate(entropies)
    )
    camp_details = "".join(_camp_summary(generation) for generation in result.camps)
    species_details = "".join(_species_summary(snapshot) for snapshot in result.species_snapshots)
    topology_details = "".join(_topology_summary(snapshot) for snapshot in result.topology_snapshots)
    heatmap_details = "".join(
        "<details>"
        f"<summary>{html.escape(str(snapshot['generation']))}: {snapshot['width']}x{snapshot['height']}</summary>"
        f"<pre>{html.escape(_render_heatmap(snapshot['counts']))}</pre>"
        "</details>"
        for snapshot in result.geography_heatmaps
    )
    distance_details = "".join(
        "<details>"
        f"<summary>{html.escape(str(matrix['generation']))}: {len(matrix['camp_ids'])} camps</summary>"
        f"<pre>{html.escape(json.dumps(matrix, indent=2))}</pre>"
        "</details>"
        for matrix in result.semantic_distance_matrices
    )
    validation = html.escape(json.dumps(result.validation, indent=2))
    phase_items = "".join(f"<li>{html.escape(str(event))}</li>" for event in result.phase_events)
    false_items = "".join(f"<li>{html.escape(str(event))}</li>" for event in result.false_events)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Semantic Ecosystem Dashboard</title>
<style>
body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 24px; line-height: 1.45; color: #17211d; }}
table {{ border-collapse: collapse; width: 100%; max-width: 980px; }}
th, td {{ border: 1px solid #cad6d0; padding: 6px 8px; text-align: left; }}
th {{ background: #edf3f0; }}
section {{ margin: 24px 0; }}
pre {{ max-height: 360px; overflow: auto; background: #f6f8f7; padding: 10px; border: 1px solid #dbe4df; }}
.layers label {{ display: inline-block; margin-right: 12px; }}
#layer-camps:not(:checked) ~ .camp-layer,
#layer-species:not(:checked) ~ .species-layer,
#layer-topology:not(:checked) ~ .topology-layer,
#layer-validation:not(:checked) ~ .validation-layer {{ display: none; }}
</style>
</head>
<body>
<h1>Oracle-Free Semantic Ecosystem Dashboard</h1>
<section class="layers">
<input id="layer-camps" type="checkbox" checked><label for="layer-camps">Camps</label>
<input id="layer-species" type="checkbox" checked><label for="layer-species">Species</label>
<input id="layer-topology" type="checkbox" checked><label for="layer-topology">Topology</label>
<input id="layer-validation" type="checkbox" checked><label for="layer-validation">Validation</label>
<div>
<h2>Metrics</h2>
<table><tr><th>Gen</th><th>Camps</th><th>Constitution Diversity</th><th>Entropy</th><th>False Consensus Freq</th><th>Adversarial Influence</th></tr>{metrics_rows}</table>
<h2>Entropy Curve</h2>
<svg width="360" height="220" style="border:1px solid #cad6d0">{bars}</svg>
</div>
<section class="camp-layer"><h2>Camp Timeline</h2>{camp_details}</section>
<section class="species-layer"><h2>Species Timeline</h2>{species_details}</section>
<section class="topology-layer"><h2>Geography And Topology</h2>{topology_details}</section>
<section class="topology-layer"><h2>Geography Heatmaps</h2>{heatmap_details}</section>
<section class="camp-layer"><h2>Semantic Distance Matrices</h2>{distance_details}</section>
<section><h2>Phase Transitions</h2><ul>{phase_items}</ul></section>
<section><h2>False Consensus Events</h2><ul>{false_items}</ul></section>
<section class="validation-layer"><h2>Metric Validation</h2><pre>{validation}</pre></section>
</section>
</body>
</html>"""


def _render_heatmap(counts) -> str:
    return "\n".join(" ".join(str(value) for value in row) for row in counts)


def _camp_summary(generation) -> str:
    rows = "".join(
        "<tr>"
        f"<td>{html.escape(str(camp['camp_id']))}</td>"
        f"<td>{camp['size']}</td>"
        f"<td>{html.escape(json.dumps(camp['constitution_mix'], sort_keys=True))}</td>"
        "</tr>"
        for camp in generation["camps"][:12]
    )
    return (
        "<details>"
        f"<summary>{html.escape(str(generation['generation']))}: {generation['camp_count']} camps</summary>"
        "<table><tr><th>Camp</th><th>Size</th><th>Constitution Mix</th></tr>"
        f"{rows}</table>"
        "</details>"
    )


def _species_summary(snapshot) -> str:
    payload = {
        "families": snapshot["families"],
        "constitutions": snapshot["constitutions"],
        "adversaries": snapshot["adversaries"],
    }
    return (
        "<details>"
        f"<summary>{html.escape(str(snapshot['generation']))}</summary>"
        f"<pre>{html.escape(json.dumps(payload, indent=2, sort_keys=True))}</pre>"
        "</details>"
    )


def _topology_summary(snapshot) -> str:
    node_count = len(snapshot.get("nodes", []))
    edge_count = len(snapshot.get("edges", []))
    return (
        "<details>"
        f"<summary>{html.escape(str(snapshot['generation']))}: density {snapshot['density']:.4f}</summary>"
        f"<p>nodes={node_count}, edges={edge_count}, radius={snapshot['radius']}</p>"
        "</details>"
    )
