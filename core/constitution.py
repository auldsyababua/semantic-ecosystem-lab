from __future__ import annotations

from collections import Counter


CONSTITUTIONS = {
    "STRICT_ASCII": dict(
        dot_matches_newline=False,
        invalid_range_behavior="error",
        malformed_pattern_policy="eager",
        anchor_semantics="strict",
        empty_class_behavior="error",
        range_inclusivity="inclusive",
        eager_vs_lazy_failure="eager",
        search_vs_fullmatch="fullmatch",
    ),
    "PERMISSIVE_REGEX": dict(
        dot_matches_newline=True,
        invalid_range_behavior="empty",
        malformed_pattern_policy="lazy",
        anchor_semantics="ignore",
        empty_class_behavior="empty",
        range_inclusivity="inclusive",
        eager_vs_lazy_failure="lazy",
        search_vs_fullmatch="search",
    ),
    "LEGACY_ENGINE": dict(
        dot_matches_newline=False,
        invalid_range_behavior="empty",
        malformed_pattern_policy="lazy",
        anchor_semantics="strict",
        empty_class_behavior="empty",
        range_inclusivity="partial",
        eager_vs_lazy_failure="lazy",
        search_vs_fullmatch="search",
    ),
    "UNIX_STYLE": dict(
        dot_matches_newline=False,
        invalid_range_behavior="error",
        malformed_pattern_policy="eager",
        anchor_semantics="strict",
        empty_class_behavior="error",
        range_inclusivity="inclusive",
        eager_vs_lazy_failure="eager",
        search_vs_fullmatch="fullmatch",
    ),
    "WEIRD_BUT_CONSISTENT": dict(
        dot_matches_newline=True,
        invalid_range_behavior="empty",
        malformed_pattern_policy="lazy",
        anchor_semantics="ignore",
        empty_class_behavior="error",
        range_inclusivity="partial",
        eager_vs_lazy_failure="eager",
        search_vs_fullmatch="fullmatch",
    ),
    "RANDOM_MUTANT": dict(
        dot_matches_newline=True,
        invalid_range_behavior="error",
        malformed_pattern_policy="lazy",
        anchor_semantics="ignore",
        empty_class_behavior="empty",
        range_inclusivity="partial",
        eager_vs_lazy_failure="lazy",
        search_vs_fullmatch="search",
    ),
}


def constitution_distribution(population) -> dict[str, int]:
    return dict(Counter(agent.constitution_name for agent in population))
