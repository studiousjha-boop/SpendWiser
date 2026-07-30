---

## Project overview

SpendWiser is a lightweight personal expense tracker built with Flask and SQLite.

---

## Architecture
```
spendly/\n• app.py              # All routes — single file, no blueprints\n• database/\n    ••• db.py           # SQLite helpers: get_db(), init_db(), seed_db()\n• templates/\n    ••• base.html       # Shared layout — all templates must extend this\n    ••• *.html          # One template per page\n• static/\n    ••• css/\n        ••• style.css       # Global styles\n        ••• landing.css     # Landing-page-only styles\n    ••• js/\n        ••• main.js         # Vanilla JS only\n• requirements.txt
```

**Where things belong:**\n- New routes → `app.py` only, no blueprints\n- DB logic → `database/db.py` only, never inline in routes\n- New pages → new `.html` file extending `base.html`\n- Page-specific styles → new `.css` file, not inline `<style>` tags\n
---