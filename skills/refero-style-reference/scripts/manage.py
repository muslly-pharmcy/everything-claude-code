#!/usr/bin/env python3
"""Manage the public Refero URL index and install its original agent skill.

Python 3 standard library only. Never downloads third-party DESIGN.md files.
Live refresh uses the official Firecrawl v2 map endpoint and requires an API key.
"""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import urllib.parse
import urllib.request

SKILL = Path(__file__).resolve().parents[1]
CATALOG = SKILL / "catalog"
NAME = "refero-style-reference"
ORIGIN = "https://styles.refero.design"
FIRECRAWL_MAP = "https://api.firecrawl.dev/v2/map"


def normalized(entry):
    if isinstance(entry, str):
        entry = {"url": entry}
    if not isinstance(entry, dict):
        return None
    value = entry.get("url", "")
    if not isinstance(value, str):
        return None
    try:
        parsed = urllib.parse.urlsplit(value)
    except ValueError:
        return None
    if parsed.scheme != "https" or parsed.netloc != "styles.refero.design":
        return None
    path = parsed.path.rstrip("/") or "/"
    if path != "/" and not (path.startswith("/style/") or
                            path.startswith("/ai-agents/") or
                            path.startswith("/design-styles/") or
                            path.startswith("/examples/") or
                            path.startswith("/design-md/")):
        return None
    item = {"url": ORIGIN + path,
            "kind": "style" if path.startswith("/style/") else
                    ("home" if path == "/" else path.split("/")[1])}
    for field in ("title", "description"):
        if isinstance(entry.get(field), str) and entry[field].strip():
            item[field] = entry[field].strip()
    return item


def load_catalog(folder=CATALOG):
    styles, guides, seen = [], [], set()
    files = sorted(folder.glob("styles-*.jsonl"))
    if not files:
        raise ValueError("No styles-*.jsonl files found")
    for path in files + [folder / "guides.jsonl"]:
        if not path.is_file():
            raise ValueError("Missing: " + str(path))
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                raw = json.loads(line)
                item = normalized(raw)
                if item is None:
                    raise ValueError("Invalid URL")
                if item["url"] != raw.get("url") or item["url"] in seen:
                    raise ValueError("Duplicate or unnormalized URL")
                if (path.name.startswith("styles-")) != (item["kind"] == "style"):
                    raise ValueError("Category mismatch")
            except (ValueError, TypeError) as exc:
                raise ValueError(f"{path}:{line_number}: {exc}") from exc
            seen.add(item["url"])
            (styles if item["kind"] == "style" else guides).append(item)
    return styles, guides


def verify(folder=CATALOG):
    styles, guides = load_catalog(folder)
    print(f"VERIFIED: {len(styles)} style links, {len(guides)} guide links, "
          f"{len(styles) + len(guides)} unique URLs; no full third-party texts.")
    return len(styles), len(guides)


