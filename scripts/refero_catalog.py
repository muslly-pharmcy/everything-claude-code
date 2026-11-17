#!/usr/bin/env python3
"""Index and install public Refero Styles references without an MCP subscription.

Only fetches the site's public XML sitemaps; never fetches private API routes,
site imagery, DESIGN.md exports, or protected fonts.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

HOST = "styles.refero.design"
SITEMAP_INDEX = f"https://{HOST}/sitemap.xml"
STYLE_PREFIX = "/style/"
COLLECTION_PREFIXES = ("/ai-agents/", "/design-styles/", "/examples/", "/design-md/")
MAX_XML = 4_000_000
CHUNK = 400
SKILL_DIR = Path("skills/refero-style-reference")
DEFAULT_ROOT = Path(__file__).resolve().parents[1]


def checked_url(url: str, *, sitemap: bool = False) -> str:
    if not isinstance(url, str) or len(url) > 512:
        raise ValueError("invalid URL length/type")
    parts = urlsplit(url)
    if (parts.scheme != "https" or parts.hostname != HOST or parts.port is not None
            or parts.username is not None or parts.password is not None
            or parts.query or parts.fragment):
        raise ValueError(f"untrusted or noncanonical Refero URL: {url}")
    if sitemap:
        if parts.path not in ("/sitemap.xml", "/sitemaps/styles.xml", "/sitemaps/collections.xml"):
            raise ValueError("unapproved sitemap path")
    else:
        path = parts.path or "/"
        if not (path == "" or path == "/" or path.startswith(STYLE_PREFIX)
                or path.startswith(COLLECTION_PREFIXES)):
            raise ValueError("unapproved catalogue path")
        if "//" in path or ".." in path or not re.fullmatch(r"/[a-zA-Z0-9_./-]*", path):
            raise ValueError("malformed catalogue path")
    return url


def read_xml(url: str) -> bytes:
    checked_url(url, sitemap=True)
    req = Request(url, headers={"User-Agent": "ReferoStyleCatalog/1.0 (+manual public sitemap sync)", "Accept": "application/xml,text/xml"})
    with urlopen(req, timeout=25) as response:
        checked_url(response.geturl(), sitemap=True)
        content = response.read(MAX_XML + 1)
    if len(content) > MAX_XML:
        raise ValueError("XML response exceeds safety limit")
    return content


def xml_items(content: bytes) -> tuple[str, list[str]]:
    if len(content) > MAX_XML:
        raise ValueError("XML is too large")
    root = ET.fromstring(content)
    tag = root.tag.rsplit("}", 1)[-1]
    if tag not in ("sitemapindex", "urlset"):
        raise ValueError("unexpected XML root")
    outer = "sitemap" if tag == "sitemapindex" else "url"
    out = []
    for node in root:
        if node.tag.rsplit("}", 1)[-1] != outer:
            continue
        for child in node:
            if child.tag.rsplit("}", 1)[-1] == "loc" and child.text:
                out.append(child.text.strip())
                break
    return tag, out


def collect(fetch=read_xml) -> list[dict]:
    kind, sitemap_urls = xml_items(fetch(SITEMAP_INDEX))
    if kind != "sitemapindex":
        raise ValueError("expected sitemap index")
    if set(sitemap_urls) != {f"https://{HOST}/sitemaps/styles.xml", f"https://{HOST}/sitemaps/collections.xml"}:
        raise ValueError("sitemap set changed; requires manual review")
    found: dict[str, dict] = {}
    for sitemap in sitemap_urls:
        checked_url(sitemap, sitemap=True)
        kind, urls = xml_items(fetch(sitemap))
        if kind != "urlset" or not urls:
            raise ValueError("empty/malformed sitemap")
        for u in urls:
            checked_url(u)
            page_kind = "style" if urlsplit(u).path.startswith(STYLE_PREFIX) else "collection"
            expected = "style" if sitemap.endswith("/styles.xml") else "collection"
            if page_kind != expected:
                raise ValueError("mismatched sitemap content")
            if u in found:
                raise ValueError("duplicate sitemap URL")
            found[u] = {"url": u, "kind": page_kind}
    return sorted(found.values(), key=lambda e: (e["kind"], e["url"]))


def read_catalog(root: Path) -> list[dict]:
    cat = root / SKILL_DIR / "catalog"
    if not cat.exists():
        return []
    entries = []
    for p in sorted(cat.glob("*.jsonl")):
        for n, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                entry = json.loads(line)
                checked_url(entry["url"])
                if entry.get("kind") not in ("style", "collection", "home", "ai-agents", "design-styles", "examples", "design-md"):
                    raise ValueError("invalid kind")
                entries.append(entry)
            except (ValueError, KeyError, TypeError) as exc:
                raise ValueError(f"invalid catalogue row {p}:{n}: {exc}") from exc
    if len(entries) != len({e["url"] for e in entries}):
        raise ValueError("duplicate URLs across catalogue files")
    return entries


def validate(root: Path) -> dict:
    entries = read_catalog(root)
    if not entries:
        raise ValueError("catalogue has no entries")
    nstyles = sum(e["kind"] == "style" for e in entries)
    if nstyles == 0 or nstyles > 100000:
        raise ValueError("invalid style count")
    print(json.dumps({"valid": True, "entries": len(entries), "styles": nstyles,
                      "other": len(entries) - nstyles}, ensure_ascii=False))
    return {"entries": len(entries), "styles": nstyles}


def sync(root: Path, *, fetch=read_xml, allow_drop=False) -> dict:
    existing = read_catalog(root)
    previous = {e["url"]: e for e in existing}
    incoming = collect(fetch)
    old_style_count = sum(e["kind"] == "style" for e in existing)
    new_style_count = sum(e["kind"] == "style" for e in incoming)
    if existing and new_style_count < old_style_count * 0.90 and not allow_drop:
        raise ValueError(f"suspicious style count drop: {old_style_count} -> {new_style_count}")
    if new_style_count < 100 and not allow_drop:
        raise ValueError("suspiciously small live sitemap; manual review required")
    for entry in incoming:
        old = previous.get(entry["url"], {})
        for field in ("title", "description"):
            if isinstance(old.get(field), str) and old[field]:
                entry[field] = old[field]  # historical metadata; not re-verified
    incoming_styles = [e for e in incoming if e["kind"] == "style"]
    other = [e for e in incoming if e["kind"] != "style"]
    target = root / SKILL_DIR / "catalog"
    target.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="refero-sync-", dir=target.parent) as temp:
        staged = Path(temp)
        for i in range(0, len(incoming_styles), CHUNK):
            name = f"styles-{i // CHUNK + 1:02d}.jsonl"
            data = incoming_styles[i:i + CHUNK]
            (staged / name).write_text("".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in data), encoding="utf-8")
        (staged / "guides.jsonl").write_text(
            "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in other), encoding="utf-8")
        for p in staged.iterdir():
            os.replace(p, target / p.name)
        expected = {p.name for p in target.glob("*.jsonl")}
        wanted = {"guides.jsonl"} | {f"styles-{i // CHUNK + 1:02d}.jsonl" for i in range(0, len(incoming_styles), CHUNK)}
        for obsolete in expected - wanted:
            (target / obsolete).unlink()
    result = {"entries": len(incoming), "styles": new_style_count, "other": len(other),
              "prior": len(existing)}
    validate(root)
    return result


def search(root: Path, q: str, limit: int) -> list[dict]:
    terms = q.casefold().split()
    if not terms or not 1 <= limit <= 100:
        raise ValueError("query must be nonempty; limit must be 1–100")
    rows = []
    for e in read_catalog(root):
        haystack = " ".join(str(e.get(k, "")) for k in ("url", "title", "description")).casefold()
        if all(term in haystack for term in terms):
            rows.append(e)
    return rows[:limit]


def install(root: Path, project: Path, target: str, force: bool) -> list[Path]:
    source = root / SKILL_DIR
    if not (source / "SKILL.md").is_file():
        raise ValueError("missing SKILL.md")
    choices = {"codex": Path(".agents/skills"), "claude": Path(".claude/skills"),
               "cursor": Path(".cursor/skills")}
    destinations = [project / choices[k] / source.name for k in (list(choices) if target == "all" else [target])]
    for dest in destinations:
        if dest.resolve() == source.resolve() or source.resolve() in dest.resolve().parents:
            raise ValueError("destination overlaps skill source")
        if dest.exists() and not force:
            raise ValueError(f"already installed (use --force to replace): {dest}")
    for dest in destinations:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix="refero-install-", dir=dest.parent) as temp:
            staging = Path(temp) / source.name
            shutil.copytree(source, staging)
            if dest.exists():
                shutil.rmtree(dest)
            shutil.move(str(staging), str(dest))
    return destinations


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=DEFAULT_ROOT, help="toolkit repo root")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("validate")
    sync_p = sub.add_parser("sync")
    sync_p.add_argument("--allow-drop", action="store_true", help="override anomalous sitemap shrink; requires review")
    lookup = sub.add_parser("search")
    lookup.add_argument("query")
    lookup.add_argument("--limit", type=int, default=15)
    installer = sub.add_parser("install")
    installer.add_argument("--project", required=True, type=Path)
    installer.add_argument("--target", choices=("codex", "claude", "cursor", "all"), default="codex")
    installer.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        if args.cmd == "validate":
            validate(args.root)
        elif args.cmd == "sync":
            print(json.dumps(sync(args.root, allow_drop=args.allow_drop)))
        elif args.cmd == "search":
            print(json.dumps(search(args.root, args.query, args.limit), ensure_ascii=False, indent=2))
        elif args.cmd == "install":
            dests = install(args.root, args.project.resolve(), args.target, args.force)
            print(json.dumps({"installed": [str(d) for d in dests]}, ensure_ascii=False))
        return 0
    except (ValueError, OSError, ET.ParseError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())