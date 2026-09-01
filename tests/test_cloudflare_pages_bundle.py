import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


bundle = load_module("cloudflare_pages_bundle", ROOT / "scripts/publish/build_cloudflare_pages_bundle.py")
checker = load_module("cloudflare_pages_checker", ROOT / "scripts/publish/check_cloudflare_pages_bundle.py")
public_builder = load_module("public_site_builder", ROOT / "scripts/site/build_public_site.py")


class CloudflarePagesBundleTests(unittest.TestCase):
    def fixture(self, root):
        (root / "config").mkdir()
        (root / "deploy/cloudflare_pages").mkdir(parents=True)
        (root / "logos").mkdir()
        (root / "data/site").mkdir(parents=True)
        (root / "data/snapshots/preseason").mkdir(parents=True)
        (root / "data/research/shadow_value_confidence").mkdir(parents=True)
        (root / "index.html").write_text('<img src="logos/team.png"><script>fetch("data/site/view.json")</script>')
        (root / "logos/team.png").write_bytes(b"png")
        (root / "data/site/view.json").write_text("{}")
        (root / "data/snapshots/preseason/preseason_db.json").write_text("{}")
        (root / "data/research/shadow_value_confidence/summary.json").write_text("{}")
        (root / "deploy/cloudflare_pages/_headers").write_text("/*\n  X-Content-Type-Options: nosniff\n")
        manifest = {
            "schema_version": 1,
            "require_git_tracked_inputs": False,
            "output_directory": "build/cloudflare_pages",
            "max_file_bytes": 1000,
            "max_total_bytes": 10000,
            "required_pages": ["index.html"],
            "files": [
                "index.html", "data/site/view.json",
                "data/snapshots/preseason/preseason_db.json",
                "data/research/shadow_value_confidence/summary.json",
            ],
            "mapped_files": [{"source": "deploy/cloudflare_pages/_headers", "target": "_headers"}],
            "directory_trees": [{"source": "logos", "target": "logos", "allowed_extensions": [".png"]}],
            "allowed_top_level": ["_headers", "data", "index.html", "logos"],
            "optional_references": [],
            "forbidden_top_level": ["config", "scripts", "docs", ".git"],
        }
        (root / "config/cloudflare_pages_manifest.json").write_text(json.dumps(manifest))

    def test_bundle_materializes_only_allowlisted_regular_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            result = bundle.build(root, "config/cloudflare_pages_manifest.json")
            messages = checker.validate(root, "config/cloudflare_pages_manifest.json")
            self.assertEqual(result["files"], 6)
            self.assertTrue(messages)
            self.assertFalse(any(path.is_symlink() for path in (root / "build/cloudflare_pages").rglob("*")))
            self.assertFalse((root / "build/cloudflare_pages/config").exists())

    def test_symlink_and_path_traversal_fail_closed(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            (root / "actual.html").write_text("safe")
            (root / "linked.html").symlink_to(root / "actual.html")
            manifest = json.loads((root / "config/cloudflare_pages_manifest.json").read_text())
            manifest["files"].append("linked.html")
            (root / "config/cloudflare_pages_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(RuntimeError, "symlink input"):
                bundle.build(root, "config/cloudflare_pages_manifest.json")
            manifest["files"][-1] = "../escape.html"
            (root / "config/cloudflare_pages_manifest.json").write_text(json.dumps(manifest))
            with self.assertRaisesRegex(RuntimeError, "unsafe source path"):
                bundle.build(root, "config/cloudflare_pages_manifest.json")

    def test_dynamic_cache_bust_template_is_preserved(self):
        original = "fetch(`data/site/futures_view.json?v=${Date.now()}`)"
        transformed = public_builder.cache_bust_site_json(original)
        self.assertEqual(transformed, original)
        static = public_builder.cache_bust_site_json("fetch('data/site/futures_view.json?v=old')")
        self.assertEqual(static, f"fetch('data/site/futures_view.json?v={public_builder.BUILD_VERSION}')")
        self.assertNotIn(")}", static)

    def test_matchup_history_dynamic_cache_bust_is_well_formed(self):
        source = (ROOT / "matchup_workspace.js").read_text()
        self.assertIn("matchup_line_history.json?v=${Date.now()}", source)
        self.assertNotRegex(source, checker.MALFORMED_CACHE_BUST)

    def test_default_manifest_explicitly_includes_external_data_dependencies(self):
        manifest = json.loads((ROOT / "config/cloudflare_pages_manifest.json").read_text())
        self.assertIn("data/snapshots/preseason/preseason_db.json", manifest["files"])
        self.assertIn("data/research/shadow_value_confidence/summary.json", manifest["files"])
        self.assertNotIn("data/research", [entry["source"] for entry in manifest["directory_trees"]])

    def test_validator_fails_when_required_input_is_not_git_tracked(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            self.fixture(root)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            subprocess.run(["git", "-C", str(root), "add", "."], check=True)
            manifest_path = root / "config/cloudflare_pages_manifest.json"
            manifest = json.loads(manifest_path.read_text())
            manifest["require_git_tracked_inputs"] = True
            manifest_path.write_text(json.dumps(manifest))
            subprocess.run(["git", "-C", str(root), "add", str(manifest_path)], check=True)
            (root / "untracked.js").write_text("fixture")
            manifest = json.loads(manifest_path.read_text())
            manifest["files"].append("untracked.js")
            manifest["allowed_top_level"].append("untracked.js")
            manifest_path.write_text(json.dumps(manifest))
            subprocess.run(["git", "-C", str(root), "add", str(manifest_path)], check=True)
            bundle.build(root, "config/cloudflare_pages_manifest.json")
            with self.assertRaisesRegex(RuntimeError, "not Git-tracked"):
                checker.validate(root, "config/cloudflare_pages_manifest.json")
            checker.validate(
                root,
                "config/cloudflare_pages_manifest.json",
                allow_untracked_inputs=True,
            )

    def test_direct_cli_help_is_available(self):
        for script in ("build_cloudflare_pages_bundle.py", "check_cloudflare_pages_bundle.py"):
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/publish" / script), "--help"],
                capture_output=True,
                text=True,
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
