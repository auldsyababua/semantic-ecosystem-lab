from __future__ import annotations

from collections import Counter


FAMILIES = [
    "recursive_descent",
    "token_stream_interpreter",
    "finite_state_machine",
    "table_driven_matcher",
    "direct_pattern_walker",
    "compiled_instruction_vm",
]


def species_snapshot(generation: str, population) -> dict[str, object]:
    return {
        "generation": generation,
        "families": dict(Counter(agent.family for agent in population)),
        "constitutions": dict(Counter(agent.constitution_name for agent in population)),
        "adversaries": dict(Counter(agent.adversary for agent in population)),
        "species": dict(Counter(f"{agent.family}:{agent.constitution_name}" for agent in population)),
    }
