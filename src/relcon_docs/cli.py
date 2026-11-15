"""Apply packaged defaults without rewriting project-owned configuration."""

import argparse
import difflib
import hashlib
import json
import os
import sys
import tempfile
from importlib.metadata import version
from importlib.resources import files
from pathlib import Path

import yaml

BASE = ".relcon-docs/base.yml"
STATE = ".relcon-docs/state.json"
CSS = "docs/stylesheets/relcon-docs.css"
WORKFLOW = ".github/workflows/docs.yml"
MATH = "docs/javascripts/relcon-docs-math.js"


class ConfigurationError(Exception):
    """A configuration cannot safely be applied."""


def digest(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def managed_assets() -> dict[str, bytes]:
    assets = files("relcon_docs").joinpath("assets")
    return {
        BASE: assets.joinpath("base.yml").read_bytes(),
        CSS: assets.joinpath("relcon-docs.css").read_bytes(),
        MATH: assets.joinpath("relcon-docs-math.js").read_bytes(),
    }


def safe_path(root: Path, relative: str) -> Path:
    """Reject symlinks and non-directory parents before reading or writing."""
    path = root
    for part in Path(relative).parts:
        path = path / part
        if path.is_symlink():
            raise ConfigurationError(f"Refusing symlink: {path}")
        if path != root / relative and path.exists() and not path.is_dir():
            raise ConfigurationError(f"Expected a directory: {path}")
    if path.exists() and not path.is_file():
        raise ConfigurationError(f"Expected a file: {path}")
    return path


def read_state(path: Path, assets: dict[str, bytes]) -> dict[str, str]:
    if not path.exists():
        return {}
    try:
        state = json.loads(path.read_text())
        hashes = state["files"]
        if (
            state["schema"] != 1
            or not isinstance(hashes, dict)
            or set(hashes) not in ({BASE, CSS}, set(assets))
            or not all(
                isinstance(value, str)
                and len(value) == 64
                and all(char in "0123456789abcdef" for char in value)
                for value in hashes.values()
            )
        ):
            raise ValueError
    except (ValueError, KeyError, TypeError) as exc:
        raise ConfigurationError(
            f"Invalid state file: {path}. Restore it from Git before configuring."
        ) from exc
    return hashes


def project_config(root: Path) -> bytes | None:
    """Validate an existing project or prepare a starter, without editing it."""
    if (root / "zensical.toml").exists():
        raise ConfigurationError("Convert zensical.toml to mkdocs.yml first; it takes precedence.")
    if (root / "mkdocs.yaml").exists():
        raise ConfigurationError("Rename mkdocs.yaml to mkdocs.yml first.")
    path = safe_path(root, "mkdocs.yml")
    if not path.exists():
        return (
            "# Project-owned configuration. Override shared defaults here.\n"
            "# Replace the local site_url with your published URL before deployment.\n"
            f"INHERIT: {BASE}\n"
            + yaml.safe_dump(
                {
                    "site_name": root.name,
                    "site_url": "http://127.0.0.1:8000/",
                },
                sort_keys=False,
            )
        ).encode()

    # Compose rather than construct: existing MkDocs configurations may use
    # !ENV and Python-name tags, which we must neither execute nor rewrite.
    try:
        config = yaml.compose(path.read_text())
        if not isinstance(config, yaml.MappingNode):
            raise ValueError
        settings = {}
        for key, value in config.value:
            if not isinstance(key, yaml.ScalarNode) or key.value in settings:
                raise ValueError
            settings[key.value] = value
        inherit = settings.get("INHERIT")
        if not isinstance(inherit, yaml.ScalarNode) or inherit.value != BASE:
            raise ConfigurationError(f"Set INHERIT: {BASE} in mkdocs.yml first.")
        docs_dir = settings.get("docs_dir")
        if docs_dir is not None and (
            not isinstance(docs_dir, yaml.ScalarNode) or docs_dir.value not in ("docs", "./docs")
        ):
            raise ConfigurationError("This version supports only docs_dir: docs.")
    except (yaml.YAMLError, ValueError) as exc:
        raise ConfigurationError("mkdocs.yml must be a YAML mapping with unique keys.") from exc
    return None


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        os.chmod(temporary, 0o644)
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def configure(root: Path, *, dry_run: bool, check: bool, force: bool) -> int:
    if not root.is_dir():
        raise ConfigurationError(f"Project directory does not exist: {root}")
    assets = managed_assets()
    paths = {name: safe_path(root, name) for name in [*assets, STATE]}
    baseline = read_state(paths[STATE], assets)
    starter = project_config(root)
    workflow_path = safe_path(root, WORKFLOW)
    changes = {}
    conflicts = []

    for name, desired in assets.items():
        path = paths[name]
        current = path.read_bytes() if path.exists() else None
        if current == desired:
            continue
        changes[name] = desired
        if name in baseline:
            if current is None or digest(current) != baseline[name]:
                conflicts.append(name)
        elif current is not None:
            conflicts.append(name)

    if starter is not None:
        changes["mkdocs.yml"] = starter
    if not workflow_path.exists():
        changes[WORKFLOW] = files("relcon_docs").joinpath("assets/docs.yml").read_bytes()
    state = {
        "schema": 1,
        "package_version": version("relcon-docs"),
        "files": {name: digest(content) for name, content in assets.items()},
    }
    state_bytes = (json.dumps(state, indent=2, sort_keys=True) + "\n").encode()
    if not paths[STATE].exists() or paths[STATE].read_bytes() != state_bytes:
        changes[STATE] = state_bytes

    for name in changes:
        print(f"Update {name}" if (root / name).exists() else f"Create {name}")
        if dry_run:
            path = root / name
            before = path.read_bytes() if path.exists() else b""
            print(
                "".join(
                    difflib.unified_diff(
                        before.decode(errors="replace").splitlines(keepends=True),
                        changes[name].decode().splitlines(keepends=True),
                        fromfile=f"a/{name}",
                        tofile=f"b/{name}",
                    )
                ),
                end="",
            )

    if conflicts:
        print("Managed-file conflicts: " + ", ".join(conflicts), file=sys.stderr)
        if not force:
            print(
                "No files written. Move customizations to mkdocs.yml or a separate CSS file; "
                "use --force to replace managed files.",
                file=sys.stderr,
            )
            return 2
        print("Explicit --force: package contents will replace these managed files.")

    if check:
        if not changes:
            print("Configuration is current.")
        return 1 if changes else 0
    if dry_run:
        print("Dry run: no files written.")
        return 0

    # Validate all destinations before writing anything. Each file replacement
    # is atomic; the state is written last so an interrupted run can be retried.
    for name in changes:
        safe_path(root, name)
    for name, content in changes.items():
        atomic_write(root / name, content)
    print("Configuration updated." if changes else "Configuration is current.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", action="version", version=version("relcon-docs"))
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("configure", help="Apply shared documentation defaults")
    command.add_argument(
        "--project", type=Path, default=Path.cwd(), help="Project root (default: cwd)"
    )
    mode = command.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Show diffs without writing")
    mode.add_argument(
        "--check", action="store_true", help="Exit 1 if updates are needed; do not write"
    )
    command.add_argument("--force", action="store_true", help="Replace conflicting managed files")
    args = parser.parse_args(argv)
    if args.check and args.force:
        parser.error("--check cannot be combined with --force")
    try:
        return configure(
            args.project.resolve(), dry_run=args.dry_run, check=args.check, force=args.force
        )
    except (ConfigurationError, OSError) as exc:
        print(f"relcon-docs: {exc}", file=sys.stderr)
        return 2
