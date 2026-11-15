# relcon-docs

Shared documentation defaults, styling, and configuration tools for Relaxed Constraints
projects using Zensical.

Install this package as a **documentation dependency**. It supplies Zensical, the
Python API handler and formatter, shared modern-theme settings, and copy-button CSS.
It has no dependency on BONDI or Yanex.

## Configure a project

Once installed in your project's environment:

```sh
relcon-docs configure --dry-run
relcon-docs configure
zensical serve
```

The project directory must already exist. A fresh project gets a minimal
`mkdocs.yml`; add your Markdown pages under `docs/` and edit navigation as needed.
The starter uses a localhost `site_url` for previews. Replace it with the published
site URL before deployment; Markdown exports require this setting.
For an existing YAML project, add `INHERIT: .relcon-docs/base.yml` first.
Convert and remove any `zensical.toml` before configuring: Zensical prefers it over YAML.

| File | Owner |
| --- | --- |
| `mkdocs.yml` | Project: metadata, navigation, API paths, Markdown-export sections and overrides |
| `.relcon-docs/base.yml` | Package: theme, Markdown extensions and API-rendering defaults |
| `docs/stylesheets/relcon-docs.css` | Package: labeled copy-button styling |
| `.relcon-docs/state.json` | Tool: applied version and hashes for detecting manual edits |

Commit all four files. Configuration is explicit: installing or upgrading the
dependency never rewrites project files. Builds and previews use ordinary
`zensical` commands, without a wrapper or sibling checkout.

## Upgrade and review

Upgrade the dependency and lockfile, then run:

```sh
relcon-docs configure --dry-run
relcon-docs configure
zensical build --strict
```

Unmodified managed files are updated. A changed or deleted managed file produces a
conflict and **no files are written**. On first adoption, an existing managed path
with different contents also conflicts. Identical contents can be adopted safely.

Move customizations into project overrides or a separate stylesheet. To explicitly
replace conflicting managed files, use `configure --force`; inspect the proposed
changes first with `configure --dry-run --force`. Force never rewrites an existing
`mkdocs.yml`. Invalid state files must be restored from Git; force does not bypass
state validation or symlink protection.

Each file replacement is atomic; the full set is not a filesystem transaction.
State is written last, and an interrupted run can be retried.

## Project overrides

Mappings merge recursively. Lists replace inherited lists, so repeat the shared
entries when overriding `theme.features` or `extra_css`. Use mapping syntax for
plugins and Markdown extensions to preserve unrelated inherited defaults:

```yaml
INHERIT: .relcon-docs/base.yml
site_name: My research project
site_url: https://example.org/my-project/
plugins:
  mkdocstrings:
    handlers:
      python:
        paths: [src]
  llmstxt:
    sections:
      Guides: ["*.md"]
      API reference: ["reference/**/*.md"]
```

The copy-button feature is shared, but Markdown export sections belong to the
project. The starter enables exports for all Markdown pages. Existing projects
should explicitly configure `llmstxt` as above.

This first version supports the standard `docs/` source directory and direct
inheritance from `.relcon-docs/base.yml`. It does not migrate arbitrary configurations,
prune old stylesheets, or modify workflow files.

## CLI reference

`relcon-docs configure [--project PATH] [--dry-run | --check] [--force]`

- `--project`: target an existing project root; defaults to the working directory.
- `--dry-run`: print proposed file diffs without writing. Conflicts still fail unless forced.
- `--check`: write nothing; exit 0 when current, 1 for pending updates, 2 for errors/conflicts.
- `--force`: explicitly replace conflicting managed files; incompatible with `--check`.
- `relcon-docs --version`: display the installed package version.

Use `relcon-docs configure --check` in CI before `zensical build --strict`.

## Development

```sh
uv sync --locked
uv run pytest
uv run ruff check .
uv run ruff format --check .
uv run relcon-docs configure --check
uv run zensical build --strict
uv build
```

For a local consumer trial before publishing, install the built wheel in an isolated
environment. The installed package contains all assets; consumers need no checkout
of this repository.
