#!/usr/bin/env python3
"""
Reorganiza el directorio raíz:
- Mueve archivos .md del raíz a docs/ (excepto README.md y ARQUITECTURA_CARPETAS.md)
- Mueve archivos .sql del raíz a db/sql/
No toca subdirectorios.
"""

from __future__ import annotations

from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SQL_DIR = ROOT / "db" / "sql"

EXCLUDE_MD = {"README.md", "ARQUITECTURA_CARPETAS.md"}


def main() -> None:
    DOCS.mkdir(parents=True, exist_ok=True)
    SQL_DIR.mkdir(parents=True, exist_ok=True)

    moved = []
    for p in ROOT.iterdir():
        if not p.is_file():
            continue
        name = p.name
        if p.suffix.lower() == ".md" and name not in EXCLUDE_MD:
            dest = DOCS / name
            shutil.move(str(p), str(dest))
            moved.append((str(p), str(dest)))
        elif p.suffix.lower() == ".sql":
            dest = SQL_DIR / name
            shutil.move(str(p), str(dest))
            moved.append((str(p), str(dest)))

    print(f"Archivos movidos: {len(moved)}")
    for a, b in moved:
        print(f"- {a} -> {b}")


if __name__ == "__main__":
    main()



