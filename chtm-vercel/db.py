import os
import psycopg2
import psycopg2.extras
from flask import g

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def get_db():
    """Returns a request-scoped Postgres connection (dict-style rows)."""
    if "db" not in g:
        g.db = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    return g.db


def close_db(e=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)
