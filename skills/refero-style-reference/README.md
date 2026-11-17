# Refero Styles — saved index and agent skill

Source: [Refero Styles](https://styles.refero.design/) — **high-quality DESIGN.md references** for AI agents.

## Inventory (17 November 2026)
- 1,344 distinct public style-detail URLs found by Firecrawl site-map discovery.
- 52 additional pages of guides, examples and design-style collections.
- Total: 1,396 distinct publicly mapped entries under the site.
- Source homepage advertises **2,000+** styles; not all are present in the discoverable site map. Counts may change.
- The JSONL index stores original URLs and any metadata that was available in the site map. It does **not** contain the complete third-party DESIGN.md texts, image assets or executable plugins.
- Each style detail page exposes design guidance and export formats: `DESIGN.md`, `Tailwind v4`, `CSS Variables`, `Design Tokens`. Not separate software packages.

## Files
- [Original agent skill](SKILL.md)
- [Catalogue part 1](catalog/styles-01.jsonl)
- [Catalogue part 2](catalog/styles-02.jsonl)
- [Catalogue part 3](catalog/styles-03.jsonl)
- [Catalogue part 4](catalog/styles-04.jsonl)
- [Guide and gallery index](catalog/guides.jsonl)

## Use
For Codex/Claude Code, copy this folder into the skill directory supported by that environment and ensure the agent can access the referenced files. For ChatGPT, use connected Refero/Firecrawl to query references or upload relevant content; storing files in GitHub does not automatically install or activate a custom skill in your ChatGPT account.

**State:** Saved as source references on a separate Git branch. Not merged, automatically installed, or applied to YmPharma/muslly.com. Do not deploy without a specific implementation request.
