# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** (also branded **SpendWiser** — both names appear in the codebase) is a personal finance tracker that helps users log expenses, view category breakdowns, and filter spending by date range. The project is being built incrementally in numbered "steps" (DB setup, auth, expenses CRUD, etc.) — the README's route table marks unimplemented steps as 🚧.

## Running the App

```bash
# Windows
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python main.py        # serves on http://127.0.0.1:5001 with debug=True (auto-reload)
```

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

> **Note:** `python3` is **not** available on this Windows machine — use `python` instead. The previous developer session hit this exact gotcha.

## Running Tests

```bash
pytest                        # full suite
pytest tests/test_foo.py      # single file
pytest -k test_name           # by test name
```

Tests use `pytest` + `pytest-flask`. The `main.py` file is set up to be testable via `pytest-flask`'s fixture conventions; once `database/db.py` is implemented, tests will need an isolated test DB.

## Architecture

### Entry point — `main.py`

A single Flask app, no blueprints. Routes are flat top-level functions:

- **Live:** `/`, `/register`, `/login`, `/terms`, `/privacy`
- **Stubs (return plain strings):** `/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`
- A `@app.context_processor` named `inject_now` exposes `{{ now }}` to all templates — currently used by `base.html` for the footer year. It uses the deprecated `datetime.utcnow()` (warning in logs); switch to `datetime.now(timezone.utc)` when touching it.

### Database — `database/db.py`

A **stub** — students implement three functions here in Step 1:
- `get_db()` — SQLite connection with `row_factory` + foreign keys enabled
- `init_db()` — `CREATE TABLE IF NOT EXISTS` for all tables
- `seed_db()` — sample data for development

The package's `__init__.py` is empty; it exists only to make `database` importable.

### Templates — `templates/`

Jinja2, all extend `base.html`. Block structure:

- `{% block title %}` — page `<title>`
- `{% block head %}` — extra `<head>` content (rare)
- `{% block content %}` — main page body
- `{% block scripts %}` — extra JS at end of body

`base.html` provides the navbar (brand "SpendWiser" + Sign in / Get started), a `<main class="main-content">` wrapper, and the footer (year via `{{ now.year }}`, terms/privacy links, brand mark).

### Styles — `static/css/style.css`

Single hand-written stylesheet, ~730 lines. Organized into comment-banded sections: Variables, Reset, Navbar, Main, Hero, Mock card, Buttons, Features, CTA, Auth, Footer, Responsive, Demo video modal. Uses CSS custom properties defined in `:root` (colors, fonts, radii, max-widths).

**Constraint observed in this project:** when the user asks for visual edits to the hero, change **only** the hero-related CSS classes — leave other sections untouched. The hero uses classes like `.hero`, `.hero-inner`, `.hero-badge`, `.hero-title`, `.hero-subtitle`, `.hero-actions`, `.hero-visual`, `.mock-card`, `.mock-card-chrome`, `.mock-dot`, `.mock-card-body`, `.mock-stats`, `.mock-stat`, `.mock-stat-label`, `.mock-stat-value`, `.mock-stat-delta`, `.mock-stat-sub`, `.mock-bars`, `.mock-bar-row`, `.mock-cat`, `.mock-bar-track`, `.mock-bar`, `.mock-bar-food`, `.mock-bar-travel`, `.mock-bar-bills`.

### Frontend JS — `static/js/main.js`

Currently empty. Page-specific inline scripts (e.g. the demo video modal in `landing.html`) live in their own template's `{% block scripts %}` rather than in `main.js`.

## Conventions

- **No build step.** Pure HTML/CSS/JS served by Flask's static handler.
- **No CSS framework.** Hand-written CSS with custom properties.
- **Fonts:** DM Serif Display (display) + DM Sans (body), loaded from Google Fonts in `base.html`.
- **Currency:** rendered as `₹` (Indian rupee) throughout the mock content.
- **Brand naming inconsistency:** README and navbar use "SpendWiser"; landing page uses "Spendly" (and page titles say "Spendly"). Don't silently change one to match the other without confirming — both may be intentional in different contexts.

## Key Files for Common Edits

| To change… | Edit |
|---|---|
| Routes / add a new page | `main.py` |
| Layout, navbar, footer, fonts | `templates/base.html` |
| Landing page hero / mock card | `templates/landing.html` + `static/css/style.css` (hero block only) |
| Auth forms | `templates/login.html`, `templates/register.html`, `static/css/style.css` (auth block) |
| Color palette / spacing tokens | `static/css/style.css` `:root` |
| DB schema / queries | `database/db.py` (currently a stub) |
