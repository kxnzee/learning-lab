import datetime as dt
import importlib.util
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "plugin" / "skills" / "review" / "scripts" / "cards.py"
spec = importlib.util.spec_from_file_location("cards", SCRIPT)
cards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cards)

TODAY = "2026-10-07"


@pytest.fixture
def lab(tmp_path):
    (tmp_path / "dashboard.md").write_text("# Дашборд\n", encoding="utf-8")
    (tmp_path / "courses").mkdir()
    return tmp_path


def run(lab, *args):
    return cards.main(["--root", str(lab), "--today", TODAY, *args])


def load(lab):
    return cards.load(lab)[1]


def test_add_creates_file_and_schedules_tomorrow(lab):
    assert run(lab, "add", "--topic", "harness", "--q", "Что такое агентный цикл?", "--a", "Цикл модель→инструмент→результат") == 0
    [c] = load(lab)
    assert c["id"] == "c0001"
    assert c["box"] == 1
    assert c["due"] == "2026-10-08"


def test_ids_increment(lab):
    run(lab, "add", "--topic", "sql", "--q", "q1", "--a", "a1")
    run(lab, "add", "--topic", "sql", "--q", "q2", "--a", "a2")
    assert [c["id"] for c in load(lab)] == ["c0001", "c0002"]


@pytest.mark.parametrize(
    "start_box,grade,box,days",
    [
        (3, "again", 1, 1),
        (3, "hard", 3, 3),   # половина интервала коробки 3 (7 // 2)
        (3, "good", 4, 16),
        (3, "easy", 5, 35),
        (6, "good", 6, 80),  # потолок
        (5, "easy", 6, 80),
        (1, "hard", 1, 1),   # минимум один день
    ],
)
def test_schedule(start_box, grade, box, days):
    card = {"box": start_box, "due": "", "last": ""}
    today = dt.date.fromisoformat(TODAY)
    cards.schedule(card, grade, today)
    assert card["box"] == box
    assert card["due"] == (today + dt.timedelta(days=days)).isoformat()
    assert card["last"] == TODAY


def test_grade_updates_file(lab):
    run(lab, "add", "--topic", "sql", "--q", "q", "--a", "a")
    assert cards.main(["--root", str(lab), "--today", "2026-10-08", "grade", "c0001", "good"]) == 0
    [c] = load(lab)
    assert (c["box"], c["due"]) == (2, "2026-10-11")


def test_grade_unknown_id(lab):
    assert run(lab, "grade", "c9999", "good") == 2


def test_due_filters_by_date_and_topic(lab, capsys):
    run(lab, "add", "--topic", "sql", "--q", "sql-q", "--a", "a")
    run(lab, "add", "--topic", "a2ui", "--q", "a2ui-q", "--a", "a")
    capsys.readouterr()
    cards.main(["--root", str(lab), "--today", TODAY, "due"])
    assert "На сегодня карточек нет" in capsys.readouterr().out
    cards.main(["--root", str(lab), "--today", "2026-10-08", "due", "--topic", "sql"])
    out = capsys.readouterr().out
    assert "sql-q" in out and "a2ui-q" not in out


def test_summary_and_quiet(lab, capsys):
    cards.main(["--root", str(lab), "--today", TODAY, "due", "--summary", "--quiet"])
    assert capsys.readouterr().out == ""
    run(lab, "add", "--topic", "sql", "--q", "q", "--a", "a")
    capsys.readouterr()
    cards.main(["--root", str(lab), "--today", "2026-10-09", "due", "--summary", "--quiet"])
    assert "к сегодняшнему дню — 1" in capsys.readouterr().out


def test_quiet_outside_lab_is_silent(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("LAB_ROOT", raising=False)
    assert cards.main(["due", "--summary", "--quiet"]) == 0
    assert capsys.readouterr().out == ""


def test_root_found_from_subdirectory(lab, monkeypatch):
    sub = lab / "courses" / "sql" / "lab"
    sub.mkdir(parents=True)
    monkeypatch.chdir(sub)
    monkeypatch.delenv("LAB_ROOT", raising=False)
    assert cards.find_root(None) == lab


def test_roundtrip_keeps_header_multiline_and_hand_edits(lab):
    text = (
        cards.HEADER
        + "\n## c0003\ntopic: harness\nq: Зачем нужен\nцикл?\na: ответ\nbox: 9\ndue: 2026-10-01\nlast: 2026-09-30\n"
    )
    (lab / "review").mkdir()
    (lab / "review" / "cards.md").write_text(text, encoding="utf-8")
    head, parsed = cards.load(lab)
    assert len(parsed) == 1  # пример в шапке внутри ``` не считается карточкой
    c = parsed[0]
    assert c["q"] == "Зачем нужен\nцикл?"
    assert c["box"] == 6  # битое значение зажато в допустимый диапазон
    cards.save(lab, head, parsed)
    assert cards.load(lab)[1][0]["q"] == "Зачем нужен\nцикл?"
    assert "Формат карточки" in (lab / "review" / "cards.md").read_text(encoding="utf-8")


def test_empty_answer_rejected(lab):
    assert run(lab, "add", "--topic", "sql", "--q", "q", "--a", "  ") == 2
