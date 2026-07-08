from datetime import datetime, timezone

from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash

from database.db import get_db, init_db, seed_db

app = Flask(__name__)
# In production, this should be loaded from environment variables
app.secret_key = "spendwiser-dev-secret-key-12345"

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
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if not name or not email or not password:
            return render_template("register.html", error="All fields are required.")
            
        if len(password) < 8:
            return render_template("register.html", error="Password must be at least 8 characters long.")
            
        conn = get_db()
        cur = conn.cursor()
        
        # Check if user already exists
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return render_template("register.html", error="An account with this email already exists.")
            
        # Insert new user
        password_hash = generate_password_hash(password)
        try:
            cur.execute(
                "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                (name, email, password_hash)
            )
            user_id = cur.lastrowid
            conn.commit()
        except Exception as e:
            conn.rollback()
            conn.close()
            return render_template("register.html", error=f"Database error: {str(e)}")
            
        conn.close()
        
        # Store user details in session to log in
        session["user_id"] = user_id
        session["user_name"] = name
        return redirect(url_for("profile"))
        
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


@app.context_processor
def inject_now():
    return {"now": datetime.now(timezone.utc)}

# ------------------------------------------------------------------ #
# Implemented and placeholder routes                                 #
# ------------------------------------------------------------------ #

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))
        
    conn = get_db()
    cur = conn.cursor()
    
    # Fetch user info
    cur.execute("SELECT name, email, created_at FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user:
        session.clear()
        conn.close()
        return redirect(url_for("login"))
        
    # Format created_at date nicely
    created_at_str = user["created_at"]
    join_date = created_at_str
    try:
        dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        join_date = dt.strftime("%B %d, %Y")
    except Exception:
        try:
            # Fallback parsing YYYY-MM-DD HH:MM:SS
            dt = datetime.strptime(created_at_str.split()[0], "%Y-%m-%d")
            join_date = dt.strftime("%B %d, %Y")
        except Exception:
            pass
            
    # Fetch user's expenses
    cur.execute(
        "SELECT id, amount, category, date, description FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user_id,)
    )
    expenses = [dict(row) for row in cur.fetchall()]
    conn.close()
    
    total_spending = sum(exp["amount"] for exp in expenses)
    total_count = len(expenses)
    avg_spending = total_spending / total_count if total_count > 0 else 0.0
    
    # Calculate category breakdown
    category_totals = {}
    for exp in expenses:
        cat = exp["category"]
        category_totals[cat] = category_totals.get(cat, 0.0) + exp["amount"]
        
    category_breakdown = []
    for cat, total in category_totals.items():
        pct = (total / total_spending * 100) if total_spending > 0 else 0
        category_breakdown.append({
            "category": cat,
            "total": total,
            "pct": pct
        })
    # Sort categories by total spending descending
    category_breakdown.sort(key=lambda x: x["total"], reverse=True)
    
    recent_expenses = expenses[:5]
    
    return render_template(
        "profile.html",
        user=user,
        join_date=join_date,
        total_spending=total_spending,
        total_count=total_count,
        avg_spending=avg_spending,
        category_breakdown=category_breakdown,
        recent_expenses=recent_expenses
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)

