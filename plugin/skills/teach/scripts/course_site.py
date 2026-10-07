#!/usr/bin/env python3
"""Собрать сайт курса для публикации одним артефактом.

Один курс = один артефакт: главная страница (миссия, критерии успеха, уроки,
справочники, что дальше) и внутренние страницы — уроки и справочники как есть.
Пути внутри артефакта повторяют пути лаборатории, поэтому относительные ссылки
уроков (../../../assets/lab.css, ../reference/…) работают без правок.

    python3 course_site.py --root ЛАБОРАТОРИЯ --course SLUG --out ПАПКА

В ПАПКЕ появляются index.html (страница артефакта) и копии файлов; в stdout —
JSON для параметра `files` инструмента Artifact: {"опубликованный/путь": "исходный/путь"}.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import sys
from pathlib import Path

TITLE_RE = re.compile(r"<title>(.*?)</title>", re.S | re.I)
WIN_RE = re.compile(r'<p class="win">(.*?)</p>', re.S | re.I)
CHECK_RE = re.compile(r"^- \[( |x|X)\] (.+)$")


def page_title(path: Path) -> str:
    m = TITLE_RE.search(path.read_text(encoding="utf-8"))
    return html.unescape(m.group(1).strip()) if m else path.stem


def page_win(path: Path) -> str:
    m = WIN_RE.search(path.read_text(encoding="utf-8"))
    if not m:
        return ""
    text = re.sub(r"<[^>]+>", "", m.group(1))
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def read_mission(course: Path) -> dict:
    data = {"name": course.name, "why": "", "checks": []}
    p = course / "MISSION.md"
    if not p.exists():
        return data
    section = None
    why: list[str] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            name = re.sub(r"^#\s*Миссия:\s*", "", line).strip()
            data["name"] = name[:1].upper() + name[1:]
        elif line.startswith("## "):
            section = line[3:].strip().lower()
        elif section == "зачем" and line.strip():
            why.append(line.strip())
        elif section and section.startswith("успех"):
            m = CHECK_RE.match(line.strip())
            if m:
                data["checks"].append((m.group(1).lower() == "x", m.group(2).strip()))
    data["why"] = " ".join(why)
    return data


def next_step(root: Path, slug: str) -> str:
    p = root / "dashboard.md"
    if not p.exists():
        return ""
    for line in p.read_text(encoding="utf-8").splitlines():
        if line.startswith("|") and f"courses/{slug}/" in line:
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells:
                text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", cells[-1])
                return re.sub(r"`([^`]+)`", r"\1", text)
    return ""


def build(root: Path, slug: str, out: Path) -> dict[str, str]:
    course = root / "courses" / slug
    if not course.is_dir():
        raise SystemExit(f"Ошибка: нет курса {course}")
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    files: dict[str, str] = {}

    def copy(src: Path, rel: str) -> None:
        dst = out / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        files[rel] = str(dst)

    for name in ("lab.css", "quiz.js"):
        src = root / "assets" / name
        if src.exists():
            copy(src, f"assets/{name}")
    lessons = sorted((course / "lessons").glob("*.html")) if (course / "lessons").exists() else []
    refs = sorted((course / "reference").glob("*.html")) if (course / "reference").exists() else []
    for p in lessons:
        copy(p, f"courses/{slug}/lessons/{p.name}")
    for p in refs:
        copy(p, f"courses/{slug}/reference/{p.name}")

    m = read_mission(course)
    done = sum(1 for ok, _ in m["checks"] if ok)
    total = len(m["checks"])
    css = (root / "assets" / "lab.css").read_text(encoding="utf-8") if (root / "assets" / "lab.css").exists() else ""
    e = html.escape

    lesson_items = "\n".join(
        f'<li><a href="courses/{slug}/lessons/{p.name}"><span class="num">{e(p.name[:4])}</span>'
        f'<span class="t">{e(page_title(p))}</span></a>'
        + (f'<p class="w">{e(page_win(p))}</p>' if page_win(p) else "")
        + "</li>"
        for p in lessons
    ) or '<li class="empty">Уроков пока нет. Скажите в чате «первый урок по ' + e(slug) + "».</li>"
    ref_items = "\n".join(
        f'<li><a href="courses/{slug}/reference/{p.name}">{e(page_title(p))}</a></li>' for p in refs
    ) or '<li class="empty">Справочники появятся после уроков.</li>'
    check_items = "\n".join(
        f'<li class="{"ok" if ok else ""}"><span class="box" aria-hidden="true">{"✓" if ok else ""}</span>{e(text)}</li>'
        for ok, text in m["checks"]
    )
    step = next_step(root, slug)

    page = f"""<title>Курс {e(slug)}</title>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500&family=IBM+Plex+Sans:wght@400;600&family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&display=swap">
