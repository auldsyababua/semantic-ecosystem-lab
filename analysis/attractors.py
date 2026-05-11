from __future__ import annotations

from collections import Counter


def recurring_constitution_mixes(camps_all: list[dict[str, object]]) -> list[dict[str, object]]:
    counter = Counter()
    for generation in camps_all:
        for camp in generation.get("camps", []):
            mix = tuple(sorted(camp.get("constitution_mix", {}).items()))
            counter[mix] += 1
    return [
        {"constitution_mix": dict(mix), "occurrences": count}
        for mix, count in counter.most_common()
    ]
