"""Exercise ownership, upgrades and actual Zensical builds."""

import html as html_module
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
    (tmp_path / "docs/index.md").write_text(
        "# Example\n\n::: sample.greet\n\n"
        '!!! note "Shared callout"\n\n    Callout body.\n\n'
        '??? tip "Shared details"\n\n    Details body.\n\n'
        "```mermaid\ngraph LR\n    A --> B\n```\n\n"
        "![Workflow](workflow.svg)\n\n"
        '<figure><img src="workflow.svg" alt="HTML workflow"></figure>\n'
    )
    (tmp_path / "docs/workflow.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"></svg>'
    )
    (tmp_path / "docs/guides").mkdir()
    (tmp_path / "docs/guides/nested.md").write_text("# Nested guide\n\nNested content.\n")
    result = subprocess.run(
        ["zensical", "build", "--strict"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    site = tmp_path / "site"
    html = (site / "index.html").read_text()
    assert 'href="#example"' in html
    assert 'class="headerlink"' in html
    assert 'title="Link to this section"' in html
    assert "¶" in html_module.unescape(html)
    assert html.count('class="glightbox"') == 2
    assert 'href="workflow.svg"' in html
    assert "sample.greet" in html
    assert 'class="admonition note"' in html
    assert '<details class="tip">' in html
    assert "<summary>Shared details</summary>" in html
    assert 'class="mermaid"' in html
    assert "A --" in html
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


def test_upgrade_from_two_asset_state_adds_math_without_force(tmp_path):
    assert run(tmp_path) == 0
    state_path = tmp_path / cli.STATE
    state = json.loads(state_path.read_text())
    del state["files"][cli.MATH]
    state_path.write_text(json.dumps(state))
    (tmp_path / cli.MATH).unlink()
    assert run(tmp_path) == 0
    assert (tmp_path / cli.MATH).read_bytes() == cli.managed_assets()[cli.MATH]
    assert run(tmp_path, "--check") == 0


def test_presentation_opt_in_and_custom_template_directory(tmp_path):
    project = tmp_path / "mkdocs.yml"
    project.write_text(
        "INHERIT: .relcon-docs/base.yml\nsite_name: Example\n"
        "site_url: https://example.org/project/\ntheme:\n  custom_dir: theme\n"
    )
    original = project.read_bytes()
    (tmp_path / "theme").mkdir()
    (tmp_path / "theme/custom.html").write_text("Project-owned template")
    assert run(tmp_path) == 0
    assert project.read_bytes() == original
    assert (tmp_path / "theme/custom.html").read_text() == "Project-owned template"
    assert (tmp_path / "theme/presentation.html").is_file()
    assert not (tmp_path / "docs/overrides/presentation.html").exists()
    assert run(tmp_path, "--check") == 0
    (tmp_path / "docs/index.md").write_text("# Ordinary page\n")
    (tmp_path / "docs/talk.md").write_text(
        "---\ntemplate: presentation.html\n---\n# Talk\n\n---\n\n## Second section\n"
    )
    updates = tmp_path / "docs/updates"
    updates.mkdir()
    (updates / ".meta.yml").write_text("template: presentation.html\n")
    (updates / "week.md").write_text("# Weekly update\n")
    result = subprocess.run(
        ["zensical", "build", "--strict"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    site = tmp_path / "site"
    assert 'class="presentation-content"' not in (site / "index.html").read_text()
    for page in ["talk/index.html", "updates/week/index.html"]:
        html = (site / page).read_text()
        assert 'class="presentation-content"' in html
        assert 'aria-pressed="false"' in html
        assert "data-presentation-root=" in html
        assert "relcon-docs-presentation.js" in html
        assert "relcon-docs-presentation.css" in html
    assert 'href="#second-section"' in (site / "talk/index.html").read_text()


def test_conflicting_presentation_template_blocks_all_writes(tmp_path):
    template = tmp_path / "docs/overrides/presentation.html"
    template.parent.mkdir(parents=True)
    template.write_text("User-owned presentation")
    before = snapshot(tmp_path)
    assert run(tmp_path) == 2
    assert snapshot(tmp_path) == before


def test_upgrade_from_previous_release_adds_presentation_assets(tmp_path):
    assert run(tmp_path) == 0
    state_path = tmp_path / cli.STATE
    state = json.loads(state_path.read_text())
    for name in list(state["files"]):
        if name not in {cli.BASE, cli.CSS, cli.MATH}:
            del state["files"][name]
            (tmp_path / name).unlink()
    state_path.write_text(json.dumps(state))
    assert run(tmp_path) == 0
    assert run(tmp_path, "--check") == 0


@pytest.mark.parametrize("directory", ["../outside", "/tmp/outside"])
def test_external_template_directory_is_rejected(tmp_path, directory):
    (tmp_path / "mkdocs.yml").write_text(
        f"INHERIT: .relcon-docs/base.yml\ntheme:\n  custom_dir: {directory}\n"
    )
    before = snapshot(tmp_path)
    assert run(tmp_path) == 2
    assert snapshot(tmp_path) == before


def test_richer_markdown_renders_with_shared_defaults(tmp_path):
    assert run(tmp_path) == 0
    (tmp_path / "docs/index.md").write_text(
        "# Layouts { #custom-title }\n\n"
        '<div class="grid cards" markdown>\n\n'
        "- **First card**\n\n- **Second card**\n\n</div>\n\n"
        '<div class="grid" markdown>\n\n'
        '![First](image.svg){ width="220" align=left loading=lazy }\n\n'
        "![Second](image.svg)\n\n</div>\n\n"
        "Baseline\n:   Reference configuration.\n\n"
        "==Important finding== and ~~Old claim~~. H~2~O.\n\n"
        "A qualified claim.[^note]\n\n[^note]: Supporting detail.\n"
    )
    (tmp_path / "docs/image.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" width="100" height="50"></svg>'
    )
    result = subprocess.run(
        ["zensical", "build", "--strict"], cwd=tmp_path, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr
    html = (tmp_path / "site/index.html").read_text()
    assert 'id="custom-title"' in html
    assert '<div class="grid cards">' in html
    assert "<strong>First card</strong>" in html
    assert '<div class="grid">' in html
    assert 'width="220"' in html
    assert 'align="left"' in html
    assert 'loading="lazy"' in html
    assert html.count('class="glightbox"') == 2
    assert "<dt>Baseline</dt>" in html
    assert "<dd>Reference configuration.</dd>" in html
    assert 'href="#fn:note"' in html
    assert 'href="#fnref:note"' in html
    assert "<mark>Important finding</mark>" in html
    assert "<del>Old claim</del>" in html
    assert "H<sub>2</sub>O" in html
