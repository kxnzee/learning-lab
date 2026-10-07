#!/usr/bin/env python3
"""Собрать самодостаточную копию урока: встроить локальные CSS и JS.

Нужен, когда урок показывают одним файлом (например, в приложении Claude):
относительные ссылки на ../../../assets/ там не открываются.

    python3 inline.py УРОК.html ВЫХОД.html             самодостаточный HTML
    python3 inline.py --artifact УРОК.html ВЫХОД.html  то же без <!doctype>/<html>/<head>/<body>:
                                                      публикация через Artifact сама оборачивает страницу
    --map ОТНОСИТЕЛЬНАЯ_ССЫЛКА=URL  (можно несколько) заменить ссылку на урок или справочник
                                    адресом его артефакта; незаменённые относительные ссылки
                                    в режиме --artifact превращаются в текст, список — в stderr

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


def to_fragment(html: str) -> str:
    """Оставить title, ссылки на шрифты, стили, тело и скрипты — без обёртки документа."""
    head = re.search(r"<head[^>]*>(.*?)</head>", html, re.S | re.I)
    body = re.search(r"<body[^>]*>(.*?)</body>", html, re.S | re.I)
    if not head or not body:
        return html
    keep = re.findall(r"<title>.*?</title>|<link[^>]+>|<style>.*?</style>|<script>.*?</script>", head.group(1), re.S | re.I)
    keep = [k for k in keep if not k.lower().startswith("<link") or "stylesheet" in k.lower()]
    return "\n".join(keep) + "\n" + body.group(1).strip() + "\n"


HREF_RE = re.compile(r'<a\s+href="([^"]+)"([^>]*)>(.*?)</a>', re.S)


def remap_links(html: str, mapping: dict[str, str], drop_unmapped: bool) -> tuple[str, list[str]]:
    dropped: list[str] = []

    def sub(m: re.Match) -> str:
        ref, rest, text = m.group(1), m.group(2), m.group(3)
        if ref in mapping:
            return f'<a href="{mapping[ref]}"{rest}>{text}</a>'
        if drop_unmapped and is_local(ref) and not ref.startswith("#"):
            dropped.append(ref)
            return text
        return m.group(0)

    return HREF_RE.sub(sub, html), dropped


def main(argv: list[str]) -> int:
    argv = list(argv)
    artifact = "--artifact" in argv
    if artifact:
        argv.remove("--artifact")
    mapping: dict[str, str] = {}
    while "--map" in argv:
        i = argv.index("--map")
        pair = argv[i + 1] if i + 1 < len(argv) else ""
        if "=" not in pair:
            print("Ошибка: --map ждёт ССЫЛКА=URL", file=sys.stderr)
            return 2
        k, v = pair.split("=", 1)
        mapping[k] = v
        del argv[i : i + 2]
    if len(argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src, out = Path(argv[0]), Path(argv[1])
    if not src.is_file():
        print(f"Ошибка: нет файла {src}", file=sys.stderr)
        return 2
    out.parent.mkdir(parents=True, exist_ok=True)
    html = inline(src)
    html, dropped = remap_links(html, mapping, drop_unmapped=artifact)
    for ref in dropped:
        print(f"ссылка без артефакта стала текстом: {ref}", file=sys.stderr)
    out.write_text(to_fragment(html) if artifact else html, encoding="utf-8")
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
