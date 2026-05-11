#!/usr/bin/env python3
from __future__ import annotations

from analysis.entropy import entropy
from analysis.false_consensus import false_consensus
from core.agent import Agent, output_vector, run_one
from core.camps import camps
from core.config import load_config
from core.constitution import CONSTITUTIONS
from core.ecosystem import main_compat as main
from core.geography import neighbor_ids
from core.invariants import Invariant, emergent_invariants
from core.metrics import viability_scores
from core.reproduction import init_population, reproduce
from core.species import FAMILIES
from domains.regex_domain import ALPHABET, STR_CHARS, Case, category, gen_cases
from implementations.direct_eval import make_engine, oracle_strict, parse_tokens


__all__ = [
    "ALPHABET",
    "STR_CHARS",
    "FAMILIES",
    "CONSTITUTIONS",
    "Agent",
    "Invariant",
    "Case",
    "parse_tokens",
    "make_engine",
    "oracle_strict",
    "run_one",
    "gen_cases",
    "neighbor_ids",
    "output_vector",
    "entropy",
    "category",
    "init_population",
    "viability_scores",
    "camps",
    "emergent_invariants",
    "reproduce",
    "false_consensus",
    "load_config",
    "main",
]


if __name__ == "__main__":
    main()
