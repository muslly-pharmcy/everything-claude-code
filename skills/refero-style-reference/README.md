# Refero Styles — reusable DESIGN.md reference skill

Source: https://styles.refero.design/  
Saved 17 November 2026. This repository holds an **original agent skill and a verified public URL index**, not a mirror of third-party designs.

## What is included

- 1,344 style URLs across `catalog/styles-01.jsonl` ... `styles-04.jsonl`
- 52 URLs for example, guide and design-category pages in `catalog/guides.jsonl`
- `SKILL.md`: an agent workflow for selecting design references and adapting principles
- `scripts/manage.py`: no-dependency cross-platform verification, installation, and optional Firecrawl refresh
- `tests/test_refero_skill.py` in repository root and GitHub Actions regression checks

The source advertises **2,000+** style references but only 1,344 public style detail URLs were discoverable through the Firecrawl map on the snapshot date. The index contains **URLs and metadata only**. It does not contain full DESIGN.md texts, licensed graphics/fonts, or executable dependencies from each example.

## Installation using GitHub Codespaces, Windows, Linux or macOS

Open a terminal inside this repository, on the committed branch containing this skill.

**Verify first:**
```bash
python3 skills/refero-style-reference/scripts/manage.py verify
```

**Codex user-wide (all repos using this machine/user account):**
```bash
python3 skills/refero-style-reference/scripts/manage.py install --agent codex --scope user
```

**Into a project (Codex + Claude Code + GitHub Copilot):**
```bash
python3 skills/refero-style-reference/scripts/manage.py install --agent all --scope project --project /absolute/path/to/project
```

**Preview without writing files:**
```bash
python3 skills/refero-style-reference/scripts/manage.py install --agent all --scope project --project /absolute/path/to/project --dry-run
```

**Windows:** replace `python3` with `py -3` if the Python launcher is installed. Use a Windows absolute path after `--project`.

The installer never overwrites existing skills unless `--replace` is set. Replacements create a `.backup` sibling and refuse if a backup is already there. User-wide scope is supported for Codex (`~/.agents/skills`) and Claude Code (`~/.claude/skills`), but not GitHub Copilot; use project scope for Copilot (`.github/skills`). Local paths refer to the machine running the command: user-wide installation inside Codespaces does **not** install to a different Windows or Android device.

## Optional index refresh — not an always-on account connection

Requires a Firecrawl API key in the process environment; **never commit it**. The default refresh is read-only:
```bash
python3 skills/refero-style-reference/scripts/manage.py refresh
```

To write a refreshed index after reviewing the counts:
```bash
python3 skills/refero-style-reference/scripts/manage.py refresh --apply
```

For offline testing use `refresh --fixture /path/map.json`. Unexpected drops >20% are blocked unless explicitly overridden. GitHub Actions validates snapshots and installer tests, including a weekly **verification** job; it does not claim to refresh the site without a configured key.

## How to use

In Codex or Claude Code, ask the agent to use `refero-style-reference` and supply the product context, then have it select three relevant design references, fetch selected live detail pages via its connected Refero or Firecrawl tools, and produce a bespoke DESIGN.md. A user-installed repository skill does **not** automatically install itself into the ChatGPT account. The Refero MCP connector may need an active subscription; Firecrawl can read publicly accessible pages separately.

## Safety

No production application changes, no auto-merge, no copying complete third-party design systems, no downloaded fonts/images. Follow the linked site's terms and verify permission before incorporating protected assets.
