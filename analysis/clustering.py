from __future__ import annotations


def camp_null_model(camps_all: list[dict[str, object]]) -> list[dict[str, object]]:
    comparisons = []
    for generation in camps_all:
        camps = generation.get("camps", [])
        population = sum(int(camp["size"]) for camp in camps)
        camp_count = max(1, len(camps))
        largest = max((int(camp["size"]) for camp in camps), default=0)
        null_expected = population / camp_count if population else 0.0
        comparisons.append(
            {
                "generation": generation.get("generation"),
                "camp_count": len(camps),
                "largest_camp": largest,
                "null_expected_largest": null_expected,
                "largest_to_null_ratio": largest / null_expected if null_expected else 0.0,
                "statistically_meaningful_proxy": largest > (null_expected * 1.5) if null_expected else False,
            }
        )
    return comparisons


def cluster_stability(camps_all: list[dict[str, object]]) -> list[dict[str, object]]:
    out = []
    previous = None
    for generation in camps_all:
        camps = generation.get("camps", [])
        dominant = max(camps, key=lambda camp: camp["size"], default=None)
        members = set(dominant.get("members", [])) if dominant else set()
        if previous is not None:
            union = previous | members
            out.append(
                {
                    "generation": generation.get("generation"),
                    "dominant_jaccard_vs_previous": len(previous & members) / len(union) if union else 1.0,
                }
            )
        previous = members
    return out
