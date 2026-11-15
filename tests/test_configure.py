"""Exercise ownership, upgrades and actual Zensical builds."""

import json
import subprocess

import pytest
import yaml

from relcon_docs import cli


def snapshot(root):
    return {
        str(path.relative_to(root)): path.read_bytes() for path in root.rglob("*") if path.is_file()
    }


def run(root, *args):
    return cli.main(["configure", "--project", str(root), *args])


def test_initialize_and_repeat_without_writes(tmp_path):
    assert run(tmp_path) == 0
    before = snapshot(tmp_path)
    mtimes = {p: (tmp_path / p).stat().st_mtime_ns for p in before}
    assert run(tmp_path) == 0
    assert run(tmp_path, "--check") == 0
    assert snapshot(tmp_path) == before
    assert {p: (tmp_path / p).stat().st_mtime_ns for p in before} == mtimes
    config = yaml.safe_load((tmp_path / "mkdocs.yml").read_text())
    assert config["INHERIT"] == cli.BASE


def test_dry_run_and_check_never_write(tmp_path, capsys):
    assert run(tmp_path, "--dry-run") == 0
    assert "+theme:" in capsys.readouterr().out
    assert snapshot(tmp_path) == {}
    assert run(tmp_path, "--check") == 1
    assert snapshot(tmp_path) == {}


@pytest.mark.parametrize("deleted", [False, True])
def test_manual_edit_or_deletion_blocks_entire_update(tmp_path, deleted):
    assert run(tmp_path) == 0
    path = tmp_path / cli.CSS
    if deleted:
        path.unlink()
    else:
        path.write_text("/* local styling */")
    before = snapshot(tmp_path)
    assert run(tmp_path) == 2
    assert run(tmp_path, "--check") == 2
    assert snapshot(tmp_path) == before
    assert run(tmp_path, "--dry-run", "--force") == 0
    assert snapshot(tmp_path) == before
    assert run(tmp_path, "--force") == 0
    assert run(tmp_path, "--check") == 0


def test_upgrade_preserves_project_and_unrelated_files(tmp_path, monkeypatch):
    assert run(tmp_path) == 0
    project = tmp_path / "mkdocs.yml"
    project.write_text(project.read_text() + "# My custom project\ntheme:\n  font: false\n")
    custom = tmp_path / "docs/custom.css"
    custom.write_text("/* project-owned */")
    original = project.read_bytes()
    assets = cli.managed_assets()
    assets[cli.CSS] += b"\n/* new package feature */\n"
    monkeypatch.setattr(cli, "managed_assets", lambda: assets)
    assert run(tmp_path, "--check") == 1
    assert run(tmp_path) == 0
    assert (tmp_path / cli.CSS).read_bytes() == assets[cli.CSS]
    assert project.read_bytes() == original
    assert custom.read_text() == "/* project-owned */"
    assert run(tmp_path, "--check") == 0


def test_initial_adoption_requires_force_for_different_existing_files(tmp_path):
    path = tmp_path / cli.BASE
    path.parent.mkdir()
    path.write_text("theme: {}\n")
    before = snapshot(tmp_path)
    assert run(tmp_path) == 2
    assert snapshot(tmp_path) == before
    assert run(tmp_path, "--force") == 0


def test_identical_untracked_assets_can_be_adopted(tmp_path):
    for name, content in cli.managed_assets().items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    assert run(tmp_path) == 0
    assert (tmp_path / cli.STATE).exists()


@pytest.mark.parametrize(
    "config",
    [
        "site_name: Missing inheritance\n",
        "INHERIT: another.yml\n",
        "INHERIT: .relcon-docs/base.yml\ndocs_dir: content\n",
        "- not a mapping\n",
        "INHERIT: .relcon-docs/base.yml\nINHERIT: other.yml\n",
    ],
)
def test_invalid_project_is_never_modified_even_with_force(tmp_path, config):
    (tmp_path / "mkdocs.yml").write_text(config)
    before = snapshot(tmp_path)
    assert run(tmp_path, "--force") == 2
    assert snapshot(tmp_path) == before


def test_yaml_tags_are_preserved_without_execution(tmp_path):
    project = tmp_path / "mkdocs.yml"
    content = (
        "INHERIT: .relcon-docs/base.yml\n"
        "site_name: !ENV SITE_NAME\n"
        "extra: !!python/object/apply:os.system ['must not execute']\n"
    )
    project.write_text(content)
    assert run(tmp_path) == 0
    assert project.read_text() == content


@pytest.mark.parametrize("filename", ["zensical.toml", "mkdocs.yaml"])
def test_competing_configuration_is_rejected(tmp_path, filename):
    (tmp_path / filename).write_text("existing")
    before = snapshot(tmp_path)
    assert run(tmp_path) == 2
    assert snapshot(tmp_path) == before


