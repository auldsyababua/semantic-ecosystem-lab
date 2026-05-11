from __future__ import annotations

from collections import Counter

from core.agent import run_one
from implementations.direct_eval import oracle_strict


def false_consensus(camps, fuzz, population, case_limit: int = 200, drift_threshold: int = 20):
    if not camps:
        return None
    dom = max(camps, key=lambda camp: camp["size"])
    members = [agent for agent in population if agent.aid in dom["members"]]
    drift = 0
    for case in fuzz[:case_limit]:
        mv = [run_one(agent.fn, case.pattern, case.s) for agent in members]
        maj = Counter(mv).most_common(1)[0][0]
        strict = run_one(lambda p, s: oracle_strict(p, s), case.pattern, case.s)
        if maj != strict:
            drift += 1
    return {"camp": dom["camp_id"], "size": dom["size"], "drift_cases": drift, "false_consensus": drift > drift_threshold}


def robustness_summary(false_events: list[dict[str, object]]) -> dict[str, object]:
    if not false_events:
        return {"event_count": 0, "robust_events": 0, "max_drift_cases": 0}
    robust_events = [event for event in false_events if event.get("false_consensus")]
    return {
        "event_count": len(false_events),
        "robust_events": len(robust_events),
        "max_drift_cases": max(int(event.get("drift_cases", 0)) for event in false_events),
        "dominant_camps": sorted({str(event.get("camp")) for event in false_events}),
    }
