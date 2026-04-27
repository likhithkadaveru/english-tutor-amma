"""
Database module — dual-mode:
  - Local dev:  SQLite  (no extra setup)
  - Production: PostgreSQL via DATABASE_URL  (Supabase free tier)

Set DATABASE_URL in .env / Streamlit secrets to switch to PostgreSQL.
Leave it unset to use SQLite.
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import date, timedelta
from pathlib import Path

# ── Backend detection ─────────────────────────────────────────────────────────

def _db_url():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        try:
            import streamlit as st
            url = st.secrets.get("DATABASE_URL", "")
        except Exception:
            pass
    return url or None


def _is_postgres() -> bool:
    url = _db_url()
    return bool(url and url.startswith(("postgres", "postgresql")))


# ── SQLite helpers ────────────────────────────────────────────────────────────

_SQLITE_PATH = Path("english_tutor.db")


@contextmanager
def _sqlite_conn():
    conn = sqlite3.connect(_SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


# ── PostgreSQL helpers ────────────────────────────────────────────────────────

@contextmanager
def _pg_conn():
    import psycopg2
    import psycopg2.extras
    from urllib.parse import urlparse, unquote

    parsed = urlparse(_db_url())
    conn = psycopg2.connect(
        host=parsed.hostname,
        port=parsed.port or 5432,
        user=unquote(parsed.username or ""),
        password=unquote(parsed.password or ""),
        dbname=(parsed.path or "/postgres").lstrip("/"),
        sslmode="require",
    )
    conn.autocommit = False
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _pg_cursor(conn):
    import psycopg2.extras
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


# ── Unified connection context manager ───────────────────────────────────────

@contextmanager
def _conn():
    if _is_postgres():
        with _pg_conn() as conn:
            yield conn
    else:
        with _sqlite_conn() as conn:
            yield conn


def _cursor(conn):
    if _is_postgres():
        return _pg_cursor(conn)
    return conn.cursor()


def _fetchall(cursor):
    rows = cursor.fetchall()
    if not rows:
        return []
    # sqlite3.Row and psycopg2 RealDictRow both support dict()
    return [dict(r) for r in rows]


def _fetchone(cursor):
    row = cursor.fetchone()
    return dict(row) if row else None


# ── Schema ────────────────────────────────────────────────────────────────────

_SQLITE_SCHEMA = """
CREATE TABLE IF NOT EXISTS learner_profile (
    id INTEGER PRIMARY KEY,
    name TEXT DEFAULT 'Amma',
    current_level TEXT DEFAULT 'beginner',
    telugu_support_level TEXT DEFAULT 'medium',
    common_mistakes TEXT DEFAULT '[]',
    vocabulary_learnt TEXT DEFAULT '[]',
    grammar_topics_practised TEXT DEFAULT '[]',
    confidence_trend TEXT DEFAULT '[]',
    favourite_topics TEXT DEFAULT '[]',
    total_sessions INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    last_practice_date TEXT,
    cached_task_date TEXT,
    cached_task_json TEXT
);

CREATE TABLE IF NOT EXISTS practice_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date TEXT NOT NULL,
    task_type TEXT,
    task_given TEXT,
    user_answer TEXT,
    ai_feedback TEXT,
    corrected_sentences TEXT,
    new_vocabulary TEXT DEFAULT '[]',
    grammar_focus TEXT,
    confidence_level TEXT,
    weak_area_detected TEXT,
    session_notes TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT NOT NULL,
    meaning TEXT,
    example_sentence TEXT,
    telugu_meaning TEXT,
    date_learnt TEXT,
    times_practised INTEGER DEFAULT 0
);
"""

_PG_SCHEMA = """
CREATE TABLE IF NOT EXISTS learner_profile (
    id SERIAL PRIMARY KEY,
    name TEXT DEFAULT 'Amma',
    current_level TEXT DEFAULT 'beginner',
    telugu_support_level TEXT DEFAULT 'medium',
    common_mistakes TEXT DEFAULT '[]',
    vocabulary_learnt TEXT DEFAULT '[]',
    grammar_topics_practised TEXT DEFAULT '[]',
    confidence_trend TEXT DEFAULT '[]',
    favourite_topics TEXT DEFAULT '[]',
    total_sessions INTEGER DEFAULT 0,
    streak INTEGER DEFAULT 0,
    last_practice_date TEXT,
    cached_task_date TEXT,
    cached_task_json TEXT
);

