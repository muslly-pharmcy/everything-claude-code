# Refero public-style skill integration (independent of subscription)

This is an operational companion to `skills/refero-style-reference/`, not a copy of Refero's paid MCP or a mirror of proprietary `DESIGN.md` exports.

## Capabilities
- Search the previously saved public URL index (1,344 style references; 52 other pages, as of 2026-11-17).
- Validate entries against a strict Refero hostname/path allowlist.
- Update URL records from **public sitemaps only** (no private API, no full-page harvesting).
- Preserve any previous title/description as *historical metadata*; those fields are not reverified by sitemap sync.
- Install the original `SKILL.md` and public reference index for project-local Codex, Claude Code or Cursor.
- Detect unexpected loss of >10% of indexed styles and stop, rather than silently wipe the catalogue.
- Propose weekly GitHub draft PRs to review changes; never merge or deploy automatically.

## Install and verify
```bash
python scripts/refero_catalog.py validate
python -m unittest discover -s tests -p 'test_refero_catalog.py' -v
python scripts/refero_catalog.py search "Linear" --limit 10
python scripts/refero_catalog.py install --project /path/to/my-project --target codex
# Alternatives: --target claude, cursor, all
# Only to intentionally replace an existing installation: --force
```

On Windows PowerShell, substitute your repository path (e.g., `D:\Projects\YourApp`) for `/path/to/my-project`.

## Refresh
```bash
python scripts/refero_catalog.py sync
```
The command requires external access to `https://styles.refero.design/sitemap.xml` and its two published child sitemaps. If the website is unavailable, it fails without downloading private data. The scheduled workflow only works after this branch is merged to the repository default branch and GitHub Actions write/PR permissions permit creating a draft PR.

## Agent setup and account limitation
- **Codex:** use `.agents/skills/refero-style-reference/SKILL.md` as a project-local skill.
- **Claude Code:** use `.claude/skills/refero-style-reference/SKILL.md`.
- **Cursor:** use `.cursor/skills/refero-style-reference/SKILL.md` when supported by that version.
- **ChatGPT:** Refero's curated skill may be visible through a connected plugin, but storing in GitHub or the ChatGPT file library does **not** automatically activate a custom skill. Public Refero pages can still be read with Firecrawl. A Refero `NO_SUBSCRIPTION` response cannot be bypassed by this index.

Use public examples as references, never copy complete source brand identity, licensed fonts, images or other protected assets.