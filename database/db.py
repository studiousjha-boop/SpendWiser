# Database helpers for SpendWiser / Spendly

"""Implementation of the data layer (Step 1).

Provides three public functions:
- ``get_db()`` – returns a SQLite connection with row_factory set to ``sqlite3.Row``
  and foreign‑key enforcement enabled.
- ``init_db()`` – creates the ``users`` and ``expenses`` tables if they do not exist.
- ``seed_db()`` – inserts a demo user and a handful of sample expenses (one per
  required category) only once.

The spec lives in ``.claude/specs/01-database-setup.md`` and defines the exact
schema and constraints.
"""

import sqlite3
from datetime import date
from pathlib import Path
from werkzeug.security import generate_password_hash
from flask import current_app

# Path to the SQLite file – placed in the project root alongside ``main.py``.
_DB_PATH = Path(__file__).resolve().parents[1] / "spendly.db"


def get_db():
    """Return a SQLite connection.

    The connection uses ``sqlite3.Row`` for dictionary‑style access and enables
    foreign‑key constraints.
    """
    db_path = _DB_PATH
    try:
        # Check if we are running in a Flask app context with TESTING enabled
        if current_app and current_app.config.get("TESTING"):
            # Use the configured test database path
            db_path = Path(current_app.config.get("DATABASE", _DB_PATH))
    except RuntimeError:
        # Outside of Flask application context
        pass

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the required tables if they are missing.

    This function is safe to call multiple times – ``CREATE TABLE IF NOT EXISTS``
    ensures idempotence.
    """
    conn = get_db()
    cur = conn.cursor()
    # Users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        )
        """
    )
    # Expenses table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            date TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


def seed_db():
    """Insert a demo user and a set of sample expenses.

    The function checks whether ``users`` already contains data; if so it
    returns early to avoid duplicate seeding on subsequent runs.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] > 0:
        conn.close()
        return

    # Insert demo user with a hashed password.
    password_hash = generate_password_hash("demo123")
    cur.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?,?,?)",
        ("Demo User", "demo@spendly.com", password_hash),
    )
    user_id = cur.lastrowid

    # Sample expenses – eight rows covering the required categories.
    current_month = date.today().strftime("%Y-%m")
    expenses = [
        (user_id, 45.99, "Food", f"{current_month}-02", "Groceries"),
        (user_id, 15.00, "Transport", f"{current_month}-03", "Bus ticket"),
        (user_id, 120.50, "Bills", f"{current_month}-04", "Electricity bill"),
        (user_id, 60.00, "Health", f"{current_month}-05", "Pharmacy"),
        (user_id, 30.75, "Entertainment", f"{current_month}-06", "Movie"),
        (user_id, 200.00, "Shopping", f"{current_month}-07", "Clothes"),
        (user_id, 12.34, "Other", f"{current_month}-08", "Miscellaneous"),
        (user_id, 8.99, "Food", f"{current_month}-09", "Coffee"),
    ]
    cur.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?,?,?,?,?)",
        expenses,
    )
    conn.commit()
    conn.close()
