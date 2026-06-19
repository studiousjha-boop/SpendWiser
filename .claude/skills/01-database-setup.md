# Implementation Plan: Database Setup (Step 1)

## Context
The project **SpendWiser/Spendly** currently has a stub `database/db.py` with only comments. The spec `\.claude/specs/01-database-setup.md` defines the required SQLite schema, functions, and integration points. All future features (auth, expenses CRUD) depend on a working data layer, so we must implement:
- `get_db()` – returns a SQLite connection with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`.
- `init_db()` – creates the **users** and **expenses** tables if they do not exist.
- `seed_db()` – inserts a demo user and eight sample expenses (one per required category) only once.

Additionally, `app.py` (actually `main.py`) must import these functions and invoke `init_db()` and `seed_db()` at startup within the Flask application context.

## Files to Modify
- **`database/db.py`** – implement all three functions and add necessary imports (`sqlite3`, `werkzeug.security.generate_password_hash`).
- **`main.py`** – import `get_db`, `init_db`, `seed_db` from `database.db` and call `init_db()` / `seed_db()` inside `with app.app_context():` before the server starts.

## Implementation Steps
1. **Add imports** to `database/db.py`:
   ```python
   import sqlite3
   from pathlib import Path
   from werkzeug.security import generate_password_hash
   ```
2. **Define a module‑level `_DB_PATH`** pointing to `spendly.db` in the project root (use `Path(__file__).resolve().parents[1] / "spendly.db"`).
3. **Implement `get_db()`**:
   - Create a new `sqlite3.Connection` to `_DB_PATH`.
   - Set `row_factory = sqlite3.Row`.
   - Execute `PRAGMA foreign_keys = ON`.
   - Return the connection.
4. **Implement `init_db()`**:
   - Open a connection via `get_db()`.
   - Execute `CREATE TABLE IF NOT EXISTS users (...);` and `CREATE TABLE IF NOT EXISTS expenses (...);` using the schema from the spec (include constraints: primary key, `UNIQUE(email)`, foreign key on `expenses.user_id`).
   - Commit and close.
5. **Implement `seed_db()`**:
   - Open a connection.
   - Check if any rows exist in `users`. If so, return early.
   - Insert the demo user with a hashed password (`generate_password_hash('demo123')`).
   - Retrieve the inserted user's `id`.
   - Define the eight expense rows covering categories **Food, Transport, Bills, Health, Entertainment, Shopping, Other** (duplicate one category to reach eight total) with realistic `amount`, `date` (current month, e.g., `2026-06-05`), and `description`.
   - Insert expenses using parameterized `INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?,?,?,?,?)`.
   - Commit and close.
6. **Update `main.py`**:
   ```python
   from database.db import init_db, seed_db
   
   with app.app_context():
       init_db()
       seed_db()
   ```
   Place this block just before `if __name__ == "__main__":`.
7. **Verification**
   - Run the Flask app (`python main.py`). Verify that `spendly.db` file appears in the project root and contains the two tables.
   - Open a Python REPL, import `get_db`, query `SELECT * FROM users;` and `SELECT * FROM expenses;` to confirm demo data.
   - Run the test suite (`pytest`). All tests should pass (currently there are no DB‑related tests, but the suite must complete without errors).
   - Re‑run the app a second time; ensure `seed_db()` does **not** duplicate the demo user or expenses.

## Acceptance Criteria
- `database/db.py` implements the three functions exactly as described.
- The SQLite file `spendly.db` is created on first run.
- Tables match the schema in the spec, including constraints.
- One demo user exists with a hashed password.
- Eight expense rows exist, spanning the required categories, with dates in `YYYY-MM-DD` format.
- Running the app multiple times does not create duplicate seed data.
- The application starts without raising any exceptions.
- All existing tests (`pytest`) pass.

## Verification Steps (to be executed after implementation)
1. `python main.py` → no traceback, DB file created.
2. In a separate terminal:
   ```bash
   python - <<'PY'
   import sqlite3, pathlib
   db_path = pathlib.Path('spendly.db')
   conn = sqlite3.connect(db_path)
   conn.row_factory = sqlite3.Row
   print('Users:', conn.execute('SELECT id, name, email FROM users').fetchall())
   print('Expenses count:', conn.execute('SELECT COUNT(*) FROM expenses').fetchone()[0])
   PY
   ```
3. `pytest` → exit code 0.
4. Restart the app, repeat step 2, verify row counts unchanged.

---
*Generated based on the spec `\.claude/specs/01-database-setup.md` and current project files.*