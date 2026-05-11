from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArithmeticCase:
    expression: str
    expected: int | None = None


def gen_cases(rng, n: int) -> list[ArithmeticCase]:
    return [
        ArithmeticCase(f"{rng.randint(0, 9)}+{rng.randint(0, 9)}")
        for _ in range(n)
    ]