<style>
{css}
.hub h1 {{ margin-bottom: .6rem; }}
.hub .why {{ color: var(--muted); }}
.progress {{ font-family: var(--mono); font-size: .8rem; color: var(--muted); margin: 0 0 .6rem; }}
.bar {{ height: 6px; background: var(--rule); border-radius: 3px; overflow: hidden; margin: 0 0 1rem; }}
.bar span {{ display: block; height: 100%; background: var(--accent); }}
.checks, .lessons, .refs {{ list-style: none; padding: 0; margin: 0 0 1rem; font-family: var(--sans); }}
.checks li {{ display: flex; gap: .7rem; align-items: baseline; padding: .4rem 0; border-bottom: 1px solid var(--rule); font-size: .92rem; }}
.checks .box {{ flex: 0 0 1.1rem; height: 1.1rem; border: 1px solid var(--muted); border-radius: 3px; font-size: .75rem; line-height: 1.1rem; text-align: center; color: var(--ok); }}
.checks li.ok .box {{ border-color: var(--ok); background: var(--ok-soft); }}
.lessons li {{ padding: .7rem 0; border-bottom: 1px solid var(--rule); }}
.lessons a {{ display: flex; gap: .8rem; align-items: baseline; text-decoration: none; color: var(--ink); font-weight: 600; }}
.lessons a:hover .t {{ color: var(--accent); text-decoration: underline; }}
.lessons .num {{ font-family: var(--mono); font-weight: 400; font-size: .8rem; color: var(--accent); }}
.lessons .w {{ margin: .25rem 0 0 2.6rem; font-size: .88rem; color: var(--muted); }}
.refs li {{ padding: .35rem 0; }}
.empty {{ color: var(--muted); font-size: .9rem; }}
.next {{ font-family: var(--sans); background: var(--accent-soft); border-left: 3px solid var(--accent); padding: .75rem 1rem; }}
</style>
<main class="hub">
  <p class="kicker">Учебная лаборатория · курс {e(slug)}</p>
  <h1>{e(m["name"])}</h1>
  <p class="why">{e(m["why"])}</p>

  <h2>Критерии успеха</h2>
  <p class="progress">Достигнуто {done} из {total}</p>
  <div class="bar" role="progressbar" aria-valuemin="0" aria-valuemax="{total}" aria-valuenow="{done}"><span style="width:{(100 * done // total) if total else 0}%"></span></div>
  <ul class="checks">
{check_items}
  </ul>

  <h2>Уроки</h2>
  <ul class="lessons">
{lesson_items}
  </ul>

  <h2>Справочники</h2>
  <ul class="refs">
{ref_items}
  </ul>
""" + (f'\n  <h2>Что дальше</h2>\n  <p class="next">{e(step)}</p>\n' if step else "") + f"""
  <footer>Новый урок — скажите в чате «следующий урок по {e(slug)}». Курс обновляется по этой же ссылке.</footer>
</main>
"""
    (out / "index.html").write_text(page, encoding="utf-8")
    return files


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", required=True)
    ap.add_argument("--course", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    files = build(Path(a.root), a.course, Path(a.out))
    print(json.dumps(files, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