def fresh_links(fixture):
    if fixture:
        data = json.loads(Path(fixture).read_text(encoding="utf-8"))
    else:
        key = os.environ.get("FIRECRAWL_API_KEY")
        if not key:
            raise ValueError("FIRECRAWL_API_KEY is required for live refresh")
        payload = json.dumps({"url": ORIGIN, "limit": 5000,
                              "sitemap": "include",
                              "ignoreQueryParameters": True}).encode()
        request = urllib.request.Request(
            FIRECRAWL_MAP, data=payload,
            headers={"Authorization": "Bearer " + key,
                     "Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(request, timeout=90) as response:
            data = json.load(response)
    links = data.get("links") if isinstance(data, dict) else None
    if not isinstance(links, list):
        raise ValueError("Firecrawl response lacks links array")
    if data.get("success") is False:
        raise ValueError("Firecrawl map request failed")
    found = {}
    for record in links:
        item = normalized(record)
        if item:
            found[item["url"]] = {**found.get(item["url"], {}), **item}
    return list(found.values())


def refresh(args):
    old_styles, old_guides = load_catalog()
    previous = {row["url"]: row for row in old_styles + old_guides}
    discovered = fresh_links(args.fixture)
    merged = []
    for item in discovered:
        old = previous.get(item["url"], {})
        merged.append({**old, **item})
    styles = sorted((x for x in merged if x["kind"] == "style"), key=lambda x: x["url"])
    guides = sorted((x for x in merged if x["kind"] != "style"), key=lambda x: x["url"])
    if len(styles) * 5 < max(1, len(old_styles)) * 4 and not args.allow_shrink:
        raise ValueError("Refusing to shrink index by over 20%; inspect source or use --allow-shrink")
    print(f"Current {len(old_styles)} styles / {len(old_guides)} guides; "
          f"discovered {len(styles)} styles / {len(guides)} guides")
    if not args.apply:
        print("DRY RUN: no files modified. Pass --apply to write URL index.")
        return
    CATALOG.mkdir(parents=True, exist_ok=True)
    chunks = [styles[i:i + 400] for i in range(0, len(styles), 400)]
    for index, chunk in enumerate(chunks, 1):
        path = CATALOG / f"styles-{index:02d}.jsonl"
        path.write_text("".join(json.dumps(x, ensure_ascii=False) + "\n" for x in chunk),
                        encoding="utf-8")
    (CATALOG / "guides.jsonl").write_text(
        "".join(json.dumps(x, ensure_ascii=False) + "\n" for x in guides), encoding="utf-8")
    for stale in CATALOG.glob("styles-*.jsonl"):
        if stale.name not in {f"styles-{i:02d}.jsonl" for i in range(1, len(chunks) + 1)}:
            stale.unlink()
    verify()


def destinations(agent, scope, project):
    requested = ["codex", "claude", "copilot"] if agent == "all" else [agent]
    if scope == "user" and "copilot" in requested:
        raise ValueError("Copilot user-wide skill path is not configured; use --scope project")
    folders = {"codex": ".agents/skills", "claude": ".claude/skills",
               "copilot": ".github/skills"}
    for tool in requested:
        root = Path.home() if scope == "user" else project
        yield tool, root / folders[tool] / NAME


def install(args):
    verify()
    project = Path(args.project).expanduser().resolve()
    for agent, destination in destinations(args.agent, args.scope, project):
        if destination.resolve() == SKILL.resolve():
            raise ValueError("Cannot overwrite the source skill")
        if destination.exists() and not args.replace:
            print(f"SKIPPED: {agent} at {destination} exists (use --replace)")
            continue
        if args.dry_run:
            print(f"DRY RUN: install {agent} to {destination}")
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        scratch = Path(tempfile.mkdtemp(prefix="refero-install-", dir=str(destination.parent)))
        backup = None
        try:
            shutil.copytree(SKILL, scratch / NAME, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            verify(scratch / NAME / "catalog")
            if destination.exists():
                backup = destination.parent / (NAME + ".backup")
                if backup.exists():
                    raise ValueError("Existing backup: " + str(backup))
                destination.rename(backup)
            (scratch / NAME).rename(destination)
            print(f"INSTALLED: {agent} at {destination}")
        except Exception:
            if backup is not None and backup.exists() and not destination.exists():
                backup.rename(destination)
            raise
        finally:
            shutil.rmtree(scratch, ignore_errors=True)
        if backup is not None:
            print(f"Previous skill backed up at {backup}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("verify")
    refresh_cmd = sub.add_parser("refresh")
    refresh_cmd.add_argument("--fixture", help="Test/mock Firecrawl JSON response (offline)")
    refresh_cmd.add_argument("--apply", action="store_true")
    refresh_cmd.add_argument("--allow-shrink", action="store_true")
    install_cmd = sub.add_parser("install")
    install_cmd.add_argument("--agent", choices=["codex", "claude", "copilot", "all"],
                             default="codex")
    install_cmd.add_argument("--scope", choices=["project", "user"], default="project")
    install_cmd.add_argument("--project", default=".")
    install_cmd.add_argument("--replace", action="store_true")
    install_cmd.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "verify":
            verify()
        elif args.command == "refresh":
            refresh(args)
        else:
            install(args)
    except (ValueError, OSError, urllib.error.URLError) as exc:
        print("ERROR:", exc, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
