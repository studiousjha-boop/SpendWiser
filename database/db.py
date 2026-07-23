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
from datetime import date, datetime, timedelta
from pathlib import Path
from werkzeug.security import generate_password_hash
from flask import current_app
import secrets

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
    # Wait on lock contention instead of immediately raising
    # "database is locked" (the default busy_timeout is 0).
    conn.execute("PRAGMA busy_timeout = 5000")
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
    # Sessions table for JWT-based authentication
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            token TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            expiry TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        )
        """
    )
    # Refunds table for processing refunds
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS refunds (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            expense_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            reason TEXT,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now')),
            processed_at TEXT,
            FOREIGN KEY(expense_id) REFERENCES expenses(id) ON DELETE CASCADE,
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


def create_user(name: str, email: str, password: str) -> int:
    """Create a new user with a hashed password.

    Args:
        name: User's full name
        email: User's email (must be unique)
        password: Plain-text password to be hashed

    Returns:
        The new user's ID

    Raises:
        sqlite3.IntegrityError: If email already exists (UNIQUE constraint)
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        password_hash = generate_password_hash(password)
        cur.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash)
        )
        user_id = cur.lastrowid
        conn.commit()
        return user_id
    finally:
        conn.close()


def create_session(user_id: int, expiry_minutes: int = 15) -> str:
    """Create a new session token (JWT-like) with specified expiry.

    Args:
        user_id: The ID of the user
        expiry_minutes: Session expiration time in minutes

    Returns:
        The generated session token
    """
    conn = get_db()
    try:
        # Generate a secure random token
        token = secrets.token_hex(32)

        # Calculate expiry time
        expiry = datetime.now() + timedelta(minutes=expiry_minutes)

        cur = conn.cursor()
        cur.execute(
            "INSERT INTO sessions (token, user_id, expiry) VALUES (?, ?, ?)",
            (token, user_id, expiry.isoformat())
        )
        conn.commit()
        return token
    finally:
        conn.close()


def get_session(token: str) -> int | None:
    """Look up a session token to get the associated user_id.

    Args:
        token: The session token to look up

    Returns:
        The user_id if valid and not expired, None otherwise
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT user_id, expiry FROM sessions WHERE token = ?", (token,))
        result = cur.fetchone()
        if not result:
            return None

        user_id, expiry_str = result
        expiry = datetime.fromisoformat(expiry_str)

        # Check if session has expired
        if datetime.now() >= expiry:
            # Session expired, delete it from DB
            cur.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
            return None

        return user_id
    finally:
        conn.close()


def delete_session(token: str) -> None:
    """Delete a session token from the database.

    Args:
        token: The session token to delete
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
    finally:
        conn.close()
