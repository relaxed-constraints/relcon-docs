"""Keep shared diagram labels and boundaries readable in both themes."""

import re

import pytest

from relcon_docs.cli import CSS, managed_assets


def contrast(first, second):
    def luminance(color):
        channels = [int(color[i : i + 2], 16) / 255 for i in (1, 3, 5)]
        linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
        return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

    values = sorted((luminance(first), luminance(second)))
    return (values[1] + 0.05) / (values[0] + 0.05)


@pytest.mark.parametrize("scheme", ["default", "slate"])
def test_diagram_contrast(scheme):
    css = managed_assets()[CSS].decode()
    block = re.search(r'\[data-md-color-scheme="' + scheme + r'"\]\s*\{([^}]+)', css)[1]
    colors = dict(re.findall(r"--relcon-diagram-([\w-]+):\s*(#[0-9a-f]{6})", block))
    for surface in ("node-bg", "frame-bg"):
        assert contrast(colors["text"], colors[surface]) >= 4.5
        assert contrast(colors["edge"], colors[surface]) >= 3
    for role in ("node", "frame"):
        assert contrast(colors[f"{role}-border"], colors[f"{role}-bg"]) >= 3
