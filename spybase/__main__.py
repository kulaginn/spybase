"""Командная строка: python -m spybase collect [файл.json]  — загрузить объявления в базу."""

from __future__ import annotations

import sys

from . import collector, db
from .api import DB_PATH


def main(argv: list[str]) -> int:
    if len(argv) < 1 or argv[0] != "collect":
        print("Использование: python -m spybase collect [data/demo_ads.json]")
        return 2
    path = argv[1] if len(argv) > 1 else "data/demo_ads.json"
    con = db.connect(DB_PATH)
    rep = collector.collect(con, collector.load_json(path), source=path)
    print(f"получено {rep.received}, новых {rep.new_ads}, обновлено {rep.updated}, отброшено {rep.rejected}")
    for r in rep.reasons:
        print("  отброшено:", r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
