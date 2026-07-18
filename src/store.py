# store.py - SQLite: generated-puzzle cache, per-day progress, stats

import json
import os
import sqlite3

from gi.repository import GLib


def _db_path():
    d = os.path.join(GLib.get_user_data_dir(), "nectar")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, "nectar.db")


class Store:
    def __init__(self):
        self._con = sqlite3.connect(_db_path())
        self._con.row_factory = sqlite3.Row
        self._con.executescript(
            """
            PRAGMA journal_mode=WAL;
            CREATE TABLE IF NOT EXISTS puzzles (
                date TEXT PRIMARY KEY,
                letters TEXT NOT NULL,
                answers TEXT NOT NULL       -- JSON array
            );
            CREATE TABLE IF NOT EXISTS found (
                date TEXT NOT NULL,
                word TEXT NOT NULL,
                PRIMARY KEY (date, word)
            );
            """
        )
        self._con.commit()

    def cached_puzzle(self, date_str):
        row = self._con.execute(
            "SELECT letters, answers FROM puzzles WHERE date=?", (date_str,)
        ).fetchone()
        if row is None:
            return None
        return row["letters"], json.loads(row["answers"])

    def cache_puzzle(self, date_str, letters, answers):
        self._con.execute(
            "INSERT OR REPLACE INTO puzzles (date, letters, answers) "
            "VALUES (?,?,?)",
            (date_str, letters, json.dumps(sorted(answers))),
        )
        self._con.commit()

    def found_words(self, date_str):
        return [
            r["word"] for r in self._con.execute(
                "SELECT word FROM found WHERE date=? ORDER BY word",
                (date_str,),
            )
        ]

    def add_found(self, date_str, word):
        self._con.execute(
            "INSERT OR IGNORE INTO found (date, word) VALUES (?,?)",
            (date_str, word),
        )
        self._con.commit()

    def days_played(self):
        return self._con.execute(
            "SELECT COUNT(DISTINCT date) AS n FROM found"
        ).fetchone()["n"]

    def total_words(self):
        return self._con.execute(
            "SELECT COUNT(*) AS n FROM found"
        ).fetchone()["n"]