CREATE TABLE IF NOT EXISTS practice_sessions (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    task_type TEXT,
    task_given TEXT,
    user_answer TEXT,
    ai_feedback TEXT,
    corrected_sentences TEXT,
    new_vocabulary TEXT DEFAULT '[]',
    grammar_focus TEXT,
    confidence_level TEXT,
    weak_area_detected TEXT,
    session_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS vocabulary (
    id SERIAL PRIMARY KEY,
    word TEXT NOT NULL,
    meaning TEXT,
    example_sentence TEXT,
    telugu_meaning TEXT,
    date_learnt TEXT,
    times_practised INTEGER DEFAULT 0
);
"""


def init_db():
    with _conn() as conn:
        c = _cursor(conn)
        if _is_postgres():
            for statement in _PG_SCHEMA.strip().split(";"):
                stmt = statement.strip()
                if stmt:
                    c.execute(stmt)
            c.execute("SELECT COUNT(*) AS cnt FROM learner_profile")
            row = _fetchone(c)
        else:
            conn.executescript(_SQLITE_SCHEMA)
            c = _cursor(conn)
            c.execute("SELECT COUNT(*) AS cnt FROM learner_profile")
            row = _fetchone(c)

        if row and int(row.get("cnt", 0) or 0) == 0:
            c.execute("INSERT INTO learner_profile (name) VALUES ('Amma')")


# ── JSON field helpers ────────────────────────────────────────────────────────

_JSON_FIELDS = [
    "common_mistakes", "vocabulary_learnt",
    "grammar_topics_practised", "confidence_trend", "favourite_topics",
]


def _parse_profile(profile: dict):
    for field in _JSON_FIELDS:
        val = profile.get(field, "[]")
        if isinstance(val, str):
            try:
                profile[field] = json.loads(val)
            except Exception:
                profile[field] = []
    return profile


# ── Public API ────────────────────────────────────────────────────────────────

import streamlit as st

@st.cache_data(ttl=30)
def get_learner_profile() -> dict:
    with _conn() as conn:
        c = _cursor(conn)
        c.execute("SELECT * FROM learner_profile WHERE id = 1")
        row = _fetchone(c)
    return _parse_profile(row) if row else {}


def update_learner_profile(updates: dict):
    with _conn() as conn:
        c = _cursor(conn)
        serialised = {
            k: (json.dumps(v) if k in _JSON_FIELDS and isinstance(v, list) else v)
            for k, v in updates.items()
        }
        if _is_postgres():
            set_clause = ", ".join(f"{k} = %s" for k in serialised)
            c.execute(
                f"UPDATE learner_profile SET {set_clause} WHERE id = 1",
                list(serialised.values()),
            )
        else:
            set_clause = ", ".join(f"{k} = ?" for k in serialised)
            c.execute(
                f"UPDATE learner_profile SET {set_clause} WHERE id = 1",
                list(serialised.values()),
            )


def save_session(session_data: dict):
    if isinstance(session_data.get("new_vocabulary"), list):
        session_data["new_vocabulary"] = json.dumps(session_data["new_vocabulary"])

    values = (
        session_data.get("date", str(date.today())),
        session_data.get("task_type", ""),
        session_data.get("task_given", ""),
        session_data.get("user_answer", ""),
        session_data.get("ai_feedback", ""),
        session_data.get("corrected_sentences", ""),
        session_data.get("new_vocabulary", "[]"),
        session_data.get("grammar_focus", ""),
        session_data.get("confidence_level", ""),
        session_data.get("weak_area_detected", ""),
        session_data.get("session_notes", ""),
    )

    sql_pg = """
        INSERT INTO practice_sessions
            (date, task_type, task_given, user_answer, ai_feedback,
             corrected_sentences, new_vocabulary, grammar_focus,
             confidence_level, weak_area_detected, session_notes)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """
    sql_sq = sql_pg.replace("%s", "?")

    with _conn() as conn:
        c = _cursor(conn)
        c.execute(sql_pg if _is_postgres() else sql_sq, values)


def save_vocabulary(words: list):
    with _conn() as conn:
        c = _cursor(conn)
        today = str(date.today())
        for w in words:
            word_text = (w.get("word") or "").strip()
            if not word_text:
                continue
            if _is_postgres():
                c.execute(
                    "SELECT id FROM vocabulary WHERE LOWER(word) = LOWER(%s)", (word_text,)
                )
            else:
                c.execute(
                    "SELECT id FROM vocabulary WHERE LOWER(word) = LOWER(?)", (word_text,)
                )
            if not _fetchone(c):
                if _is_postgres():
                    c.execute(
                        """INSERT INTO vocabulary
                           (word, meaning, example_sentence, telugu_meaning, date_learnt)
                           VALUES (%s,%s,%s,%s,%s)""",
                        (word_text, w.get("meaning",""), w.get("example_sentence",""),
                         w.get("telugu_meaning",""), today),
                    )
                else:
                    c.execute(
                        """INSERT INTO vocabulary
                           (word, meaning, example_sentence, telugu_meaning, date_learnt)
                           VALUES (?,?,?,?,?)""",
                        (word_text, w.get("meaning",""), w.get("example_sentence",""),
                         w.get("telugu_meaning",""), today),
                    )


def _sessions_to_dicts(rows: list) -> list:
    result = []
    for row in rows:
        s = dict(row)
        try:
            s["new_vocabulary"] = json.loads(s.get("new_vocabulary") or "[]")
        except Exception:
            s["new_vocabulary"] = []
        result.append(s)
    return result


@st.cache_data(ttl=30)
def get_recent_sessions(n: int = 10) -> list:
    with _conn() as conn:
        c = _cursor(conn)
        if _is_postgres():
            c.execute(
                "SELECT * FROM practice_sessions ORDER BY created_at DESC LIMIT %s", (n,)
            )
        else:
            c.execute(
                "SELECT * FROM practice_sessions ORDER BY created_at DESC LIMIT ?", (n,)
            )
        rows = _fetchall(c)
    return _sessions_to_dicts(rows)


def get_today_sessions() -> list:
    today = str(date.today())
    with _conn() as conn:
        c = _cursor(conn)
        ph = "%s" if _is_postgres() else "?"
        c.execute(
            f"SELECT * FROM practice_sessions WHERE date = {ph} ORDER BY created_at DESC",
            (today,),
        )
        rows = _fetchall(c)
    return _sessions_to_dicts(rows)


@st.cache_data(ttl=60)
def get_vocabulary_list() -> list:
    with _conn() as conn:
        c = _cursor(conn)
        c.execute("SELECT * FROM vocabulary ORDER BY date_learnt DESC, id DESC")
        return _fetchall(c)


@st.cache_data(ttl=30)
def get_streak_and_stats() -> dict:
    with _conn() as conn:
        c = _cursor(conn)

        c.execute(
            "SELECT DISTINCT date FROM practice_sessions ORDER BY date DESC"
        )
        dates = [r["date"] for r in _fetchall(c)]

        streak = 0
        today = date.today()
        for i in range(len(dates)):
            if dates[i] == str(today - timedelta(days=i)):
                streak += 1
            else:
                break

        c.execute("SELECT COUNT(*) AS cnt FROM practice_sessions")
        total = int((_fetchone(c) or {}).get("cnt", 0) or 0)

        c.execute("SELECT COUNT(*) AS cnt FROM vocabulary")
        vocab_count = int((_fetchone(c) or {}).get("cnt", 0) or 0)

        c.execute(
            "SELECT COUNT(DISTINCT date) AS cnt FROM practice_sessions "
            "WHERE date::date >= CURRENT_DATE - INTERVAL '7 days'"
            if _is_postgres()
            else
            "SELECT COUNT(DISTINCT date) AS cnt FROM practice_sessions "
            "WHERE date >= date('now', '-7 days')"
        )
        week_days = int((_fetchone(c) or {}).get("cnt", 0) or 0)

        c.execute(
            "SELECT COUNT(DISTINCT date) AS cnt FROM practice_sessions "
            "WHERE date::date >= CURRENT_DATE - INTERVAL '30 days'"
            if _is_postgres()
            else
            "SELECT COUNT(DISTINCT date) AS cnt FROM practice_sessions "
            "WHERE date >= date('now', '-30 days')"
        )
        month_days = int((_fetchone(c) or {}).get("cnt", 0) or 0)

    return {
        "streak": streak,
        "total_sessions": total,
        "vocab_count": vocab_count,
        "week_days": week_days,
        "month_days": month_days,
        "practice_dates": dates,
    }


def get_weak_areas() -> list:
    with _conn() as conn:
        c = _cursor(conn)
        c.execute(
            """
            SELECT weak_area_detected, COUNT(*) AS cnt
            FROM practice_sessions
            WHERE weak_area_detected IS NOT NULL AND weak_area_detected != ''
            GROUP BY weak_area_detected
            ORDER BY cnt DESC
            LIMIT 5
            """
        )
        return [(r["weak_area_detected"], r["cnt"]) for r in _fetchall(c)]


def get_sessions_this_week() -> list:
    with _conn() as conn:
        c = _cursor(conn)
        c.execute(
            "SELECT * FROM practice_sessions "
            "WHERE date::date >= CURRENT_DATE - INTERVAL '7 days' ORDER BY date DESC"
            if _is_postgres()
            else
            "SELECT * FROM practice_sessions "
            "WHERE date >= date('now', '-7 days') ORDER BY date DESC"
        )
        rows = _fetchall(c)
    return _sessions_to_dicts(rows)


# ── Daily task cache (avoid regenerating on every visit) ─────────────────────

def get_cached_task_for_today():
    today = str(date.today())
    with _conn() as conn:
        c = _cursor(conn)
        c.execute(
            "SELECT cached_task_date, cached_task_json FROM learner_profile WHERE id = 1"
        )
        row = _fetchone(c)
    if row and row.get("cached_task_date") == today and row.get("cached_task_json"):
        try:
            return json.loads(row["cached_task_json"])
        except Exception:
            return None
    return None


def save_cached_task_for_today(task: dict):
    today = str(date.today())
    task_json = json.dumps(task)
    with _conn() as conn:
        c = _cursor(conn)
        if _is_postgres():
            c.execute(
                "UPDATE learner_profile SET cached_task_date = %s, cached_task_json = %s WHERE id = 1",
                (today, task_json),
            )
        else:
            c.execute(
                "UPDATE learner_profile SET cached_task_date = ?, cached_task_json = ? WHERE id = 1",
                (today, task_json),
            )


def clear_st_cache():
    """Call after writes so cached reads reflect new data."""
    get_learner_profile.clear()
    get_recent_sessions.clear()
    get_vocabulary_list.clear()
    get_streak_and_stats.clear()
