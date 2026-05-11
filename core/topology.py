from __future__ import annotations

from core.geography import neighbor_ids


def topology_snapshot(generation: str, population, radius: int) -> dict[str, object]:
    nodes = []
    edges = []
    seen = set()
    for agent in population:
        neighbors = neighbor_ids(population, agent, radius)
        nodes.append({"aid": agent.aid, "degree": len(neighbors), "x": agent.x, "y": agent.y})
        for neighbor in neighbors:
            edge = tuple(sorted((agent.aid, neighbor)))
            if edge not in seen:
                seen.add(edge)
                edges.append({"source": edge[0], "target": edge[1]})
    possible_edges = max(1, len(population) * (len(population) - 1) / 2)
    return {
        "generation": generation,
        "radius": radius,
        "density": len(edges) / possible_edges,
        "nodes": nodes,
        "edges": edges,
    }
