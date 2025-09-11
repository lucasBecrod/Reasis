#!/usr/bin/env python3
"""
Mueve todos los archivos .md desde docs/ al directorio raíz.
"""
from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path('.').resolve()
DOCS = ROOT / 'docs'


def main() -> None:
    if not DOCS.exists():
        print("No existe carpeta docs/")
        return
    moved = []
    for p in DOCS.glob('*.md'):
        dest = ROOT / p.name
        if dest.exists():
            dest = ROOT / f"{p.stem}_from_docs{p.suffix}"
        shutil.move(str(p), str(dest))
        moved.append((str(p), str(dest)))
    print(f"MD movidos a raíz: {len(moved)}")
    for a, b in moved:
        print(f"- {a} -> {b}")


if __name__ == '__main__':
    main()



