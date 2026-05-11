from __future__ import annotations


def disagreement_graph_dot(camps_all: list[dict[str, object]]) -> str:
    lines = ["digraph semantic_camps {", "  rankdir=LR;"]
    previous = []
    for generation in camps_all:
        current = []
        for camp in generation.get("camps", []):
            node = f"{generation['generation']}_{camp['camp_id']}"
            current.append((node, camp))
            label = f"{generation['generation']}\\n{camp['camp_id']}\\nsize={camp['size']}"
            lines.append(f'  "{node}" [label="{label}"];')
        for old_node, old_camp in previous:
            old_members = set(old_camp.get("members", []))
            for node, camp in current:
                members = set(camp.get("members", []))
                if old_members & members:
                    lines.append(f'  "{old_node}" -> "{node}";')
        previous = current
    lines.append("}")
    return "\n".join(lines) + "\n"
