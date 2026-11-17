---
name: refero-style-reference
description: Search an indexed catalogue of Refero website DESIGN.md examples; select and apply grounded design principles to web and app UI without cloning brand identity.
---
# Refero Style Reference

## Purpose
Use this skill when a user wants visual references, website design direction, or a project-specific DESIGN.md. This is an original retrieval-and-synthesis skill, not one of Refero's downloadable designs. Its bundled catalogue contains **links and available metadata** only, NOT the full DESIGN.md contents, asset libraries, code dependencies, or external fonts.

## Evidence
- Original site: https://styles.refero.design/
- Library catalogue: `catalog/styles-01.jsonl` through `styles-04.jsonl` (1,344 discovered style URLs on 2026-11-17).
- Other site pages: `catalog/guides.jsonl` (52 discovered non-style URLs).
- Canonical detail pages: `https://styles.refero.design/style/{uuid}`
- Refero MCP design search and full style retrieval are preferable when available. Firecrawl can locate and read source pages.

## Procedure
1. Identify the product type, target audience, RTL/localization needs, accessibility constraints, target devices and existing brand.
2. Search catalogue `*.jsonl` by source website, category, theme, font or source description; prioritize 3-5 relevant style entries. Do not load every style.
3. For selected URLs, use Refero's search/get-style tools or fetch the individual live style page with Firecrawl. Verify the pages are accessible and current.
4. Extract typography, palette and the intended roles of tokens, spacing, density, grids, surfaces, component states, imagery direction, motion, and do/don't guidance; distinguish measurements from interpretations.
5. Produce a project-specific `DESIGN.md` describing original application guidelines, tokens, responsive behavior, RTL adaptation and constraints. Cite chosen source URLs and date accessed.
6. Do not claim installation or execution of anything unless verified. The website's `DESIGN.md` is design guidance, not an executable agent Skill. To enable in an agent, the host must load this SKILL.md and connect the required source tools.
7. Never copy a complete third-party identity, protected images, fonts, or proprietary assets into a project without checking permissions. No bulk mirroring; link to source references.

## Design quality checks
- Legibility and accessible color contrast
- Consistent spacing scale and component roles
- Keyboard and touch interaction, loading/error/empty states
- Mobile/desktop layouts; RTL-first labels where applicable
- No source-brand impersonation
- No implementation change until the user requests one

## Scope boundary
This index is a snapshot of publicly discoverable URLs, not an exhaustive copy of all 2,000+ examples advertised on the site. Missing/inaccessible pages remain unverified. Do not infer that any site is preinstalled in ChatGPT, Codex, or a target repository.
