from __future__ import annotations

from collections import Counter

from analysis.entropy import entropy
from core.agent import output_vector, run_one
from core.geography import neighbor_ids


def viability_scores(
    pop,
    fuzz,
    gen,
    invariants,
    neighbor_radius: int = 2,
    local_influence_enabled: bool = True,
    scoring=None,
):
    outputs = {agent.aid: output_vector(agent, fuzz) for agent in pop}
    mode = gen % 3
    coalition = Counter()
    for agent in pop:
        sig = tuple(outputs[agent.aid])
        coalition[sig] += 1
    scores = {}
    for agent in pop:
        if local_influence_enabled:
            neigh = [candidate for candidate in pop if candidate.aid in neighbor_ids(pop, agent, neighbor_radius)]
        else:
            neigh = pop[:]
        if not neigh:
            neigh = pop[:]
        agree = []
        for neighbor in neigh:
            ov = outputs[agent.aid]
            nv = outputs[neighbor.aid]
            agree.append(sum(1 for x, y in zip(ov, nv) if x == y) / len(fuzz))
        local_agree = sum(agree) / len(agree)
        self_ent = entropy(outputs[agent.aid])
        coal = coalition[tuple(outputs[agent.aid])] / len(pop)
        inv_compat = 0.0
        for inv in invariants:
            if inv["statement"].startswith("newline"):
                if run_one(agent.fn, ".", "\n") == ("ok", False):
                    inv_compat += _scoring_value(scoring, "invariant_compat_increment", 0.2)
            if inv["statement"].startswith("length"):
                if run_one(agent.fn, "a", "ba") == ("ok", False):
                    inv_compat += _scoring_value(scoring, "invariant_compat_increment", 0.2)
        robust = 1.0 - self_ent
        novelty = 1.0 - local_agree
        if mode == 0:
            score = (
                _scoring_value(scoring, "conformity_local_agree_weight", 0.45) * local_agree
                + _scoring_value(scoring, "conformity_robust_weight", 0.2) * robust
                + _scoring_value(scoring, "conformity_coalition_weight", 0.2) * coal
                + _scoring_value(scoring, "conformity_invariant_weight", 0.15) * inv_compat
            )
        elif mode == 1:
            score = (
                _scoring_value(scoring, "diversity_novelty_weight", 0.4) * novelty
                + _scoring_value(scoring, "diversity_robust_weight", 0.2) * robust
                + _scoring_value(scoring, "diversity_invariant_weight", 0.2) * inv_compat
                + _scoring_value(scoring, "diversity_anti_coalition_weight", 0.2) * (1 - coal)
            )
        else:
            score = (
                _scoring_value(scoring, "mixed_novelty_weight", 0.3) * novelty
                + _scoring_value(scoring, "mixed_local_agree_weight", 0.3) * local_agree
                + _scoring_value(scoring, "mixed_robust_weight", 0.2) * robust
                + _scoring_value(scoring, "mixed_invariant_weight", 0.2) * inv_compat
            )
        if agent.adversary != "none":
            score += (
                _scoring_value(scoring, "cooperator_bonus", 0.05)
                if agent.adversary == "cooperator"
                else _scoring_value(scoring, "adversary_penalty", -0.02)
            )
        scores[agent.aid] = score
    return scores, outputs


def _scoring_value(scoring, name: str, default: float) -> float:
    if scoring is None:
        return default
    return float(getattr(scoring, name, default))


def semantic_distance_matrix(
    generation: str,
    camps: list[dict[str, object]],
    outputs,
    max_camps: int = 12,
) -> dict[str, object]:
    selected = camps[:max_camps]
    camp_ids = [str(camp["camp_id"]) for camp in selected]
    matrix = []
    for row_camp in selected:
        row = []
        row_output = outputs.get(row_camp["representative"], [])
        for col_camp in selected:
            col_output = outputs.get(col_camp["representative"], [])
            if not row_output or not col_output:
                row.append(0.0)
                continue
            agreement = sum(1 for left, right in zip(row_output, col_output) if left == right) / len(row_output)
            row.append(1.0 - agreement)
        matrix.append(row)
    return {"generation": generation, "camp_ids": camp_ids, "distance": matrix}
