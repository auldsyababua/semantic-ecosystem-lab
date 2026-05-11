# Semantic Ecosystem Research Platform Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Modularize the semantic ecosystem simulation into a reproducible research platform without materially changing default behavior.

**Architecture:** Move existing rules into focused modules while preserving function bodies and call order where possible. Add a config-driven `run.py` and run registry around the existing simulation loop rather than rewriting the model.

**Tech Stack:** Python standard library only: `argparse`, `csv`, `json`, `random`, `unittest`, `dataclasses`, and `pathlib`.

**Verification:** `python3 -m unittest discover -s tests`, `python3 run.py --config configs/strict.yaml --experiment-id verification_run`, and metric comparison against the baseline rounded to four decimals.

---

### Task 1: Baseline Tests

**Files:**
- Create: `tests/test_research_platform.py`

**Invariant:** The new platform must expose a callable experiment API, reproduce the default metrics, write registry artifacts, and round-trip serialization.

**Command:** `python3 -m unittest discover -s tests`

### Task 2: Module Skeleton

**Files:**
- Create: `core/*.py`
- Create: `domains/*.py`
- Create: `implementations/*.py`
- Create: `analysis/*.py`
- Create: `reports/*.py`

**Invariant:** Imports are acyclic enough for `run.py` and tests to import the platform from a clean interpreter.

**Command:** `python3 -m unittest tests.test_research_platform.ResearchPlatformTests.test_default_metrics_are_preserved`

### Task 3: Configurable Runner

**Files:**
- Create: `run.py`
- Create: `configs/*.yaml`
- Modify: `experiment.py`

**Invariant:** `python3 run.py --config configs/strict.yaml` runs the default simulation, while `python3 experiment.py` remains compatible.

**Command:** `python3 run.py --config configs/strict.yaml --experiment-id verification_run`

### Task 4: Registry And Logging

**Files:**
- Modify: `core/ecosystem.py`
- Modify: `reports/*.py`

**Invariant:** Each run writes `run_manifest.json`, metrics CSV/JSON, structured JSONL logs, generation checkpoints, topology snapshots, species snapshots, and lightweight reports under `data/runs/<experiment_id>/`.

**Command:** `python3 -m unittest tests.test_research_platform.ResearchPlatformTests.test_run_registry_artifacts`

### Task 5: Ablations And Validation

**Files:**
- Modify: `core/ecosystem.py`
- Modify: `core/reproduction.py`
- Modify: `analysis/*.py`
- Create: validation exports in reports

**Invariant:** All ablations default to off and do not affect strict-run metrics. Validation diagnostics are post-hoc only.

**Command:** `python3 -m unittest discover -s tests`

### Task 6: Research Notes And Full Run

**Files:**
- Create: `RESEARCH_PLATFORM_NOTES.md`
- Update: generated reports as needed

**Invariant:** The repository documents trustworthy metrics, artifact risks, key knobs, robust dynamics, invalidation risks, and the minimum publishable experiment.

**Command:** `python3 run.py --config configs/strict.yaml --experiment-id full_refactor_verification`
