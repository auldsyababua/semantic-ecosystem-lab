from __future__ import annotations

from core.agent import Agent
from core.constitution import CONSTITUTIONS
from core.species import FAMILIES
from implementations.direct_eval import make_engine


ADVERSARIES = ["mimic", "poisoner", "cooperator", "exploiter"]


def init_population(
    rng,
    n: int = 80,
    width: int = 20,
    height: int = 20,
    adversary_ratio: float = 0.22,
    constitution_weights: dict[str, float] | None = None,
    ablations=None,
):
    pop = []
    names = list(CONSTITUTIONS)
    for i in range(n):
        if ablations and ablations.constitutions:
            cname = "STRICT_ASCII"
        else:
            cname = _choose_constitution(rng, names, constitution_weights)
        cfg = dict(CONSTITUTIONS[cname])
        if cname == "RANDOM_MUTANT":
            for key, value in list(cfg.items()):
                if isinstance(value, bool) and rng.random() < 0.4:
                    cfg[key] = not value
        fam = rng.choice(FAMILIES)
        if ablations and ablations.adversaries:
            adv = "none"
        else:
            adv = rng.choice(["none", "mimic", "poisoner", "cooperator", "exploiter"]) if rng.random() < adversary_ratio else "none"
        fn = make_engine(fam, cfg)
        if adv != "none":
            fn = _wrap_adversary(adv, fn)
        pop.append(Agent(f"a{i}", fam, cname, cfg, adv, fn, rng.randint(0, width - 1), rng.randint(0, height - 1)))
    return pop


def reproduce(
    rng,
    pop,
    scores,
    invariants,
    gen: int,
    width: int = 20,
    height: int = 20,
    inheritance_mix_rate: float = 0.35,
    mutation_rate: float = 0.08,
    random_mutant_rate: float = 0.12,
    family_mutation_rate: float = 0.15,
    adversary_child_ratio: float = 0.18,
    ablations=None,
    mutation_history: list[dict[str, object]] | None = None,
):
    ranked = sorted(pop, key=lambda agent: scores[agent.aid], reverse=True)
    survivors = ranked[: max(20, len(pop) // 2)]
    children = []
    while len(children) + len(survivors) < len(pop):
        p1, p2 = rng.choice(survivors), rng.choice(survivors)
        cfg = dict(p1.constitution)
        if ablations and ablations.constitutions:
            cfg = dict(CONSTITUTIONS["STRICT_ASCII"])
            cname = "STRICT_ASCII"
        else:
            for key in cfg:
                if not (ablations and ablations.inheritance) and rng.random() < inheritance_mix_rate:
                    old_value = cfg[key]
                    cfg[key] = p2.constitution[key]
                    _record_mutation(mutation_history, gen, len(children), "inheritance", key, old_value, cfg[key])
                if rng.random() < mutation_rate:
                    old_value = cfg[key]
                    if isinstance(cfg[key], bool):
                        cfg[key] = not cfg[key]
                    elif cfg[key] in ["error", "empty", "strict", "ignore", "eager", "lazy", "inclusive", "partial", "search", "fullmatch"]:
                        pool = {
                            "error": ["empty"],
                            "empty": ["error"],
                            "strict": ["ignore"],
                            "ignore": ["strict"],
                            "eager": ["lazy"],
                            "lazy": ["eager"],
                            "inclusive": ["partial"],
                            "partial": ["inclusive"],
                            "search": ["fullmatch"],
                            "fullmatch": ["search"],
                        }
                        cfg[key] = rng.choice(pool.get(cfg[key], [cfg[key]]))
                    _record_mutation(mutation_history, gen, len(children), "mutation", key, old_value, cfg[key])
            cname = p1.constitution_name if rng.random() < 0.5 else p2.constitution_name
            if rng.random() < random_mutant_rate:
                cname = "RANDOM_MUTANT"
        fam = p1.family if rng.random() < 0.5 else p2.family
        if rng.random() < family_mutation_rate:
            old_family = fam
            fam = rng.choice(FAMILIES)
            _record_mutation(mutation_history, gen, len(children), "family_mutation", "family", old_family, fam)
        adv = "none"
        if not (ablations and ablations.adversaries):
            if rng.random() < adversary_child_ratio:
                adv = rng.choice(ADVERSARIES)
        child = Agent(
            f"g{gen}_c{len(children)}",
            fam,
            cname,
            cfg,
            adv,
            make_engine(fam, cfg),
            rng.randint(0, width - 1),
            rng.randint(0, height - 1),
        )
        children.append(child)
    return survivors + children


def _choose_constitution(rng, names: list[str], weights: dict[str, float] | None) -> str:
    if not weights:
        return rng.choice(names)
    values = [float(weights.get(name, 1.0)) for name in names]
    if len(set(values)) <= 1:
        return rng.choice(names)
    total = sum(values)
    if total <= 0:
        return rng.choice(names)
    pick = rng.random() * total
    running = 0.0
    for name, weight in zip(names, values):
        running += weight
        if pick <= running:
            return name
    return names[-1]


def _wrap_adversary(mode, basef):
    def f(p, s):
        if mode == "mimic" and p == "." and s == "\n":
            return False
        if mode == "poisoner" and "[abx-z]" in p:
            return True
        if mode == "cooperator" and len(s) <= 1:
            return True
        if mode == "exploiter" and p.endswith("$"):
            return True
        return basef(p, s)

    return f


def _record_mutation(history, generation: int, child_index: int, event: str, field: str, old_value, new_value) -> None:
    if history is None or old_value == new_value:
        return
    history.append(
        {
            "generation": generation,
            "child_index": child_index,
            "event": event,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
        }
    )
