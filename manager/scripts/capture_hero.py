#!/usr/bin/env python3
"""Capture README hero: Shallow reef · My Portfolio · Navigate · Graph."""

import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/images/portolan-hero.png"
URL = os.environ.get("PORTOLAN_URL", "http://127.0.0.1:5173")


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Install: pip install playwright && playwright install chromium", file=sys.stderr)
        return 1

    try:
        from PIL import Image
    except ImportError:
        Image = None  # type: ignore

    raw = ROOT / "docs/images/portolan-hero-raw.png"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1180, "height": 1280})
        page.goto(URL, wait_until="networkidle")

        page.evaluate(
            """() => {
            for (const id of ['demo', 'local-reef', 'template']) {
              localStorage.setItem(`scuba-dock-guide-dismissed:${id}`, '1');
              localStorage.setItem(`scuba-dock-seen:${id}:my-portfolio`, '1');
            }
          }"""
        )
        page.reload(wait_until="networkidle")

        page.get_by_role("button", name="/", exact=True).click()
        page.get_by_role("button", name="Shallow reef", exact=True).click()

        # vault switch keeps my-portfolio channel → workspace opens directly
        page.wait_for_selector(".workspace-shell", timeout=15000)
        page.get_by_role("tab", name="Graph", exact=True).click()

        page.add_style_tag(
            content=".obsidian-link-notice { display: none !important; }"
        )

        page.wait_for_selector("canvas", timeout=30000)
        time.sleep(1.8)

        box = page.locator(".main-content").bounding_box()
        if not box:
            raise RuntimeError("Could not find .main-content")
        page.screenshot(path=str(raw), clip=box)
        browser.close()

    if Image:
        img = Image.open(raw)
        max_w = 1160
        if img.width > max_w:
            ratio = max_w / img.width
            img = img.resize((max_w, int(img.height * ratio)), Image.Resampling.LANCZOS)
        img.save(OUT, optimize=True)
        raw.unlink()
    else:
        raw.rename(OUT)

    print(f"Wrote {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
