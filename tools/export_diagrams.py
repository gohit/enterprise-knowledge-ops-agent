r"""Export all Mermaid diagrams found in docs/*.md to SVG + PNG image files.

Renders each ```mermaid fenced code block using mermaid.js inside a headless
Chromium (via Playwright). Diagram definitions stay local and are rendered in the
local browser; only the mermaid.js library is loaded from a CDN.

Usage:
    .\.venv\Scripts\python.exe tools\export_diagrams.py
Outputs to: docs/diagrams/<doc-stem>_<n>.svg and .png  (+ index.html)
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DOCS = ROOT / "docs"
OUT = DOCS / "diagrams"

MERMAID_CDN = "https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs"

# Matches ```mermaid ... ``` fenced blocks.
FENCE = re.compile(r"```mermaid\s*\n(.*?)```", re.DOTALL)

# Renders one diagram string to an SVG string using mermaid in the page.
RENDER_JS = """
async ([code]) => {
    const mermaid = (await import('%s')).default;
    mermaid.initialize({ startOnLoad: false, theme: 'default', securityLevel: 'loose' });
    const { svg } = await mermaid.render('graphDiv', code);
    document.body.innerHTML = svg;
    return svg;
}
""" % MERMAID_CDN


def collect_diagrams() -> list[tuple[str, str]]:
    """Return (name, mermaid_code) for every diagram across docs, in doc order."""
    diagrams: list[tuple[str, str]] = []
    for md in sorted(DOCS.glob("*.md")):
        blocks = FENCE.findall(md.read_text(encoding="utf-8"))
        for i, code in enumerate(blocks, start=1):
            name = f"{md.stem}_{i}"
            diagrams.append((name, code.strip()))
    return diagrams


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    diagrams = collect_diagrams()
    if not diagrams:
        print("No mermaid diagrams found in docs/*.md")
        return 1

    print(f"Found {len(diagrams)} diagram(s). Rendering...")
    rendered: list[str] = []

    with sync_playwright() as p:
        # Use the system-installed Edge (trusts the corporate root CA, so the
        # mermaid.js CDN loads); avoids downloading Playwright's own Chromium.
        browser = p.chromium.launch(channel="msedge")
        # deviceScaleFactor boosts PNG resolution for crisp images.
        page = browser.new_page(viewport={"width": 1600, "height": 1200},
                                device_scale_factor=2)
        page.set_content("<!DOCTYPE html><html><body></body></html>")

        for name, code in diagrams:
            try:
                svg = page.evaluate(RENDER_JS, [code])
            except Exception as exc:  # noqa: BLE001
                print(f"  [FAIL] {name}: {exc}")
                continue

            (OUT / f"{name}.svg").write_text(svg, encoding="utf-8")

            # Screenshot the rendered svg element for the PNG.
            el = page.query_selector("svg")
            if el:
                el.screenshot(path=str(OUT / f"{name}.png"))
            print(f"  [ok]   {name}.svg / .png")
            rendered.append(name)

        browser.close()

    # Build a simple gallery so all images can be reviewed in one place.
    items = "\n".join(
        f'<figure><figcaption>{n}</figcaption>'
        f'<img src="{n}.svg" alt="{n}"/></figure>'
        for n in rendered
    )
    (OUT / "index.html").write_text(
        "<!DOCTYPE html><html><head><meta charset='utf-8'>"
        "<title>Diagram gallery</title>"
        "<style>body{font-family:sans-serif;margin:24px;background:#fafafa}"
        "figure{margin:0 0 32px;padding:16px;background:#fff;border:1px solid #ddd;"
        "border-radius:8px}figcaption{font-weight:600;margin-bottom:8px;color:#333}"
        "img{max-width:100%}</style></head><body>"
        "<h1>Enterprise Knowledge Ops Agent — Diagrams</h1>"
        f"{items}</body></html>",
        encoding="utf-8",
    )

    print(f"\nDone. {len(rendered)} diagram(s) written to {OUT}")
    print(f"Open {OUT / 'index.html'} to review them all.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
