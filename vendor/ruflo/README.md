# Pinned Ruflo skill registry (review-first)

Source: https://github.com/ruvnet/ruflo at `87f612cef121b50c2e31e2d3f88e46d88963a377` (MIT). See `LICENSE` and `source/SKILL.md`.

A GitHub-tree-derived inventory of **403 SKILL.md files**, **16 skill-local supporting files**, **134 named skills published in 34 skills.sh catalog groups** is in `skills-catalog.json`. These are overlapping categories, not additive independent capabilities. Files can refer to external CLI/MCP dependencies not included in the registry.

All 403 paths and Git blob SHA-1 checksums are indexed. Source files are deliberately not bulk-activated: run `node scripts/ruflo-skills-sync.mjs --scope published` for a dry-run, or `--scope all` to preview all source paths. The importer requires explicit `--apply --i-reviewed-these-skills`; `--scope all` deposits files under `vendor/ruflo/source/` for review rather than turning them on. Preview first and review selected SKILL.md/supporting scripts before using `--scope published` to make them agent-discoverable. This does not install Ruflo CLI or MCP servers.

Do not run unpinned @latest commands in production; the repository is an agent-orchestration toolkit, not a pharmacy ERP runtime. Enforce resource caps, RLS, journal immutability, FEFO, idempotency, project isolation, consent and tests. No generated artifacts or instruction files prove a live rollout.

## Entire upstream source (submodule)

The full, unmodified Ruflo source tree is pinned at `vendor/ruflo/upstream` to commit `87f612cef121b50c2e31e2d3f88e46d88963a377` via a Git submodule. In a disposable checkout, use `git submodule update --init vendor/ruflo/upstream`, then verify `git -C vendor/ruflo/upstream rev-parse HEAD` equals that revision. This fetches source into an inert vendor path but **does not run, install, enable or approve any skill**. The inventory retains 403 SKILL.md paths plus 16 support files, and `vendor/ruflo/source/SKILL.md` preserves the original root skill as a convenience. Do not point a production agent's active skills directory at the whole upstream tree.
