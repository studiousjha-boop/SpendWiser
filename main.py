import sqlite3
from datetime import date, datetime, timedelta, timezone
from functools import wraps

from flask import Flask, render_template, request, redirect, url_for, session, flash, abort
from werkzeug.security import check_password_hash

from database.db import (
    get_db, init_db, seed_db, create_user, create_session, get_session, delete_session,
    add_expense as add_expense_db, get_expense as get_expense_db,
    update_expense as update_expense_db, delete_expense as delete_expense_db
)
from database.queries import (
    get_user_by_id, get_summary_stats,
    get_recent_transactions, get_category_breakdown,
)

app = Flask(__name__)
# In production, this should be loaded from environment variables
app.secret_key = "spendwiser-dev-secret-key-12345"


def login_required(f):
    """Decorator to require valid session token for a route."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = session.get("token")
        if not token:
            flash("Please log in to access this page.")
            return redirect(url_for("login"))

        # Verify token and check if session exists
        user_id = get_session(token)
        if not user_id:
            session.clear()
            flash("Session expired. Please log in again.")
            return redirect(url_for("login"))

        # Set user_id in session for use in route handlers
        session["user_id"] = user_id
        return f(*args, **kwargs)
    return decorated_function


with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm_password = request.form.get("confirm_password")

        # Server-side validation
        if not name or not email or not password:
            flash("All fields are required.")
            return render_template("register.html")

        if len(password) < 8:
            flash("Password must be at least 8 characters long.")
            return render_template("register.html")

        if confirm_password is not None and password != confirm_password:
            flash("Passwords do not match.")
            return render_template("register.html")

        # Create user and session token
        try:
            user_id = create_user(name, email, password)
            token = create_session(user_id)

            # Store token in session
            session["token"] = token
            session["user_id"] = user_id
            session["user_name"] = name
            return redirect(url_for("profile"))
        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                flash("An account with this email already exists.")
            else:
                flash(str(e))
            return render_template("register.html")

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if not email or not password:
            return render_template("login.html", error="All fields are required.")

        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name, password_hash FROM users WHERE email = ?", (email,))
        user = cur.fetchone()
        conn.close()

        if user and check_password_hash(user["password_hash"], password):
            # Create a session token in the database
            token = create_session(user["id"])

            # Store token in session
            session["token"] = token
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            return redirect(url_for("profile"))
        else:
            return render_template("login.html", error="Invalid email or password.")

    return render_template("login.html")


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/analytics")
@login_required
def analytics():
    return render_template("analytics.html")


@app.context_processor
def inject_now():
    return {"now": datetime.now(timezone.utc)}

# ------------------------------------------------------------------ #
# Implemented and placeholder routes                                 #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    # Delete session token from database
    token = session.get("token")
    if token:
        delete_session(token)

    # Clear all session data
    session.clear()

    # Redirect to landing page
    return redirect(url_for("landing"))


@app.route("/profile")
@login_required
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    # ------------------------------------------------------------------ #
    # Date filter: read and validate query parameters                    #
    # ------------------------------------------------------------------ #
    date_from = request.args.get("date_from")
    date_to = request.args.get("date_to")

    # Track which preset button should be highlighted (if any)
    active_filter = ""

    # Handle preset quick-select buttons
    preset = request.args.get("preset")
    if preset:
        today = date.today()
        if preset == "this_month":
            date_from = today.replace(day=1).isoformat()
            date_to = today.isoformat()
            active_filter = "this_month"
        elif preset == "last_3_months":
            date_from = (today - timedelta(days=90)).isoformat()
            date_to = today.isoformat()
            active_filter = "last_3_months"
        elif preset == "last_6_months":
            date_from = (today - timedelta(days=180)).isoformat()
            date_to = today.isoformat()
            active_filter = "last_6_months"
        elif preset == "all":
            date_from = None
            date_to = None
            active_filter = "all"

    # Validate ISO date format — treat malformed values as absent
    if date_from:
        try:
            datetime.strptime(date_from, "%Y-%m-%d")
        except ValueError:
            date_from = None
    if date_to:
        try:
            datetime.strptime(date_to, "%Y-%m-%d")
        except ValueError:
            date_to = None

    # Reject inverted ranges
    if date_from and date_to and date_from > date_to:
        flash("Start date must be before end date.")
        date_from = None
        date_to = None

    # ------------------------------------------------------------------ #
    # Fetch data via query helpers                                       #
    # ------------------------------------------------------------------ #
    user = get_user_by_id(user_id)
    if not user:
        session.clear()
        return redirect(url_for("login"))

    stats = get_summary_stats(user_id, date_from, date_to)
    recent = get_recent_transactions(user_id, 5, date_from, date_to)
    breakdown = get_category_breakdown(user_id, date_from, date_to)

    total_spending = stats["total_spent"]
    total_count = stats["transaction_count"]
    avg_spending = total_spending / total_count if total_count > 0 else 0.0

    # Determine active filter highlighting for non-preset cases
    if not active_filter:
        active_filter = "custom" if (date_from or date_to) else "all"

    return render_template(
        "profile.html",
        user=user,
        join_date=user["member_since"],
        total_spending=total_spending,
        total_count=total_count,
        avg_spending=avg_spending,
        category_breakdown=breakdown,
        recent_expenses=recent,
        date_from=date_from,
        date_to=date_to,
        active_filter=active_filter,
    )


CATEGORIES = ["Food", "Transport", "Bills", "Health", "Entertainment", "Shopping", "Other"]


@app.route("/expenses/add", methods=["GET", "POST"])
@login_required
def add_expense():
    user_id = session.get("user_id")
    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid positive amount.")
            return render_template("add_expense.html", categories=CATEGORIES, today=datetime.now().strftime("%Y-%m-%d"))

        if not category or category not in CATEGORIES:
            flash("Please select a valid category.")
            return render_template("add_expense.html", categories=CATEGORIES, today=datetime.now().strftime("%Y-%m-%d"))

        if not date_str:
            flash("Please provide a date.")
            return render_template("add_expense.html", categories=CATEGORIES, today=datetime.now().strftime("%Y-%m-%d"))

        add_expense_db(user_id, amount, category, date_str, description)
        flash("Expense added successfully!")
        return redirect(url_for("profile"))

    today_str = datetime.now().strftime("%Y-%m-%d")
    return render_template("add_expense.html", categories=CATEGORIES, today=today_str)


@app.route("/expenses/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_expense(id):
    user_id = session.get("user_id")
    expense = get_expense_db(id, user_id)
    if not expense:
        abort(404)

    if request.method == "POST":
        amount_str = request.form.get("amount", "").strip()
        category = request.form.get("category", "").strip()
        date_str = request.form.get("date", "").strip()
        description = request.form.get("description", "").strip()

        try:
            amount = float(amount_str)
            if amount <= 0:
                raise ValueError
        except ValueError:
            flash("Please enter a valid positive amount.")
            return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)

        if not category or category not in CATEGORIES:
            flash("Please select a valid category.")
            return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)

        if not date_str:
            flash("Please provide a date.")
            return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)

        update_expense_db(id, user_id, amount, category, date_str, description)
        flash("Expense updated successfully!")
        return redirect(url_for("profile"))

    return render_template("edit_expense.html", expense=expense, categories=CATEGORIES)


@app.route("/expenses/<int:id>/delete", methods=["GET", "POST"])
@login_required
def delete_expense(id):
    user_id = session.get("user_id")
    expense = get_expense_db(id, user_id)
    if not expense:
        abort(404)

    delete_expense_db(id, user_id)
    flash("Expense deleted successfully!")
    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True, port=5001)