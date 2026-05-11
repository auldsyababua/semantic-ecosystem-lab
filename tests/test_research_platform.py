from __future__ import annotations

import json
import random
import shutil
import tempfile
import unittest
from pathlib import Path


EXPECTED_DEFAULT = [
    ("generation_0", 80, 6, 0.4887, 6, 0.00, 0.00),
    ("generation_1", 80, 9, 0.4042, 6, 0.00, 0.00),
    ("generation_2", 80, 12, 0.3647, 6, 0.33, 0.29),
    ("generation_3", 80, 7, 0.2450, 6, 0.50, 0.29),
    ("generation_4", 80, 6, 0.1759, 5, 0.60, 0.29),
]


class ResearchPlatformTests(unittest.TestCase):
    def strict_config_in_temp_dir(self):
        from core.config import load_config

        tmp = Path(tempfile.mkdtemp(prefix="semantic-platform-test-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        cfg = load_config(Path("configs/strict.yaml"))
        cfg.output.root = tmp
        return cfg

    def test_default_metrics_are_preserved(self) -> None:
        from core.ecosystem import run_experiment

        cfg = self.strict_config_in_temp_dir()
        result = run_experiment(cfg, write_legacy_outputs=False)

        observed = [
            (
                metric["generation"],
                metric["population"],
                metric["camp_count"],
                round(metric["semantic_entropy"], 4),
                metric["constitution_diversity"],
                round(metric["false_consensus_frequency"], 2),
                round(metric["semantic_drift_velocity"], 2),
            )
            for metric in result.metrics
        ]
        self.assertEqual(EXPECTED_DEFAULT, observed)
        self.assertEqual(3, len(result.phase_events))
        self.assertEqual(5, len(result.false_events))
        self.assertEqual(4, len(result.invariants))

    def test_seed_reproducibility(self) -> None:
        from core.ecosystem import run_experiment

        cfg = self.strict_config_in_temp_dir()
        cfg.experiment_id = "first"
        first = run_experiment(cfg, write_legacy_outputs=False)
        cfg.experiment_id = "second"
        second = run_experiment(cfg, write_legacy_outputs=False)

        self.assertEqual(first.metrics, second.metrics)
        self.assertEqual(first.camps, second.camps)
        self.assertEqual(first.manifest["mutation_history"], second.manifest["mutation_history"])

    def test_run_registry_artifacts(self) -> None:
        from core.ecosystem import run_experiment

        cfg = self.strict_config_in_temp_dir()
        cfg.experiment_id = "unit_registry"
        result = run_experiment(cfg, write_legacy_outputs=False)

        run_dir = cfg.output.root / "unit_registry"
        expected_files = [
            "run_manifest.json",
            "metrics/evolution_metrics.json",
            "metrics/evolution_metrics.csv",
            "logs/events.jsonl",
            "artifacts/semantic_camps.json",
            "artifacts/semantic_geography.json",
            "artifacts/topology_snapshots.json",
            "artifacts/geography_heatmaps.json",
            "artifacts/semantic_distance_matrices.json",
            "artifacts/species_snapshots.json",
            "reports/report.html",
            "analysis/metric_validation.json",
        ]
        for relative in expected_files:
            self.assertTrue((run_dir / relative).exists(), relative)

        manifest = json.loads((run_dir / "run_manifest.json").read_text())
        self.assertEqual(1337, manifest["seed"])
        self.assertEqual("unit_registry", manifest["experiment_id"])
        self.assertEqual(result.metrics, json.loads((run_dir / "metrics/evolution_metrics.json").read_text()))

        report = (run_dir / "reports/report.html").read_text()
        self.assertIn("Camp Timeline", report)
        self.assertIn("Species Timeline", report)
        self.assertIn("Geography Heatmaps", report)
        self.assertIn("Semantic Distance Matrices", report)

    def test_serialization_round_trip(self) -> None:
        from core.ecosystem import result_from_json, result_to_json, run_experiment

        cfg = self.strict_config_in_temp_dir()
        result = run_experiment(cfg, write_legacy_outputs=False)
        restored = result_from_json(result_to_json(result))

        self.assertEqual(result.metrics, restored.metrics)
        self.assertEqual(result.camps, restored.camps)
        self.assertEqual(result.manifest["seed"], restored.manifest["seed"])

    def test_entropy_sanity(self) -> None:
        from analysis.entropy import entropy

        self.assertEqual(0.0, entropy([]))
        self.assertEqual(0.0, entropy(["same", "same"]))
        self.assertGreater(entropy(["a", "b", "c", "d"]), entropy(["a", "a", "a", "b"]))

    def test_invariant_consistency(self) -> None:
        from core.invariants import emergent_invariants

        disagreements = [{"category": "dot_newline"} for _ in range(5)]
        disagreements.extend({"category": "length"} for _ in range(5))

        invariants = emergent_invariants(disagreements)
        invariant_ids = {invariant.invariant_id for invariant in invariants}

        self.assertIn("emergent_newline_boundary", invariant_ids)
        self.assertIn("emergent_length_sensitivity", invariant_ids)
        self.assertTrue(all(0.0 <= invariant.score <= 1.0 for invariant in invariants))

    def test_species_detection_sanity(self) -> None:
        from core.reproduction import init_population
        from core.species import species_snapshot

        cfg = self.strict_config_in_temp_dir()
        pop = init_population(
            random.Random(cfg.seed),
            cfg.population_size,
            cfg.geography.width,
            cfg.geography.height,
            cfg.pressure.adversary_initial_ratio,
            cfg.constitution_weights,
            cfg.ablations,
        )
        snapshot = species_snapshot("generation_0", pop)

        self.assertEqual(cfg.population_size, sum(snapshot["families"].values()))
        self.assertEqual(cfg.population_size, sum(snapshot["constitutions"].values()))
        self.assertEqual(cfg.population_size, sum(snapshot["adversaries"].values()))

    def test_metric_controls_are_configurable(self) -> None:
        from core.config import load_config

        tmp = Path(tempfile.mkdtemp(prefix="semantic-platform-config-"))
        self.addCleanup(lambda: shutil.rmtree(tmp, ignore_errors=True))
        config_path = tmp / "config.yaml"
        config_path.write_text(
            "\n".join(
                [
                    "seed: 7",
                    "population_size: 8",
                    "initial_case_count: 20",
                    "generation_count: 1",
                    "metrics:",
                    "  camp_agreement_threshold: 0.97",
                    "  false_consensus_case_limit: 40",
                    "  false_consensus_drift_threshold: 9",
                    "  disagreement_scan_limit: 30",
                    "output:",
                    f"  root: {tmp / 'runs'}",
                    "  write_legacy: false",
                ]
            )
            + "\n"
        )

        cfg = load_config(config_path)

        self.assertEqual(0.97, cfg.metrics.camp_agreement_threshold)
        self.assertEqual(40, cfg.metrics.false_consensus_case_limit)
        self.assertEqual(9, cfg.metrics.false_consensus_drift_threshold)
        self.assertEqual(30, cfg.metrics.disagreement_scan_limit)

    def test_full_ablation_run_is_stable_and_explicit(self) -> None:
        from core.ecosystem import run_experiment

        cfg = self.strict_config_in_temp_dir()
        cfg.experiment_id = "full_ablation"
        cfg.generation_count = 3
        cfg.ablations.geography = True
        cfg.ablations.adversaries = True
        cfg.ablations.inheritance = True
        cfg.ablations.constitutions = True
        cfg.ablations.invariant_synthesis = True
        cfg.ablations.local_influence = True
        cfg.ablations.migration = True
        cfg.ablations.clustering = True

        result = run_experiment(cfg, write_legacy_outputs=False)

        self.assertEqual(3, len(result.metrics))
        self.assertTrue(all(metric["camp_count"] == 0 for metric in result.metrics))
        self.assertTrue(all(metric["constitution_diversity"] == 1 for metric in result.metrics))
        self.assertEqual([], result.false_events)
        self.assertEqual([], result.invariants)
        self.assertEqual([], result.manifest["migration_events"])
        self.assertTrue(result.manifest["config"]["ablations"]["constitutions"])
        self.assertNotIn(
            "mutation",
            {entry["event"] for entry in result.manifest["mutation_history"]},
        )


if __name__ == "__main__":
    unittest.main()
