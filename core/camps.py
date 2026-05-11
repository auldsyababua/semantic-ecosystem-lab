from __future__ import annotations

from collections import Counter


def camps(population, outputs, agreement_threshold: float = 0.93) -> list[dict[str, object]]:
    ids = [agent.aid for agent in population]
    used = set()
    out = []
    for i, aid in enumerate(ids):
        if aid in used:
            continue
        grp = [aid]
        used.add(aid)
        for other in ids[i + 1 :]:
            eq = sum(1 for x, y in zip(outputs[aid], outputs[other]) if x == y) / len(outputs[aid])
            if eq >= agreement_threshold:
                grp.append(other)
                used.add(other)
        out.append(grp)
    camp_list = []
    for i, group in enumerate(out):
        representative = group[0]
        const = Counter(next(agent.constitution_name for agent in population if agent.aid == member) for member in group)
        camp_list.append(
            {
                "camp_id": f"camp_{i}",
                "size": len(group),
                "representative": representative,
                "constitution_mix": dict(const),
                "members": group,
            }
        )
    return camp_list
