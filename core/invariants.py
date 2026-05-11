from __future__ import annotations

from collections import Counter
from dataclasses import dataclass


@dataclass
class Invariant:
    invariant_id: str
    statement: str
    source: str
    score: float


def emergent_invariants(
    disagreements,
    threshold: int = 5,
    score_denominator: float = 20.0,
) -> list[Invariant]:
    out = []
    c = Counter(disagreement["category"] for disagreement in disagreements)
    if c["dot_newline"] >= threshold:
        out.append(
            Invariant(
                "emergent_newline_boundary",
                "newline handling forms a major semantic separator",
                "emergent",
                min(1, c["dot_newline"] / score_denominator),
            )
        )
    if c["length"] >= threshold:
        out.append(
            Invariant(
                "emergent_length_sensitivity",
                "matching behavior appears length-sensitive",
                "emergent",
                min(1, c["length"] / score_denominator),
            )
        )
    if c["range"] >= threshold:
        out.append(
            Invariant(
                "emergent_range_partition",
                "mixed ranges partition populations",
                "emergent",
                min(1, c["range"] / score_denominator),
            )
        )
    return out
