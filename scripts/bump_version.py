"""Bump the release version everywhere it lives.

Usage: python scripts/bump_version.py 0.3.1

docs_rag/__init__.py is the single source of truth (pyproject.toml reads it
dynamically). server.json repeats the version twice for the MCP registry, so
this script rewrites both of its fields to match.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INIT = ROOT / "docs_rag" / "__init__.py"
SERVER_JSON = ROOT / "server.json"
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")


def main():
    if len(sys.argv) != 2 or not SEMVER.match(sys.argv[1]):
        sys.exit("usage: python scripts/bump_version.py MAJOR.MINOR.PATCH")
    new = sys.argv[1]

    init_text = INIT.read_text()
    old = re.search(r'__version__ = "([^"]+)"', init_text).group(1)
    INIT.write_text(init_text.replace(f'__version__ = "{old}"', f'__version__ = "{new}"'))

    server = json.loads(SERVER_JSON.read_text())
    server["version"] = new
    for package in server.get("packages", []):
        package["version"] = new
    SERVER_JSON.write_text(json.dumps(server, indent=2) + "\n")

    print(f"{old} -> {new} (docs_rag/__init__.py, server.json)")


if __name__ == "__main__":
    main()
