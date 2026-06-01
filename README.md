# SpendWiser

> Track every rupee. Own your finances.

**SpendWiser** is a personal finance tracker that helps you log expenses, understand your spending patterns, and take control of your financial life — one transaction at a time.

---

## Features

- **Log expenses instantly** — add any expense in seconds: category, amount, date, and description.
- **Understand your patterns** — see exactly where your money goes with category breakdowns and monthly summaries.
- **Filter by time period** — view your spending for any date range: last week, last month, or a custom period.
- **Clean, responsive UI** — works on mobile and desktop, with a calm editorial design.

---

## Tech Stack

- **Backend:** [Flask](https://flask.palletsprojects.com/) 3.1
- **Templating:** [Jinja2](https://jinja.palletsprojects.com/)
- **Database:** SQLite (via Python's built-in `sqlite3` module)
- **Frontend:** Vanilla HTML / CSS / JavaScript
- **Testing:** [pytest](https://docs.pytest.org/) + [pytest-flask](https://pytest-flask.readthedocs.io/)
- **WSGI (dev):** Werkzeug

---

## Project Structure

```
.
├── main.py                  # Flask app + routes
├── requirements.txt         # Python dependencies
├── database/
│   ├── __init__.py
│   └── db.py                # SQLite helpers (get_db, init_db, seed_db)
├── templates/               # Jinja2 templates
│   ├── base.html            # Layout (navbar + footer)
│   ├── landing.html         # Public landing page
│   ├── login.html           # Sign in
│   ├── register.html        # Sign up
│   ├── terms.html           # Terms & Conditions
│   └── privacy.html         # Privacy Policy
├── static/
│   ├── css/style.css        # Site styles
│   └── js/main.js           # Frontend scripts
└── venv/                    # Local virtual environment (not committed)
```

---

## Getting Started

### Prerequisites

- Python **3.10+**
- `git`

### 1. Clone the repository

```bash
git clone https://github.com/studiousjha-boop/SpendWiser.git
cd SpendWiser
```

### 2. Create a virtual environment

**Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the app

```bash
python main.py
```

The development server starts at **http://127.0.0.1:5001**.

---

## Available Routes

| Route                       | Description                | Status            |
| --------------------------- | -------------------------- | ----------------- |
| `GET /`                     | Landing page               | ✅ Live           |
| `GET /register`             | Sign up form               | ✅ Live           |
| `GET /login`                | Sign in form               | ✅ Live           |
| `GET /terms`                | Terms & Conditions         | ✅ Live           |
| `GET /privacy`              | Privacy Policy             | ✅ Live           |
| `GET /logout`               | Sign out                   | 🚧 Step 3         |
| `GET /profile`              | User profile               | 🚧 Step 4         |
| `GET /expenses/add`         | Add a new expense          | 🚧 Step 7         |
| `GET /expenses/<id>/edit`   | Edit an expense            | 🚧 Step 8         |
| `GET /expenses/<id>/delete` | Delete an expense          | 🚧 Step 9         |

---

## Running Tests

The project uses `pytest` with `pytest-flask`. From the project root, with the virtual environment activated:

```bash
pytest
```

Tests live alongside the code; add new ones as you implement each step.

---

## Development Notes

- The dev server runs with `debug=True` — Flask auto-reloads on file changes.
- `database/db.py` is a stub. Implement `get_db()`, `init_db()`, and `seed_db()` in **Step 1** to enable persistence.
- The current year in the footer is injected via a Flask `context_processor` (`inject_now`) — see `main.py`.
- Frontend modal logic (e.g. the *"See How It Works"* demo) uses vanilla JS only — no build step or framework.

---

## Contributing

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -m "Add your feature"`
4. Push to your branch: `git push origin feature/your-feature`
5. Open a Pull Request

---

## License

This project is for educational purposes. All rights reserved by the author.

---

## Contact

Built by [Akshit Jha](https://github.com/studiousjha-boop). For questions or feedback, open an issue on GitHub.
