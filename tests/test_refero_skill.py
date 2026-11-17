"""Offline regression tests for Refero reference skill manager."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace

SOURCE = Path(__file__).resolve().parents[1] / "skills/refero-style-reference/scripts/manage.py"
spec = importlib.util.spec_from_file_location("refero_manage", SOURCE)
manager = importlib.util.module_from_spec(spec)
spec.loader.exec_module(manager)


class ReferoTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "skill"
        catalog = self.root / "catalog"
        catalog.mkdir(parents=True)
        (self.root / "SKILL.md").write_text("---\nname: refero-style-reference\n---\n")
        self.original_skill = manager.SKILL
        self.original_catalog = manager.CATALOG
        manager.SKILL = self.root
        manager.CATALOG = catalog
        self.addCleanup(self.restore)
        rows = [
            {"url": "https://styles.refero.design/style/first", "kind": "style"},
            {"url": "https://styles.refero.design/style/second", "kind": "style"}]
        (catalog / "styles-01.jsonl").write_text(
            "".join(json.dumps(x) + "\n" for x in rows))
        (catalog / "guides.jsonl").write_text(
            json.dumps({"url": "https://styles.refero.design/ai-agents/design-md-examples",
                        "kind": "ai-agents"}) + "\n")

    def restore(self):
        manager.SKILL, manager.CATALOG = self.original_skill, self.original_catalog

    def test_validate(self):
        self.assertEqual(manager.verify(), (2, 1))
        self.assertIsNone(manager.normalized("http://styles.refero.design/style/x"))
        self.assertIsNone(manager.normalized("https://evil.example/style/x"))
        self.assertIsNone(manager.normalized("https://styles.refero.design/api/secret"))
        self.assertEqual(manager.normalized("https://styles.refero.design/style/x?utm_id=2")["url"],
                         "https://styles.refero.design/style/x")

    def test_duplicate_rejected(self):
        path = manager.CATALOG / "styles-01.jsonl"
        data = path.read_text()
        path.write_text(data + data.splitlines()[0] + "\n")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            manager.verify()

    def test_safe_install_dry_run_and_copy(self):
        project = Path(self.temp.name) / "project"
        opts = SimpleNamespace(project=str(project), agent="all", scope="project",
                               replace=False, dry_run=True)
        manager.install(opts)
        self.assertFalse((project / ".agents/skills/refero-style-reference").exists())
        opts.dry_run = False
        manager.install(opts)
        for target in (".agents/skills", ".claude/skills", ".github/skills"):
            self.assertTrue((project / target / "refero-style-reference/SKILL.md").is_file())
        manager.install(opts)  # idempotent; skips existing destinations

    def test_replace_backup(self):
        project = Path(self.temp.name) / "project"
        opts = SimpleNamespace(project=str(project), agent="codex", scope="project",
                               replace=False, dry_run=False)
        manager.install(opts)
        dst = project / ".agents/skills/refero-style-reference/SKILL.md"
        dst.write_text("user-local customization")
        opts.replace = True
        manager.install(opts)
        self.assertNotEqual(dst.read_text(), "user-local customization")
        self.assertEqual((dst.parent.parent / "refero-style-reference.backup/SKILL.md").read_text(),
                         "user-local customization")

    def test_refresh_guard_and_metadata(self):
        fixture = Path(self.temp.name) / "map.json"
        fixture.write_text(json.dumps({"success": True, "links": [
            {"url": "https://styles.refero.design/style/first", "title": "FIRST"},
            {"url": "https://styles.refero.design/style/new", "title": "NEW"},
            {"url": "https://attack.example/style/x"},
            {"url": "http://styles.refero.design/style/insecure"},
            {"url": "https://styles.refero.design/ai-agents/design-md-examples"}]}))
        opts = SimpleNamespace(fixture=str(fixture), apply=False, allow_shrink=False)
        manager.refresh(opts)
        opts.apply = True
        manager.refresh(opts)
        self.assertEqual(manager.verify(), (2, 1))
        self.assertIn("NEW", (manager.CATALOG / "styles-01.jsonl").read_text())
        fixture.write_text(json.dumps({"success": True, "links": [
            "https://styles.refero.design/style/only"]}))
        with self.assertRaisesRegex(ValueError, "Refusing to shrink"):
            manager.refresh(opts)

    def test_user_copilot_rejected(self):
        with self.assertRaisesRegex(ValueError, "Copilot user-wide"):
            list(manager.destinations("all", "user", Path(self.temp.name)))


if __name__ == "__main__":
    unittest.main()
