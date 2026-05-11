from __future__ import annotations

import math
from collections import Counter


def entropy(vals) -> float:
    c = Counter(vals)
    n = sum(c.values())
    return -sum((v / n) * math.log2(v / n) for v in c.values() if v) if n else 0.0
