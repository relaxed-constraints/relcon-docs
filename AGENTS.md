# Working on relcon-docs

Keep this package independent of BONDI and Yanex. Shared documentation configuration
and assets belong here; project content and research code do not.

Preserve ordinary Zensical build and serve commands. Configuration updates are explicit.
Never overwrite project-owned configuration. Treat managed-file conflicts as errors
unless the caller explicitly requests force.

Use uv, pytest and Ruff. Test configuration updates, conflicts, installed assets and
strict documentation builds. Record user-facing changes under Unreleased.
Work on codex/ branches and leave commits for review; do not merge without approval.
