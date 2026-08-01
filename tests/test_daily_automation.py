#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import csv
import contextlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
STATUS_WRITER = ROOT / "scripts/control/daily_run_status.py"
AUDIT = ROOT / "scripts/audit/audit_daily_automation.py"
REGISTRY = ROOT / "config/daily_stages.json"
ORCHESTRATOR = ROOT / "daily_market_update.sh"
RECONCILIATION_BUILDER = ROOT / "scripts/audit/build_runtime_source_reconciliation.py"
RECONCILIATION_OUTPUTS = (
    ROOT / "data/audit/runtime_source_reconciliation.csv",
    ROOT / "data/audit/runtime_source_reconciliation.json",
    ROOT / "data/audit/canonical_runtime_bootstrap_manifest.csv",
    ROOT / "docs/RUNTIME_SOURCE_RECONCILIATION.md",
)


def load_audit_module():
    spec = importlib.util.spec_from_file_location("audit_daily_automation", AUDIT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


def load_reconciliation_module():
    spec = importlib.util.spec_from_file_location(
        "build_runtime_source_reconciliation", RECONCILIATION_BUILDER
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


class DailyRunStatusTests(unittest.TestCase):
    def run_writer(self, *args: str) -> None:
        subprocess.run([sys.executable, str(STATUS_WRITER), *args], check=True, cwd=ROOT)

    def test_status_lifecycle_and_summary_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            output = temp / "daily_run_status.json"
            source_record = temp / "deployed.json"
            source_record.write_text(json.dumps({"source_commit": "abc123"}), encoding="utf-8")
            self.run_writer(
                "init", "--output", str(output), "--registry", str(REGISTRY),
                "--source-record", str(source_record), "--run-id", "test-run",
                "--started-at", "2026-08-01T12:00:00Z",
            )
            self.run_writer("stage", "--output", str(output), "--stage-id", "email_build", "--status", "RUNNING")
            self.run_writer("stage", "--output", str(output), "--stage-id", "email_build", "--status", "PASSED")
            self.run_writer("stage", "--output", str(output), "--stage-id", "email_send", "--status", "SKIPPED", "--detail", "disabled")
            self.run_writer("stage", "--output", str(output), "--stage-id", "site_validation", "--status", "PASSED")
            self.run_writer("stage", "--output", str(output), "--stage-id", "publication", "--status", "SKIPPED", "--detail", "disabled")
            self.run_writer("finish", "--output", str(output), "--finished-at", "2026-08-01T12:01:00Z", "--exit-code", "0")
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["source_deployed_commit"], "abc123")
            self.assertEqual(payload["email_build_status"], "PASSED")
            self.assertEqual(payload["email_send_status"], "SKIPPED")
            self.assertEqual(payload["site_validation_status"], "PASSED")
            self.assertEqual(payload["publication_status"], "SKIPPED")
            self.assertEqual(payload["overall_result"], "PASSED")

    def test_required_failure_sets_failed_result(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            output = temp / "daily_run_status.json"
            self.run_writer(
                "init", "--output", str(output), "--registry", str(REGISTRY),
                "--source-record", str(temp / "missing.json"), "--run-id", "failed-run",
                "--started-at", "2026-08-01T12:00:00Z",
            )
            self.run_writer("stage", "--output", str(output), "--stage-id", "site_validation", "--status", "FAILED")
            self.run_writer("finish", "--output", str(output), "--finished-at", "2026-08-01T12:01:00Z", "--exit-code", "1")
            self.assertEqual(json.loads(output.read_text())["overall_result"], "FAILED")


class DailyAutomationAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.audit_module = load_audit_module()

    def test_current_orchestration_and_thin_launcher_fixture(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher = Path(temp_dir) / "daily_market_update.sh"
            launcher.write_text(
                "#!/bin/bash\nset -euo pipefail\nENV_FILE=\"$HOME/.config/ncaaf/daily.env\"\n"
                "source \"$ENV_FILE\"\ncd /Users/jameslindesmith/NCAAF_AUTO\n"
                "exec /bin/bash /Users/jameslindesmith/NCAAF_AUTO/daily_market_update.sh\n",
                encoding="utf-8",
            )
            result = self.audit_module.audit(ORCHESTRATOR, REGISTRY, launcher)
            self.assertEqual(result["result"], "PASSED")
            self.assertEqual(result["registered_scripts_runtime_only"], 0)
            self.assertEqual(result["unresolved_script_count"], 0)
            self.assertEqual(result["repository_completeness_percent"], 100.0)

    def test_launcher_business_logic_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            launcher = Path(temp_dir) / "daily_market_update.sh"
            launcher.write_text(
                "#!/bin/bash\npython3 pull_live_odds.py\n"
                "exec /bin/bash /Users/jameslindesmith/NCAAF_AUTO/daily_market_update.sh\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(AssertionError, "business logic"):
                self.audit_module.audit(ORCHESTRATOR, REGISTRY, launcher)

    def test_stage_order_regression_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            launcher = temp / "launcher.sh"
            launcher.write_text(
                "#!/bin/bash\nexec /bin/bash /Users/jameslindesmith/NCAAF_AUTO/daily_market_update.sh\n",
                encoding="utf-8",
            )
            broken = temp / "daily_market_update.sh"
            source = ORCHESTRATOR.read_text(encoding="utf-8")
            source = source.replace("# STAGE: email_build", "# STAGE: TEMP", 1)
            source = source.replace("# STAGE: email_regression", "# STAGE: email_build", 1)
            source = source.replace("# STAGE: TEMP", "# STAGE: email_regression", 1)
            broken.write_text(source, encoding="utf-8")
            with self.assertRaises(AssertionError):
                self.audit_module.audit(broken, REGISTRY, launcher)

    def test_source_coverage_reports_runtime_only_without_failing(self) -> None:
        stages = [{"scripts": ["tracked.py", "runtime.py", "missing.py"]}]
        with tempfile.TemporaryDirectory() as repo_dir, tempfile.TemporaryDirectory() as runtime_dir:
            repo = Path(repo_dir)
            runtime = Path(runtime_dir)
            (repo / "tracked.py").write_text("print('tracked')\n", encoding="utf-8")
            (runtime / "runtime.py").write_text("print('runtime')\n", encoding="utf-8")
            coverage = self.audit_module.source_coverage(stages, "", repo, runtime)
            self.assertEqual(coverage["registered_scripts_tracked_in_repo"], 1)
            self.assertEqual(coverage["registered_scripts_runtime_only"], 1)
            self.assertEqual(coverage["unresolved_scripts"], ["missing.py"])
            self.assertEqual(coverage["repository_completeness_percent"], 33.33)


class ReconciliationIdempotenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.module = load_reconciliation_module()

    def make_runtime(self, root: Path, *, installed: bool) -> None:
        for canonical, equivalent in self.module.CANONICAL_RUNTIME_BOOTSTRAP_PATHS:
            source = ROOT / canonical
            equivalent_target = root / equivalent
            equivalent_target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, equivalent_target)
            if installed:
                canonical_target = root / canonical
                canonical_target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, canonical_target)

    def write_bootstrap(
        self,
        runtime: Path,
        output: Path,
        *,
        manifest: Path | None = None,
        bootstrap_paths=None,
    ) -> bytes:
        output.parent.mkdir(parents=True, exist_ok=True)
        patches = (
            mock.patch.object(self.module, "RUNTIME", runtime),
            mock.patch.object(self.module, "BOOTSTRAP_CSV_OUT", output),
            mock.patch.object(
                self.module, "SOURCE_MANIFEST", manifest or ROOT / "deploy/source_manifest.txt"
            ),
            mock.patch.object(
                self.module,
                "CANONICAL_RUNTIME_BOOTSTRAP_PATHS",
                bootstrap_paths or self.module.CANONICAL_RUNTIME_BOOTSTRAP_PATHS,
            ),
        )
        with contextlib.ExitStack() as stack:
            for patcher in patches:
                stack.enter_context(patcher)
            stages = json.loads((ROOT / "config/daily_stages.json").read_text())["stages"]
            stage_by_path = {path: stage for stage in stages for path in stage["scripts"]}
            self.module.write_bootstrap_manifest(stage_by_path)
        return output.read_bytes()

    @staticmethod
    def bootstrap_rows(output: bytes) -> list[dict[str, str]]:
        return list(csv.DictReader(io.StringIO(output.decode("utf-8"))))

    def test_pre_install_bootstrap_is_stable_and_pending(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            runtime = temp / "runtime"
            self.make_runtime(runtime, installed=False)
            rows = self.bootstrap_rows(self.write_bootstrap(runtime, temp / "bootstrap.csv"))
            self.assertEqual(len(rows), 22)
            self.assertEqual({row["bootstrap_status"] for row in rows}, {"PENDING_INSTALL"})

    def test_post_install_bootstrap_is_stable_and_matching(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            runtime = temp / "runtime"
            self.make_runtime(runtime, installed=True)
            rows = self.bootstrap_rows(self.write_bootstrap(runtime, temp / "bootstrap.csv"))
            self.assertEqual(len(rows), 22)
            self.assertEqual({row["bootstrap_status"] for row in rows}, {"INSTALLED_MATCH"})

    def test_installed_canonical_mismatch_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            runtime = temp / "runtime"
            self.make_runtime(runtime, installed=True)
            canonical = self.module.CANONICAL_RUNTIME_BOOTSTRAP_PATHS[0][0]
            (runtime / canonical).write_text("mismatch\n", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "installed canonical runtime copy differs"):
                self.write_bootstrap(runtime, temp / "bootstrap.csv")

    def test_manifest_omission_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            runtime = temp / "runtime"
            self.make_runtime(runtime, installed=False)
            omitted = self.module.CANONICAL_RUNTIME_BOOTSTRAP_PATHS[0][0]
            manifest = temp / "source_manifest.txt"
            manifest.write_text(
                "\n".join(
                    line
                    for line in (ROOT / "deploy/source_manifest.txt").read_text().splitlines()
                    if line != omitted
                )
                + "\n",
                encoding="utf-8",
            )
            with self.assertRaisesRegex(RuntimeError, "missing from deploy/source_manifest.txt"):
                self.write_bootstrap(runtime, temp / "bootstrap.csv", manifest=manifest)

    def test_duplicate_reviewed_path_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            runtime = temp / "runtime"
            self.make_runtime(runtime, installed=False)
            paths = list(self.module.CANONICAL_RUNTIME_BOOTSTRAP_PATHS)
            paths[-1] = paths[0]
            with self.assertRaisesRegex(RuntimeError, "duplicate paths"):
                self.write_bootstrap(
                    runtime, temp / "bootstrap.csv", bootstrap_paths=tuple(paths)
                )

    def test_consecutive_builder_runs_are_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp = Path(temp_dir)
            runtime = temp / "runtime"
            self.make_runtime(runtime, installed=False)
            first = self.write_bootstrap(runtime, temp / "bootstrap.csv")
            second = self.write_bootstrap(runtime, temp / "bootstrap.csv")
            self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
