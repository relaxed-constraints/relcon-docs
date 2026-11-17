# Changelog

## Unreleased

- Replace image examples with a reproducible Matplotlib Poisson plot, supplied
  as PNG and SVG with a standalone generation script.

- Enable attribute lists, Markdown in HTML, definition lists and footnotes, with
  a Layouts showcase for grids, image alignment and richer Markdown.

## 0.1.4 — 2026-11-17

- Use the same page-action typography and padding on presentation and ordinary pages.

## 0.1.3 — 2026-11-17

- Match the presentation toggle icon size to the Copy as Markdown icon.

## 0.1.2 — 2026-11-17

- Label the presentation sidebar “Table of contents”, restoring the normal title
  when presentation mode is inactive.

- Restrict presentation mode to desktop viewports while preserving the preference
  across resizing; use more compact page-action buttons.

- Add opt-in presentation pages with a focused layout, section navigation, keyboard
  shortcuts and a site-scoped remembered preference.

## 0.1.1 — 2026-11-17

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
