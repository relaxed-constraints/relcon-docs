# Changelog

## Unreleased

- Enable built-in image lightboxes across documentation sites, including zoom
  controls, without additional dependencies or image markup.
- Recommend a bounded dependency range and document explicit lockfile upgrades.

## 0.1.0 — 2026-11-15

- Enable heading permalinks with the paragraph symbol and descriptive link titles.

- Sort API members alphabetically and exclude underscore-prefixed members by default.

- Publish the self-hosted documentation showcase with Markdown, diagrams, equations
  and figures; use the reusable deployment workflow on main and manual runs.
- Add shared on-demand MathJax rendering and dark-theme Markdown-copy controls.

- Add paired accent fill, border and text colours for highlighting diagram boxes,
  with a light/dark example on the diagram-colours page.

- Share accessible light/dark diagram colours for flowcharts and sequence roles,
  with CSS properties for custom diagrams and legacy variable aliases.

- Enable callouts, collapsible notes and Mermaid diagrams in shared defaults.

- Enable Markdown exports and llms.txt in shared defaults for new and existing
  projects, without requiring local plugin configuration.

- Add a reusable GitHub Pages deployment workflow with caller-owned triggers.
- Create a manual-only starter docs.yml on configuration when absent; preserve
  existing workflow contents, even with --force.

- Add packaged Zensical defaults and copy-button styling.
- Add explicit configuration, dry-run diffs, CI checks and managed-file conflict detection.
- Preserve project-owned YAML and support ordinary Zensical builds and previews.
