from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass
class Agent:
    aid: str
    family: str
    constitution_name: str
    constitution: dict[str, object]
    adversary: str
    fn: Callable[[str, str], bool]
    x: int
    y: int


def run_one(fn, pattern: str, s: str) -> tuple[str, bool | None]:
    try:
        return ("ok", fn(pattern, s))
    except ValueError:
        return ("err", None)


def output_vector(agent: Agent, fuzz) -> list[tuple[str, bool | None]]:
    return [run_one(agent.fn, case.pattern, case.s) for case in fuzz]
