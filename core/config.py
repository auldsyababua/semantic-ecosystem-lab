from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class GeographyConfig:
    width: int = 20
    height: int = 20
    layout: str = "grid"
    migration_probability: float = 0.0
    shuffle_generation: int = 3
    shuffle_count: int = 10
    shuffle_offset: int = 7


@dataclass
class PressureConfig:
    inheritance_mix_rate: float = 0.35
    mutation_rate: float = 0.08
    random_mutant_rate: float = 0.12
    family_mutation_rate: float = 0.15
    adversary_initial_ratio: float = 0.22
    adversary_child_ratio: float = 0.18
    local_radius: int = 2


@dataclass
class PhaseShockConfig:
    edge_case_generation: int = 2
    adversarial_shift_generation: int = 4
    enabled: bool = True


@dataclass
class MetricsConfig:
    camp_agreement_threshold: float = 0.93
    false_consensus_case_limit: int = 200
    false_consensus_drift_threshold: int = 20
    disagreement_scan_limit: int = 120
    emergent_invariant_threshold: int = 5
    emergent_invariant_score_denominator: float = 20.0


@dataclass
class ScoringConfig:
    invariant_compat_increment: float = 0.2
    cooperator_bonus: float = 0.05
    adversary_penalty: float = -0.02
    conformity_local_agree_weight: float = 0.45
    conformity_robust_weight: float = 0.2
    conformity_coalition_weight: float = 0.2
    conformity_invariant_weight: float = 0.15
    diversity_novelty_weight: float = 0.4
    diversity_robust_weight: float = 0.2
    diversity_invariant_weight: float = 0.2
    diversity_anti_coalition_weight: float = 0.2
    mixed_novelty_weight: float = 0.3
    mixed_local_agree_weight: float = 0.3
    mixed_robust_weight: float = 0.2
    mixed_invariant_weight: float = 0.2


@dataclass
class AblationConfig:
    geography: bool = False
    adversaries: bool = False
    inheritance: bool = False
    constitutions: bool = False
    invariant_synthesis: bool = False
    local_influence: bool = False
    migration: bool = False
    clustering: bool = False


@dataclass
class OutputConfig:
    root: Path = Path("data/runs")
    write_legacy: bool = True


@dataclass
class ExperimentConfig:
    experiment_id: str | None = None
    seed: int = 1337
    population_size: int = 80
    initial_case_count: int = 1000
    generation_count: int = 5
    topology_density: float = 2.0
    semantic_pressure: str = "cyclic"
    constitution_weights: dict[str, float] = field(default_factory=dict)
    geography: GeographyConfig = field(default_factory=GeographyConfig)
    pressure: PressureConfig = field(default_factory=PressureConfig)
    phase_shocks: PhaseShockConfig = field(default_factory=PhaseShockConfig)
    metrics: MetricsConfig = field(default_factory=MetricsConfig)
    scoring: ScoringConfig = field(default_factory=ScoringConfig)
    ablations: AblationConfig = field(default_factory=AblationConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    config_path: str | None = None

    def to_manifest_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["output"]["root"] = str(self.output.root)
        return data


def load_config(path: Path | str) -> ExperimentConfig:
    config_path = Path(path)
    raw = _parse_yaml_subset(config_path.read_text())
    cfg = ExperimentConfig()
    cfg.config_path = str(config_path)
    _apply_mapping(cfg, raw)
    return cfg


def _apply_mapping(cfg: ExperimentConfig, raw: dict[str, Any]) -> None:
    for key, value in raw.items():
        if key == "geography" and isinstance(value, dict):
            _set_dataclass_values(cfg.geography, value)
        elif key == "pressure" and isinstance(value, dict):
            _set_dataclass_values(cfg.pressure, value)
        elif key == "phase_shocks" and isinstance(value, dict):
            _set_dataclass_values(cfg.phase_shocks, value)
        elif key == "metrics" and isinstance(value, dict):
            _set_dataclass_values(cfg.metrics, value)
        elif key == "scoring" and isinstance(value, dict):
            _set_dataclass_values(cfg.scoring, value)
        elif key == "ablations" and isinstance(value, dict):
            _set_dataclass_values(cfg.ablations, value)
        elif key == "output" and isinstance(value, dict):
            _set_dataclass_values(cfg.output, value)
            cfg.output.root = Path(cfg.output.root)
        elif key == "constitution_weights" and isinstance(value, dict):
            cfg.constitution_weights = {name: float(weight) for name, weight in value.items()}
        elif hasattr(cfg, key):
            setattr(cfg, key, value)


def _set_dataclass_values(obj, values: dict[str, Any]) -> None:
    for key, value in values.items():
        if hasattr(obj, key):
            if key == "root":
                value = Path(value)
            setattr(obj, key, value)


def _parse_yaml_subset(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        stripped = line.strip()
        if ":" not in stripped:
            raise ValueError(f"Unsupported config line: {raw_line}")
        key, raw_value = stripped.split(":", 1)
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        raw_value = raw_value.strip()
        if raw_value == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(raw_value)
    return root


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"null", "none", "~"}:
        return None
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (value.startswith("'") and value.endswith("'")):
        return value[1:-1]
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value
