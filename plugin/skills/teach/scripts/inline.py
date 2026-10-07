#!/usr/bin/env python3
"""Собрать самодостаточную копию урока: встроить локальные CSS и JS.

Нужен, когда урок показывают одним файлом (например, в приложении Claude):
относительные ссылки на ../../../assets/ там не открываются.

    python3 inline.py УРОК.html ВЫХОД.html

Внешние ссылки (http/https) не трогает. Исходный урок не меняет.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

LINK_RE = re.compile(r'<link\s+[^>]*rel=["\']stylesheet["\'][^>]*href=["\']([^"\']+)["\'][^>]*>', re.I)
SCRIPT_RE = re.compile(r'<script\s+[^>]*src=["\']([^"\']+)["\'][^>]*>\s*</script>', re.I)


def is_local(ref: str) -> bool:
    return not re.match(r"^(https?:)?//", ref)


def inline(src: Path) -> str:
    html = src.read_text(encoding="utf-8")
    base = src.parent

    def css(m: re.Match) -> str:
        ref = m.group(1)
        path = base / ref
        if not is_local(ref) or not path.is_file():
            return m.group(0)
        return "<style>\n" + path.read_text(encoding="utf-8") + "\n</style>"

    def js(m: re.Match) -> str:
        ref = m.group(1)
        path = base / ref
        if not is_local(ref) or not path.is_file():
            return m.group(0)
        code = path.read_text(encoding="utf-8").replace("</script", "<\\/script")
        return "<script>\n" + code + "\n</script>"

    return SCRIPT_RE.sub(js, LINK_RE.sub(css, html))


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src, out = Path(argv[0]), Path(argv[1])
    if not src.is_file():
        print(f"Ошибка: нет файла {src}", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(inline(src), encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
