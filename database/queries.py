"""Query helpers for SpendWiser profile page.

Each function accepts optional ``date_from`` / ``date_to`` parameters to
narrow results to a date range.  When both are omitted the behaviour is
identical to the unfiltered case.
"""

from datetime import datetime, timedelta
from database.db import get_db

# ------------------------------------------------------------------- #
# Helpers                                                             #
# ------------------------------------------------------------------- #


def _build_date_filter(date_from: str | None, date_to: str | None) -> tuple[str, list]:
    """Return a (clause, params) tuple for appending to a ``WHERE`` clause.

    At most one bound is required; the returned SQL uses ``BETWEEN`` when
    both ends are provided and individual ``>=`` / ``<=`` otherwise.
    """
    clause = ""
    params: list = []
    if date_from and date_to:
        clause = " AND date BETWEEN ? AND ?"
        params = [date_from, date_to]
    elif date_from:
        clause = " AND date >= ?"
        params = [date_from]
    elif date_to:
        clause = " AND date <= ?"
        params = [date_to]
    return clause, params


def _summarise_pct(items: list[dict]) -> list[dict]:
    """Compute integer percentages that sum to 100.

    Each item must have a ``"total"`` key.  The largest value absorbs the
    rounding remainder so the list always sums to 100.
    """
    grand = sum(item["total"] for item in items)
    if grand == 0:
        return items

    remainder = 100
    for i, item in enumerate(items):
        if i == len(items) - 1:
            item["pct"] = remainder
        else:
            pct = round(item["total"] / grand * 100)
            item["pct"] = pct
            remainder -= pct
    return items


# ------------------------------------------------------------------- #
# Public helpers                                                      #
# ------------------------------------------------------------------- #


def get_user_by_id(user_id: int) -> dict | None:
    """Look up a user by primary key.

    Returns a dict with keys ``name``, ``email``, ``member_since``
    (formatted as "Month YYYY") or ``None`` if not found.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name, email, created_at FROM users WHERE id = ?",
            (user_id,),
        )
        row = cur.fetchone()
        if not row:
            return None

        # Parse member_since from created_at timestamp
        created = row["created_at"]
        try:
            dt = datetime.fromisoformat(created.replace("Z", "+00:00"))
        except Exception:
            try:
                dt = datetime.strptime(created.split()[0], "%Y-%m-%d")
            except Exception:
                dt = None

        return {
            "name": row["name"],
            "email": row["email"],
            "member_since": dt.strftime("%B %Y") if dt else created,
        }
    finally:
        conn.close()


def get_summary_stats(
    user_id: int,
    date_from: str | None = None,
    date_to: str | None = None,
) -> dict:
    """Return aggregate spending stats for a user.

    Results are a dict with keys ``total_spent``, ``transaction_count``,
    ``top_category`` (or ``"—"`` when there are no expenses).
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        date_clause, params = _build_date_filter(date_from, date_to)

        cur.execute(
            f"SELECT SUM(amount), COUNT(*) FROM expenses WHERE user_id = ?{date_clause}",
            [user_id] + params,
        )
        row = cur.fetchone()
        total = row[0] if row and row[0] else 0.0
        count = row[1] if row and row[1] else 0

        top_category = "—"
        if count > 0:
            cur.execute(
                f"SELECT category FROM expenses WHERE user_id = ?{date_clause} GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
                [user_id] + params,
            )
            top_row = cur.fetchone()
            if top_row:
                top_category = top_row["category"]

        return {
            "total_spent": total,
            "transaction_count": count,
            "top_category": top_category,
        }
    finally:
        conn.close()


def get_recent_transactions(
    user_id: int,
    limit: int = 10,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Return the most recent expenses for a user.

    Each item contains ``id``, ``amount``, ``category``, ``date``,
    ``description``.  Ordered newest-first.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        date_clause, params = _build_date_filter(date_from, date_to)

        cur.execute(
            f"SELECT id, amount, category, date, description FROM expenses WHERE user_id = ?{date_clause} ORDER BY date DESC, id DESC LIMIT ?",
            [user_id] + params + [limit],
        )
        return [dict(row) for row in cur.fetchall()]
    finally:
        conn.close()


def get_category_breakdown(
    user_id: int,
    date_from: str | None = None,
    date_to: str | None = None,
) -> list[dict]:
    """Return per-category totals with integer percentages.

    Each item has keys ``name``, ``total`` (numeric), ``pct`` (integer
    0-100).  Ordered by ``total`` descending.  Percentages always sum to
    100; the largest category absorbs any rounding remainder.
    """
    conn = get_db()
    try:
        cur = conn.cursor()
        date_clause, params = _build_date_filter(date_from, date_to)

        cur.execute(
            f"SELECT category, SUM(amount) as total FROM expenses WHERE user_id = ?{date_clause} GROUP BY category ORDER BY total DESC",
            [user_id] + params,
        )
        rows = [{"name": row["category"], "total": row["total"]} for row in cur.fetchall()]
        return _summarise_pct(rows)
    finally:
        conn.close()
