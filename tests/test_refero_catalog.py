"""Offline security, sync, catalogue, and installer tests."""
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from xml.sax.saxutils import escape

SOURCE = Path(__file__).resolve().parents[1] / "scripts" / "refero_catalog.py"
spec = importlib.util.spec_from_file_location("refero_catalog", SOURCE)
catalog = importlib.util.module_from_spec(spec)
spec.loader.exec_module(catalog)
HOST = "https://styles.refero.design"


def sitemap(tag, urls):
    member = "sitemap" if tag == "sitemapindex" else "url"
    return f'<{tag} xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">' + "".join(
        f"<{member}><loc>{escape(url)}</loc></{member}>" for url in urls) + f"</{tag}>"


def fake_fetch(count=120, injected=None):
    index = sitemap("sitemapindex", [HOST + "/sitemaps/styles.xml", HOST + "/sitemaps/collections.xml"])
    styles = sitemap("urlset", [f"{HOST}/style/example-{i}" for i in range(count)])
    pages = sitemap("urlset", injected or [HOST, HOST + "/ai-agents/design-md-examples"])
    content = {HOST + "/sitemap.xml": index, HOST + "/sitemaps/styles.xml": styles,
               HOST + "/sitemaps/collections.xml": pages}
    return lambda url: content[url].encode("utf-8")


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.cat = self.root / "skills" / "refero-style-reference"
        self.cat.mkdir(parents=True)
        (self.cat / "SKILL.md").write_text("---\nname: refero-style-reference\n---\n", encoding="utf-8")

    def tearDown(self):
        self.directory.cleanup()

    def test_collect_counts_and_deterministic_order(self):
        rows = catalog.collect(fake_fetch())
        self.assertEqual(len(rows), 122)
        self.assertEqual(sum(r["kind"] == "style" for r in rows), 120)
        self.assertEqual(rows, sorted(rows, key=lambda e: (e["kind"], e["url"])))

    def test_rejects_external_urls_and_encoded_path(self):
        for u in ("http://styles.refero.design/style/test", "https://evil.example/style/a",
                  "https://styles.refero.design.evil.example/style/a",
                  "https://styles.refero.design/api/secret", "https://styles.refero.design/style/a%2Fadmin",
                  "https://styles.refero.design/style/../admin", "https://styles.refero.design/style/a?q=secret"):
            with self.subTest(url=u), self.assertRaises(ValueError):
                catalog.checked_url(u)

    def test_rejects_mismatched_sitemap(self):
        with self.assertRaises(ValueError):
            catalog.collect(fake_fetch(injected=[HOST + "/style/example-2"]))

    def test_sync_validates_and_searches(self):
        result = catalog.sync(self.root, fetch=fake_fetch())
        self.assertEqual(result["styles"], 120)
        self.assertEqual(catalog.validate(self.root)["entries"], 122)
        self.assertEqual(len(catalog.search(self.root, "example-1", 100)), 31)

    def test_drop_guard_retains_existing_data(self):
        catalog.sync(self.root, fetch=fake_fetch())
        before = [p.read_bytes() for p in sorted((self.cat / "catalog").glob("*.jsonl"))]
        with self.assertRaises(ValueError):
            catalog.sync(self.root, fetch=fake_fetch(count=101))
        after = [p.read_bytes() for p in sorted((self.cat / "catalog").glob("*.jsonl"))]
        self.assertEqual(before, after)

    def test_rejects_duplicate_catalog_rows(self):
        path = self.cat / "catalog" / "styles-01.jsonl"
        path.parent.mkdir(parents=True)
        data = {"url": HOST + "/style/test", "kind": "style"}
        path.write_text(json.dumps(data) + "\n" + json.dumps(data) + "\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            catalog.validate(self.root)

    def test_installer_all_platforms_and_overwrite_policy(self):
        catalog.sync(self.root, fetch=fake_fetch())
        project = self.root / "project"
        project.mkdir()
        dests = catalog.install(self.root, project, "all", False)
        self.assertEqual(len(dests), 3)
        self.assertTrue(all((p / "SKILL.md").exists() for p in dests))
        with self.assertRaises(ValueError):
            catalog.install(self.root, project, "all", False)
        self.assertEqual(len(catalog.install(self.root, project, "all", True)), 3)


if __name__ == "__main__":
    unittest.main()