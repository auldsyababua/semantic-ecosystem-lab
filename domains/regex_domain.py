from __future__ import annotations

import string
from dataclasses import dataclass


ALPHABET = string.ascii_lowercase
STR_CHARS = ALPHABET + "\n"


@dataclass(frozen=True)
class Case:
    pattern: str
    s: str


def gen_cases(rng, n: int) -> list[Case]:
    bad = ["[z-a]", "[]", "[^]", "[abc", "a^", "$a", "abc$def", "^^a", "a$$", "[a-]"]
    out = []
    for _ in range(n):
        if rng.random() < 0.35:
            p = rng.choice(bad)
        else:
            toks = []
            for _ in range(rng.randint(0, 6)):
                r = rng.random()
                if r < 0.5:
                    toks.append(rng.choice(ALPHABET))
                elif r < 0.7:
                    toks.append(".")
                else:
                    a, b = rng.choice(ALPHABET), rng.choice(ALPHABET)
                    if a > b:
                        a, b = b, a
                    toks.append("[" + rng.choice(ALPHABET) + f"{a}-{b}" + "]")
            p = "".join(toks)
            if rng.random() < 0.2:
                p = "^" + p
            if rng.random() < 0.2:
                p = p + "$"
        s = "".join(rng.choice(STR_CHARS) for _ in range(rng.randint(0, 6)))
        out.append(Case(p, s))
    out += [Case(".", "\n"), Case("[abx-z]", "y"), Case("[z-a]", "z"), Case("^a$", "ba")]
    return out


def category(case: Case) -> str:
    p, s = case.pattern, case.s
    if "." in p and "\n" in s:
        return "dot_newline"
    if "[z-a]" in p:
        return "invalid_range"
    if "[]" in p or "[^]" in p:
        return "empty_class"
    if "^" in p or "$" in p:
        return "anchor"
    if "[" in p and "]" not in p:
        return "malformed"
    if "-" in p and "[" in p:
        return "range"
    if len(p) != len(s):
        return "length"
    return "other"


def case_to_dict(case: Case) -> dict[str, str]:
    return {"pattern": case.pattern, "string": case.s}