@pytest.mark.parametrize("state", ["broken json", "null", '{"schema": 9, "files": {}}'])
def test_corrupt_state_is_not_overwritten(tmp_path, state):
    assert run(tmp_path) == 0
    (tmp_path / cli.STATE).write_text(state)
    before = snapshot(tmp_path)
    assert run(tmp_path, "--force") == 2
    assert snapshot(tmp_path) == before


def test_symlink_parent_is_rejected(tmp_path):
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (project / ".relcon-docs").symlink_to(outside, target_is_directory=True)
    assert run(project, "--force") == 2
    assert list(outside.iterdir()) == []


def test_state_hashes_record_installed_assets(tmp_path):
    assert run(tmp_path) == 0
    state = json.loads((tmp_path / cli.STATE).read_text())
    assert state["files"] == {
        name: cli.digest(content) for name, content in cli.managed_assets().items()
    }


@pytest.mark.parametrize("existing", [False, True])
def test_actual_build_exports_markdown_and_renders_api(tmp_path, existing):
    if existing:
        (tmp_path / "mkdocs.yml").write_text(
            "INHERIT: .relcon-docs/base.yml\n"
            "site_name: Existing project\nsite_url: https://example.org/\n"
        )
    assert run(tmp_path) == 0
    project = tmp_path / "mkdocs.yml"
    config = yaml.safe_load(project.read_text())
    config.setdefault("plugins", {})["mkdocstrings"] = {"handlers": {"python": {"paths": ["."]}}}
    project.write_text(yaml.safe_dump(config, sort_keys=False))
    (tmp_path / "sample.py").write_text(
        "def greet(name: str) -> str:\n"
        '    """Return a greeting.\n\n'
        "    Args:\n"
        "        name: Person to greet.\n\n"
        "    Returns:\n"
        "        A friendly greeting.\n"
        '    """\n'
        '    return f"Hello {name}"\n'
    )
    (tmp_path / "docs/index.md").write_text("# Example\n\n::: sample.greet\n")
    (tmp_path / "docs/guides").mkdir()
    (tmp_path / "docs/guides/nested.md").write_text("# Nested guide\n\nNested content.\n")
    result = subprocess.run(
        ["zensical", "build", "--strict"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    site = tmp_path / "site"
    html = (site / "index.html").read_text()
    assert "sample.greet" in html
    assert "data-md-copy-url" in html
    assert "stylesheets/relcon-docs.css" in html
    assert "Return a greeting" in (site / "index.md").read_text()
    assert "index.md" in (site / "llms.txt").read_text()
    assert "Nested content" in (site / "guides/nested/index.md").read_text()
    assert "data-md-copy-url" in (site / "guides/nested/index.html").read_text()
    assert (site / "stylesheets/relcon-docs.css").read_bytes() == cli.managed_assets()[cli.CSS]


def test_starter_workflow_is_manual_only_and_project_owned(tmp_path):
    assert run(tmp_path) == 0
    workflow = tmp_path / cli.WORKFLOW
    # BaseLoader keeps GitHub's "on" key as a string instead of a YAML 1.1 boolean.
    config = yaml.load(workflow.read_text(), Loader=yaml.BaseLoader)
    assert set(config["on"]) == {"workflow_dispatch"}
    assert "deploy-docs.yml@main" in config["jobs"]["docs"]["uses"]
    state = json.loads((tmp_path / cli.STATE).read_text())
    assert cli.WORKFLOW not in state["files"]


@pytest.mark.parametrize(
    "content",
    [
        """# Custom release workflow
on:
  release:
    types: [published]
""",
        """# Custom consumer workflow
on:
  push:
    branches: [main]
""",
        "",  # Even an empty existing file belongs to the user.
    ],
)
def test_existing_workflow_is_untouched_in_all_modes(tmp_path, content):
    workflow = tmp_path / cli.WORKFLOW
    workflow.parent.mkdir(parents=True)
    workflow.write_text(content)
    original_mtime = workflow.stat().st_mtime_ns
    for args in [(), ("--force",), ("--dry-run",), ("--check",)]:
        assert run(tmp_path, *args) == 0
        assert workflow.read_text() == content
        assert workflow.stat().st_mtime_ns == original_mtime


def test_workflow_adoption_on_upgrade_and_dry_run(tmp_path, capsys):
    assert run(tmp_path) == 0
    (tmp_path / cli.WORKFLOW).unlink()
    before = snapshot(tmp_path)
    assert run(tmp_path, "--check") == 1
    assert run(tmp_path, "--dry-run") == 0
    assert f"Create {cli.WORKFLOW}" in capsys.readouterr().out
    assert snapshot(tmp_path) == before
    assert run(tmp_path) == 0
    assert (tmp_path / cli.WORKFLOW).is_file()


def test_workflow_symlink_blocks_all_writes(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    (project / ".github").symlink_to(outside, target_is_directory=True)
    assert run(project, "--force") == 2
    assert not (project / cli.BASE).exists()
    assert list(outside.iterdir()) == []
