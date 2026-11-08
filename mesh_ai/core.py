"""Local-first, transparent two-agent Mesh AI demo for Ghost.

This is a deterministic assistant scaffold, not an actual LLM or conscious agent.
It stores only explicit notes, lessons, and user-approved rules.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import sqlite3
import threading
import uuid
from pathlib import Path
from typing import Any

DATA_DIR = Path(os.environ.get("GHOST_MESH_HOME", Path(__file__).resolve().parent))
DB_PATH = DATA_DIR / "mesh_memory.sqlite3"
COLORS = {"blue", "green", "amber", "pink", "violet", "red", "teal"}
MAX_NOTE_TEXT = 8000
MAX_PROMPT = 4000


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def connect() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    with connect() as db:
        db.executescript("""
        CREATE TABLE IF NOT EXISTS notes (
          id TEXT PRIMARY KEY, title TEXT NOT NULL, body TEXT NOT NULL,
          color TEXT NOT NULL, size INTEGER NOT NULL, importance INTEGER NOT NULL,
          tags TEXT NOT NULL, kind TEXT NOT NULL DEFAULT 'note', created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL, last_accessed TEXT NOT NULL, archived INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS rules (
          id TEXT PRIMARY KEY, body TEXT NOT NULL, source TEXT NOT NULL,
          status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL, updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS turns (
          id TEXT PRIMARY KEY, prompt TEXT NOT NULL, alpha TEXT NOT NULL, beta TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS agent_state (
          agent TEXT PRIMARY KEY, frustration REAL NOT NULL DEFAULT 0,
          last_error TEXT NOT NULL DEFAULT '', updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS feedback (
          id TEXT PRIMARY KEY, agent TEXT NOT NULL, correction TEXT NOT NULL,
          created_at TEXT NOT NULL
        );
        """)
        for agent in ("Alpha", "Beta"):
            db.execute("INSERT OR IGNORE INTO agent_state(agent, updated_at) VALUES (?, ?)", (agent, now()))


def clean_text(value: Any, maximum: int, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} peab olema tekst")
    value = value.strip()
    if not value or len(value) > maximum:
        raise ValueError(f"{field} peab olema 1–{maximum} märki")
    return value


def _note(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["tags"] = json.loads(item["tags"])
    item["archived"] = bool(item["archived"])
    item["memory_strength"] = round(memory_strength(item), 3)
    return item


def memory_strength(note: dict[str, Any]) -> float:
    """Explainable decay score; it never deletes or edits the note automatically."""
    try:
        last = dt.datetime.fromisoformat(note["last_accessed"])
        days = max(0.0, (dt.datetime.now(dt.timezone.utc) - last).total_seconds() / 86400)
    except (ValueError, KeyError):
        days = 0
    importance = max(1, min(5, int(note.get("importance", 3)))) / 5
    return importance * math.exp(-days / 45)


def create_note(title: Any, body: Any, color: Any = "blue", size: Any = 16,
                importance: Any = 3, tags: Any = None, kind: str = "note") -> dict[str, Any]:
    title = clean_text(title, 120, "Pealkiri")
    body = clean_text(body, MAX_NOTE_TEXT, "Märge")
    if color not in COLORS:
        raise ValueError("Tundmatu värv")
    try:
        size = int(size); importance = int(importance)
    except (TypeError, ValueError):
        raise ValueError("Suurus ja tähtsus peavad olema täisarvud")
    if not 10 <= size <= 32 or not 1 <= importance <= 5:
        raise ValueError("Suurus peab olema 10–32 ja tähtsus 1–5")
    if not isinstance(tags, list) or len(tags) > 12 or any(not isinstance(t, str) for t in tags):
        raise ValueError("Sildid peavad olema kuni 12 tekstist koosnev loend")
    stamp = now(); item_id = str(uuid.uuid4())
    with connect() as db:
        db.execute("INSERT INTO notes VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)",
                   (item_id, title, body, color, size, importance,
                    json.dumps([t.strip()[:32] for t in tags if t.strip()], ensure_ascii=False),
                    kind, stamp, stamp, stamp))
        row = db.execute("SELECT * FROM notes WHERE id=?", (item_id,)).fetchone()
    return _note(row)


def list_notes(include_archived: bool = False) -> list[dict[str, Any]]:
    with connect() as db:
        rows = db.execute("SELECT * FROM notes WHERE archived=? ORDER BY updated_at DESC",
                          (1 if include_archived else 0,)).fetchall()
    return [_note(r) for r in rows]


def archive_note(note_id: str, archived: bool = True) -> bool:
    with connect() as db:
        cur = db.execute("UPDATE notes SET archived=?, updated_at=? WHERE id=?",
                         (int(archived), now(), note_id))
    return cur.rowcount > 0


def forget_note(note_id: str) -> bool:
    """Explicit forget: archive rather than irreversibly erase user data."""
    return archive_note(note_id, True)


def retrieve_memory(query: str, limit: int = 5) -> list[dict[str, Any]]:
    terms = {w.lower() for w in re.findall(r"[\wõäöüšž]+", query) if len(w) > 2}
    candidates = list_notes()
    scored = []
    for item in candidates:
        haystack = (item["title"] + " " + item["body"] + " " + " ".join(item["tags"])).lower()
        overlap = sum(1 for term in terms if term in haystack)
        score = overlap + memory_strength(item) * 0.25
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    selected = [item for _, item in scored[:limit]]
    if selected:
        stamp = now()
        with connect() as db:
            db.executemany("UPDATE notes SET last_accessed=? WHERE id=?",
                           [(stamp, item["id"]) for item in selected])
    return selected


def get_rules() -> list[dict[str, Any]]:
    with connect() as db:
        return [dict(r) for r in db.execute("SELECT * FROM rules ORDER BY created_at DESC").fetchall()]


def suggest_rule(body: Any) -> dict[str, Any]:
    body = clean_text(body, 500, "Harjumus")
    stamp = now(); rule_id = str(uuid.uuid4())
    with connect() as db:
        db.execute("INSERT INTO rules(id,body,source,status,created_at,updated_at) VALUES (?,?,?,'pending',?,?)",
                   (rule_id, body, "user suggestion", stamp, stamp))
        return dict(db.execute("SELECT * FROM rules WHERE id=?", (rule_id,)).fetchone())


def set_rule(rule_id: str, action: str) -> bool:
    if action not in {"approved", "rejected", "pending"}:
        raise ValueError("Vigane reegli olek")
    with connect() as db:
        cur = db.execute("UPDATE rules SET status=?,updated_at=? WHERE id=?",
                         (action, now(), rule_id))
    return cur.rowcount > 0


def approved_rules() -> list[str]:
    return [r["body"] for r in get_rules() if r["status"] == "approved"]


def _agent_state() -> dict[str, dict[str, Any]]:
    with connect() as db:
        return {r["agent"]: dict(r) for r in db.execute("SELECT * FROM agent_state")}


def think(prompt: Any) -> dict[str, Any]:
    prompt = clean_text(prompt, MAX_PROMPT, "Küsimus")
    memories = retrieve_memory(prompt)
    rules = approved_rules()
    memory_text = "\n".join(f"- {n['title']}: {n['body'][:300]}" for n in memories) or "Sobivat salvestatud mälu ei leitud."
    rule_text = "\n".join(f"- {r}" for r in rules) or "Kasutaja kinnitatud reegleid pole."
    # Transparent demo agents: responses are structured reflections, not LLM output.
    alpha = f"Vaade A: sõnasta eesmärk ja kontrolli kinnitatud reegleid.\nKüsimus: {prompt}\nKasutatav mälu:\n{memory_text}\nReeglid:\n{rule_text}"
    beta = f"Vaade B: otsi lünki ja paku kontrollitav järgmine samm.\nVõimalik kontroll: mida saaks enne otsust väikese testiga kinnitada?\nMäluallikaid: {len(memories)}."
    stamp = now()
    with connect() as db:
        db.execute("INSERT INTO turns VALUES (?,?,?,?,?)", (str(uuid.uuid4()), prompt, alpha, beta, stamp))
    return {"agents": {"Alpha": alpha, "Beta": beta}, "memories": memories,
            "approved_rules": rules, "note": "Need on läbipaistvad reeglipõhised demo-vastused, mitte päris LLM-i mõtlemine."}


def record_feedback(agent: Any, correction: Any) -> dict[str, Any]:
    if agent not in {"Alpha", "Beta"}:
        raise ValueError("Agent peab olema Alpha või Beta")
    correction = clean_text(correction, 2000, "Parandus")
    stamp = now()
    with connect() as db:
        db.execute("INSERT INTO feedback VALUES (?,?,?,?)", (str(uuid.uuid4()), agent, correction, stamp))
        row = db.execute("SELECT frustration FROM agent_state WHERE agent=?", (agent,)).fetchone()
        # “Frustration” is a UI signal calculated from reported errors, not an emotion.
        level = min(1.0, float(row[0]) * 0.7 + 0.3)
        db.execute("UPDATE agent_state SET frustration=?,last_error=?,updated_at=? WHERE agent=?",
                   (level, correction[:300], stamp, agent))
    create_note(f"Õppetund {agent}", correction, "amber", 16, 4, ["tagasiside", agent.lower()], "lesson")
    return {"agent": agent, "frustration_signal": level,
            "explanation": "See on vea/tagasiside indikaator, mitte päris viha ega tunne."}


def state() -> dict[str, Any]:
    return {"name": "Ghost Mesh AI (local)", "network": "local-only",
            "ai_provider": "demo-rules", "agents": _agent_state(),
            "notes": len(list_notes()), "rules": get_rules()}

init_db()
