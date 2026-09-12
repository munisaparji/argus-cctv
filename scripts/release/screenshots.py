"""Regenerate thesis screenshots at 2x DPI using the console's Playwright installation."""

import subprocess

from argus.config import ROOT

if __name__ == "__main__":
    subprocess.run(["node", "browser-check.mjs"], cwd=ROOT / "apps/console", check=True)
