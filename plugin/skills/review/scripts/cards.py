#!/usr/bin/env python3
"""Карточки интервального повторения для учебной лаборатории.

Хранилище — review/cards.md в корне лаборатории (папка с dashboard.md).
Расписание — система Лейтнера: у карточки есть коробка 1..6, у коробки
интервал в днях. Оценка ответа двигает карточку между коробками.

Команды:
  due     [--topic T] [--summary] [--quiet]   карточки к повторению на сегодня
  add     --topic T --q ВОПРОС --a ОТВЕТ       новая карточка (коробка 1, завтра)
  grade   ID again|hard|good|easy              оценить ответ и перенести срок
  stats                                        сводка по темам и коробкам

Общие флаги: --root ПУТЬ (корень лаборатории), --today ГГГГ-ММ-ДД (для тестов).
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

INTERVALS = {1: 1, 2: 3, 3: 7, 4: 16, 5: 35, 6: 80}
MAX_BOX = max(INTERVALS)
KEYS = ("topic", "q", "a", "box", "due", "last")
HEADER = (
    "# Карточки повторения\n\n"
    "Файл ведёт скрипт cards.py из плагина lab (скилл review). Формат карточки:\n\n"
    "```\n## c0001\ntopic: harness\nq: вопрос\na: ответ\nbox: 1\ndue: 2026-10-08\nlast: 2026-10-07\n```\n"
)
CARD_RE = re.compile(r"^## (c\d{4,})\s*$")
KEY_RE = re.compile(r"^(topic|q|a|box|due|last):\s?(.*)$")


class LabNotFound(Exception):
    pass


def find_root(explicit: str | None) -> Path:
    candidates = []
    if explicit:
        candidates.append(Path(explicit))
    if os.environ.get("LAB_ROOT"):
        candidates.append(Path(os.environ["LAB_ROOT"]))
    cwd = Path.cwd().resolve()
    candidates.extend([cwd, *cwd.parents])
    for c in candidates:
        if (c / "dashboard.md").is_file() and (c / "courses").is_dir():
            return c
    raise LabNotFound("Лаборатория не найдена: нужна папка с dashboard.md и courses/")


def cards_path(root: Path) -> Path:
    return root / "review" / "cards.md"


def parse(text: str) -> tuple[str, list[dict]]:
    """Возвращает (шапка до первой карточки, список карточек)."""
    head_lines: list[str] = []
    cards: list[dict] = []
    cur: dict | None = None
    last_key: str | None = None
    in_fence = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_fence = not in_fence
        m = None if in_fence else CARD_RE.match(line)
        if m:
            cur = {"id": m.group(1)}
            cards.append(cur)
            last_key = None
            continue
        if cur is None:
            head_lines.append(line)
            continue
        km = KEY_RE.match(line)
        if km:
            last_key = km.group(1)
            cur[last_key] = km.group(2).strip()
        elif line.strip() and last_key in ("q", "a"):
            cur[last_key] += "\n" + line.rstrip()
    for c in cards:
        c["box"] = min(max(int(c.get("box") or 1), 1), MAX_BOX)
        c.setdefault("topic", "")
        c.setdefault("q", "")
        c.setdefault("a", "")
        c.setdefault("due", "")
        c.setdefault("last", "")
    head = "\n".join(head_lines).rstrip() + "\n" if head_lines else HEADER
    return head, cards


def render(head: str, cards: list[dict]) -> str:
    out = [head.rstrip(), ""]
    for c in cards:
        out.append(f"## {c['id']}")
        for k in KEYS:
            out.append(f"{k}: {c[k]}")
        out.append("")
    return "\n".join(out).rstrip() + "\n"


def load(root: Path) -> tuple[str, list[dict]]:
    p = cards_path(root)
    if not p.exists():
        return HEADER, []
    return parse(p.read_text(encoding="utf-8"))


def save(root: Path, head: str, cards: list[dict]) -> None:
    p = cards_path(root)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(render(head, cards), encoding="utf-8")


def is_due(card: dict, today: dt.date) -> bool:
    try:
        return dt.date.fromisoformat(card["due"]) <= today
    except ValueError:
        return True  # битая дата — показать, чтобы её починили


def schedule(card: dict, grade: str, today: dt.date) -> None:
    box = card["box"]
    if grade == "again":
        box, days = 1, INTERVALS[1]
    elif grade == "hard":
        days = max(1, INTERVALS[box] // 2)
    elif grade == "good":
        box = min(box + 1, MAX_BOX)
        days = INTERVALS[box]
    elif grade == "easy":
        box = min(box + 2, MAX_BOX)
        days = INTERVALS[box]
    else:
        raise ValueError(grade)
    card["box"] = box
    card["last"] = today.isoformat()
    card["due"] = (today + dt.timedelta(days=days)).isoformat()


def next_id(cards: list[dict]) -> str:
    n = max((int(c["id"][1:]) for c in cards), default=0) + 1
    return f"c{n:04d}"


def cmd_due(root, args, today):
    _, cards = load(root)
    due = [c for c in cards if is_due(c, today) and (not args.topic or c["topic"] == args.topic)]
    if args.summary:
        if not due:
            if not args.quiet:
                print("Повторение: на сегодня карточек нет.")
            return 0
        by_topic: dict[str, int] = {}
        for c in due:
            by_topic[c["topic"]] = by_topic.get(c["topic"], 0) + 1
        parts = ", ".join(f"{t}: {n}" for t, n in sorted(by_topic.items()))
        print(f"Повторение: карточек к сегодняшнему дню — {len(due)} ({parts}). Начни сессию с review.")
        return 0
    if not due:
        print("На сегодня карточек нет.")
        return 0
    for c in due:
        print(f"## {c['id']} · {c['topic']} · коробка {c['box']} · срок {c['due']}")
        print(f"q: {c['q']}")
        print(f"a: {c['a']}")
        print()
    return 0


def cmd_add(root, args, today):
    head, cards = load(root)
    for field in ("q", "a"):
        if not getattr(args, field).strip():
            print(f"Ошибка: пустое поле --{field}", file=sys.stderr)
            return 2
    card = {
        "id": next_id(cards),
        "topic": args.topic,
        "q": args.q.strip(),
        "a": args.a.strip(),
        "box": 1,
        "due": (today + dt.timedelta(days=INTERVALS[1])).isoformat(),
        "last": today.isoformat(),
    }
    cards.append(card)
    save(root, head, cards)
    print(f"Добавлена {card['id']} ({card['topic']}), первое повторение {card['due']}")
    return 0


def cmd_grade(root, args, today):
    head, cards = load(root)
    for c in cards:
        if c["id"] == args.id:
            schedule(c, args.grade, today)
            save(root, head, cards)
            print(f"{c['id']}: коробка {c['box']}, следующее повторение {c['due']}")
            return 0
    print(f"Ошибка: карточка {args.id} не найдена", file=sys.stderr)
    return 2


def cmd_stats(root, args, today):
    _, cards = load(root)
    if not cards:
        print("Карточек пока нет.")
        return 0
    topics: dict[str, dict] = {}
    for c in cards:
        t = topics.setdefault(c["topic"], {"total": 0, "due": 0, "boxes": [0] * MAX_BOX})
        t["total"] += 1
        t["due"] += is_due(c, today)
        t["boxes"][c["box"] - 1] += 1
    print("тема | всего | к повторению | по коробкам 1..6")
    for name, t in sorted(topics.items()):
        print(f"{name} | {t['total']} | {t['due']} | {' '.join(map(str, t['boxes']))}")
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--root")
    p.add_argument("--today")
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("due")
    d.add_argument("--topic")
    d.add_argument("--summary", action="store_true")
    d.add_argument("--quiet", action="store_true", help="молчать, если лаборатории нет или карточек нет")
    a = sub.add_parser("add")
    a.add_argument("--topic", required=True)
    a.add_argument("--q", required=True)
    a.add_argument("--a", required=True)
    g = sub.add_parser("grade")
    g.add_argument("id")
    g.add_argument("grade", choices=["again", "hard", "good", "easy"])
    sub.add_parser("stats")
    args = p.parse_args(argv)
    today = dt.date.fromisoformat(args.today) if args.today else dt.date.today()
    try:
        root = find_root(args.root)
    except LabNotFound as e:
        if getattr(args, "quiet", False):
            return 0
        print(f"Ошибка: {e}", file=sys.stderr)
        return 2
    return {"due": cmd_due, "add": cmd_add, "grade": cmd_grade, "stats": cmd_stats}[args.cmd](root, args, today)


if __name__ == "__main__":
    sys.exit(main())
