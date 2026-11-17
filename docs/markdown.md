# Markdown

Write documentation as plain-text `.md` files. These examples work with the
shared relcon-docs configuration. Each source example is followed by its output.

## Headings

Use one `#` heading for the page title, then `##` and `###` for sections and
subsections. Keep levels in order so readers can follow the structure.

```markdown
## Experiment setup
### Dataset
```

### Dataset

This is a third-level heading; the page title and section headings show the other levels.

## Text and links

```markdown
Use **bold** for emphasis, *italics* for a term, and `code` for identifiers.
Read the [diagram guide](diagrams.md).
```

Use **bold** for emphasis, *italics* for a term, and `code` for identifiers.
Read the [diagram guide](diagrams.md).

## Highlighting and strikethrough

Use `==text==` to highlight a finding and `~~text~~` to cross out an old statement.
The shared configuration enables `pymdownx.mark` and `pymdownx.tilde`, supported by
[Zensical](https://zensical.org/docs/compatibility/markdown/python-markdown-extensions/#caret-mark-tilde).

```markdown
==The revised query uses the index.==
~~The query scans the entire collection.~~
```

==The revised query uses the index.==
~~The query scans the entire collection.~~

Tilde also supports subscripts: `H~2~O` renders as H~2~O.

## Lists

```markdown
- Dataset
- Workload
    - Queries
    - Parameters

An ordered procedure:

1. Prepare the data.
2. Run the experiment.
3. Inspect the results.
```

- Dataset
- Workload
    - Queries
    - Parameters

An ordered procedure:

1. Prepare the data.
2. Run the experiment.
3. Inspect the results.

## Tables

```markdown
| Setting | Purpose |
| --- | --- |
| `site_name` | Title shown in the header |
| `site_url` | Published documentation URL |
```

| Setting | Purpose |
| --- | --- |
| `site_name` | Title shown in the header |
| `site_url` | Published documentation URL |

## Code blocks

Add a language after the opening fence for syntax highlighting. The outer
four-backtick fence below lets us display a three-backtick fence as source.

````markdown
```python
def greet(name: str) -> str:
    return f"Hello, {name}"
```
````

```python
def greet(name: str) -> str:
    return f"Hello, {name}"
```

## Quotations

```markdown
> Record assumptions alongside each experiment.
```

> Record assumptions alongside each experiment.

## Callouts and collapsible notes

```markdown
!!! note "Reproducibility"

    Record the dataset and configuration used for each run.

??? tip "Optional details"

    Keep longer explanations here.
```

!!! note "Reproducibility"

    Record the dataset and configuration used for each run.

??? tip "Optional details"

    Keep longer explanations here.

## Content tabs

```markdown
=== "Python"

    Use a Python script for reusable experiment logic.

=== "Notebook"

    Use a notebook to explore results interactively.
```

=== "Python"

    Use a Python script for reusable experiment logic.

=== "Notebook"

    Use a notebook to explore results interactively.

## Heading links

Hover over a heading to reveal its ¶ permalink. Click it to navigate to that
section, or copy the link address to share a direct link. These links are enabled
in the shared defaults and need no page-specific Markdown.
