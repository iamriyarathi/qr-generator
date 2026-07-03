"""
Database access layer.

Every query in this module uses parameter placeholders ("?") rather than
string formatting, which is what protects the application against SQL
injection. Never build queries with f-strings / % / .format() on
user-supplied data.
"""
import sqlite3
from datetime import date

from flask import current_app, g


def get_db():
    """Return a request-scoped SQLite connection."""
    if "db" not in g:
        g.db = sqlite3.connect(
            current_app.config["DATABASE_PATH"],
            detect_types=sqlite3.PARSE_DECLTYPES,
        )
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db(app):
    """Create tables if they do not already exist and register teardown."""
    with app.app_context():
        db = get_db()
        with open(
            __file__.replace("db.py", "schema.sql"), "r", encoding="utf-8"
        ) as f:
            db.executescript(f.read())
        db.commit()
    app.teardown_appcontext(close_db)


# ----------------------------------------------------------------------
# CRUD helpers
# ----------------------------------------------------------------------

def insert_history(qr_type, user_input, qr_data, file_name, customization_json):
    db = get_db()
    cur = db.execute(
        """INSERT INTO history (qr_type, user_input, qr_data, file_name, customization)
           VALUES (?, ?, ?, ?, ?)""",
        (qr_type, user_input, qr_data, file_name, customization_json),
    )
    db.commit()
    return cur.lastrowid


def get_history_item(item_id):
    db = get_db()
    return db.execute("SELECT * FROM history WHERE id = ?", (item_id,)).fetchone()


def list_history(search=None, qr_type=None, limit=200):
    db = get_db()
    query = "SELECT * FROM history WHERE 1=1"
    params = []
    if search:
        query += " AND (user_input LIKE ? OR qr_type LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    if qr_type:
        query += " AND qr_type = ?"
        params.append(qr_type)
    query += " ORDER BY created_date DESC LIMIT ?"
    params.append(limit)
    return db.execute(query, params).fetchall()


def delete_history_item(item_id):
    db = get_db()
    cur = db.execute("DELETE FROM history WHERE id = ?", (item_id,))
    db.commit()
    return cur.rowcount


def increment_download_count(item_id):
    db = get_db()
    db.execute(
        "UPDATE history SET download_count = download_count + 1 WHERE id = ?",
        (item_id,),
    )
    db.commit()


def get_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) AS c FROM history").fetchone()["c"]

    today_str = date.today().isoformat()
    today_count = db.execute(
        "SELECT COUNT(*) AS c FROM history WHERE DATE(created_date) = ?",
        (today_str,),
    ).fetchone()["c"]

    most_used_row = db.execute(
        """SELECT qr_type, COUNT(*) AS c FROM history
           GROUP BY qr_type ORDER BY c DESC LIMIT 1"""
    ).fetchone()
    most_used = most_used_row["qr_type"] if most_used_row else "—"

    total_downloads = db.execute(
        "SELECT COALESCE(SUM(download_count), 0) AS c FROM history"
    ).fetchone()["c"]

    by_type = db.execute(
        """SELECT qr_type, COUNT(*) AS c FROM history
           GROUP BY qr_type ORDER BY c DESC"""
    ).fetchall()

    recent = db.execute(
        "SELECT * FROM history ORDER BY created_date DESC LIMIT 8"
    ).fetchall()

    return {
        "total": total,
        "today": today_count,
        "most_used_type": most_used,
        "total_downloads": total_downloads,
        "by_type": [dict(r) for r in by_type],
        "recent": [dict(r) for r in recent],
    }
