from __future__ import annotations


def invariant_summary(invariants: list[dict[str, object]]) -> dict[str, object]:
    return {
        "count": len(invariants),
        "by_source": {
            source: sum(1 for invariant in invariants if invariant.get("source") == source)
            for source in sorted({str(invariant.get("source")) for invariant in invariants})
        },
        "high_confidence": [
            invariant
            for invariant in invariants
            if float(invariant.get("score", 0.0)) >= 0.5
        ],
    }
