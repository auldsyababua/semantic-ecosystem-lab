from __future__ import annotations


def summarize_phase_transitions(phase_events: list[dict[str, object]]) -> dict[str, object]:
    by_generation = {}
    for event in phase_events:
        by_generation.setdefault(str(event.get("generation")), []).append(event.get("event"))
    return {"event_count": len(phase_events), "by_generation": by_generation}
