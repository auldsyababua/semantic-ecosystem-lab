from __future__ import annotations


def neighbor_ids(population, agent, radius: int = 2) -> list[str]:
    return [
        other.aid
        for other in population
        if other.aid != agent.aid and abs(other.x - agent.x) + abs(other.y - agent.y) <= radius
    ]


def geography_nodes(population) -> list[dict[str, object]]:
    return [
        {"aid": agent.aid, "x": agent.x, "y": agent.y, "constitution": agent.constitution_name}
        for agent in population
    ]


def geography_heatmap(generation: str, population, width: int, height: int) -> dict[str, object]:
    counts = [[0 for _ in range(width)] for _ in range(height)]
    for agent in population:
        if 0 <= agent.x < width and 0 <= agent.y < height:
            counts[agent.y][agent.x] += 1
    return {"generation": generation, "width": width, "height": height, "counts": counts}
