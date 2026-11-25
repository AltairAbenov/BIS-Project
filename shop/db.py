"""
Database connection (whole team).
The database is created from every file in schema/ in name order:
01_shop.sql (weeks 9-12), 02_..., 03_... - each new feature adds its own file,
so two branches never edit the same schema file.
"""
import glob
import os
import sqlite3

from flask import current_app, g


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_exc=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def schema_files(project_dir):
    return sorted(glob.glob(os.path.join(project_dir, "schema", "*.sql")))


def init_db(database, project_dir):
    """Create the database on first run; later schema files are added when they appear."""
    con = sqlite3.connect(database)
    con.execute("CREATE TABLE IF NOT EXISTS _schema_files (name TEXT PRIMARY KEY)")
    done = {r[0] for r in con.execute("SELECT name FROM _schema_files")}
    for path in schema_files(project_dir):
        name = os.path.basename(path)
        if name in done:
            continue
        with open(path, encoding="utf-8") as f:
            con.executescript(f.read())
        con.execute("INSERT INTO _schema_files (name) VALUES (?)", (name,))
        con.commit()
    con.close()
