"""Tests for date filter on profile page (Step 6).

Covers the date-filter functionality for GET /profile including:
- No filter (unfiltered view shows all expenses)
- Custom date ranges via date_from / date_to query params
- Quick presets (this_month, last_3_months, last_6_months, all)
- Malformed and inverted date handling
- Empty result sets (zero state)
- Auth guard (unauthenticated redirect)
- All three sections (stats, categories, recent transactions) respect the filter
"""

from datetime import date, timedelta


# ------------------------------------------------------------------ #
# Helpers                                                            #
# ------------------------------------------------------------------ #

def _login(client):
    """Log in the seeded demo user."""
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123",
    })


def _add_expense(client, amount, category, date_str, description):
    """Add an expense via the add_expense route (caller must be logged in)."""
    return client.post("/expenses/add", data={
        "amount": str(amount),
        "category": category,
        "date": date_str,
        "description": description,
    }, follow_redirects=True)


# ================================================================== #
# Auth Guard                                                         #
# ================================================================== #

def test_profile_requires_login(client):
    """Unauthenticated GET /profile redirects to /login."""
    response = client.get("/profile")

    assert response.status_code == 302, "Expected redirect for unauthenticated user"
    assert "/login" in response.location, "Redirect target should be /login"


# ================================================================== #
# Unfiltered View                                                    #
# ================================================================== #

def test_unfiltered_profile_shows_all_expenses(client):
    """GET /profile with no query params returns all seeded expenses."""
    _login(client)
    response = client.get("/profile")

    assert response.status_code == 200

    # Seeded demo user details
    assert b"Demo User" in response.data

    # 8 seeded expenses totalling 493.57
    assert b"493.57" in response.data, "Total spending should be 493.57"
    assert b"8" in response.data or b">8<" in response.data, \
        "Transaction count should be 8"

    # Verify seeded expense descriptions appear in recent transactions
    assert b"Groceries" in response.data
    assert b"Clothes" in response.data
    assert b"Coffee" in response.data
    assert b"Electricity" in response.data or b"Electricity bill" in response.data

    # Verify all seeded categories appear in the breakdown
    assert b"Shopping" in response.data
    assert b"Food" in response.data
    assert b"Bills" in response.data


# ================================================================== #
# Custom Date Range                                                  #
# ================================================================== #

def test_custom_date_range_filters_correctly(client):
    """GET /profile with valid date_from/date_to filters to matching expenses only."""
    _login(client)

    today = date.today()
    # Last day of previous month -- outside the current month
    prev_month_end = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
    _add_expense(client, 99.99, "Shopping", prev_month_end, "Past month item")

    # Filter to current month only (all seeded expenses are in the current month)
    first_of_month = today.replace(day=1).isoformat()
    response = client.get(
        f"/profile?date_from={first_of_month}&date_to={today.isoformat()}"
    )

    assert response.status_code == 200
    # Past-month expense should be excluded
    assert b"Past month item" not in response.data, \
        "Expense from previous month should not appear"
    # All seed data (current month) should still be present
    assert b"493.57" in response.data, "Filtered total should be 493.57 (seed data)"


def test_custom_date_range_excludes_outside_window(client):
    """Filtering to a window that contains no expenses shows zero state."""
    _login(client)
    response = client.get("/profile?date_from=2020-01-01&date_to=2020-01-31")

    assert response.status_code == 200
    # Zero-state indicators in the page
    assert b"No expenses recorded yet" in response.data, \
        "Should show empty recent-transactions message"
    assert b"No expense data available" in response.data, \
        "Should show empty category-breakdown message"


# ================================================================== #
# Presets                                                            #
# ================================================================== #

def test_preset_this_month(client):
    """GET /profile?preset=this_month limits to the current calendar month."""
    _login(client)

    today = date.today()
    prev_month = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")
    _add_expense(client, 50.00, "Food", prev_month, "Last month lunch")

    response = client.get("/profile?preset=this_month")

    assert response.status_code == 200
    # The past-month expense should be filtered out
    assert b"Last month lunch" not in response.data, \
        "Expense from previous month must not appear with this_month preset"
    # Seed data is all in the current month
    assert b"493.57" in response.data, "Total spending should be 493.57"
    assert b"Coffee" in response.data, "Seed expense Coffee should be visible"


def test_preset_last_3_months(client):
    """GET /profile?preset=last_3_months limits to trailing 90 days."""
    _login(client)

    old_date = (date.today() - timedelta(days=91)).isoformat()
    _add_expense(client, 30.00, "Other", old_date, "Over 90 days old")

    response = client.get("/profile?preset=last_3_months")

    assert response.status_code == 200
    assert b"Over 90 days old" not in response.data, \
        "Expense older than 90 days must not appear"
    assert b"493.57" in response.data, "Seed data should still be visible"


def test_preset_last_6_months(client):
    """GET /profile?preset=last_6_months limits to trailing 180 days."""
    _login(client)

    old_date = (date.today() - timedelta(days=181)).isoformat()
    _add_expense(client, 40.00, "Transport", old_date, "Over 180 days old")

    response = client.get("/profile?preset=last_6_months")

    assert response.status_code == 200
    assert b"Over 180 days old" not in response.data, \
        "Expense older than 180 days must not appear"
    assert b"493.57" in response.data, "Seed data should still be visible"


def test_preset_all_shows_all_expenses(client):
    """GET /profile?preset=all shows all expenses (unfiltered)."""
    _login(client)

    _add_expense(client, 42.00, "Other", "2023-06-15", "Ancient purchase")

    response = client.get("/profile?preset=all")

    assert response.status_code == 200
    # All expenses including the old one should be visible
    assert b"Ancient purchase" in response.data, \
        "All-expenses preset should include historically old expense"
    # 493.57 + 42.00 = 535.57
    assert b"535.57" in response.data, "Total should include the added 42.00 expense"


# ================================================================== #
# Malformed / Missing Dates                                          #
# ================================================================== #

def test_malformed_date_from_falls_back_unfiltered(client):
    """Malformed date_from silently falls back to the unfiltered view."""
    _login(client)
    response = client.get("/profile?date_from=not-a-date")

    assert response.status_code == 200
    # All seed data should still be visible
    assert b"493.57" in response.data, "Unfiltered total should appear"
    assert b"8" in response.data or b">8<" in response.data, \
        "Transaction count should be 8"


def test_malformed_date_to_falls_back_unfiltered(client):
    """Malformed date_to silently falls back to the unfiltered view."""
    _login(client)
    response = client.get("/profile?date_to=also-invalid")

    assert response.status_code == 200
    assert b"493.57" in response.data, "Unfiltered total should appear"
    assert b"Coffee" in response.data, "Seed data should be visible"


def test_both_dates_malformed_falls_back_unfiltered(client):
    """When both date params are malformed, fall back to unfiltered view."""
    _login(client)
    response = client.get("/profile?date_from=bad&date_to=worse")

    assert response.status_code == 200
    assert b"493.57" in response.data, "Unfiltered total should appear"
    assert b"8" in response.data or b">8<" in response.data, \
        "Transaction count should be 8"


# ================================================================== #
# Inverted Range                                                     #
# ================================================================== #

def test_inverted_date_range_flashes_error(client):
    """When date_from > date_to, flash error and fall back to unfiltered."""
    _login(client)
    response = client.get(
        "/profile?date_from=2026-07-15&date_to=2026-07-01",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Start date must be before end date." in response.data, \
        "Flash error message should be visible"
    # Fallback: all seed data still shown
    assert b"493.57" in response.data, "Unfiltered data should still be visible"


# ================================================================== #
# Empty Result Set                                                   #
# ================================================================== #

def test_no_expenses_in_range_shows_zero_state(client):
    """Filtering to a range with no expenses shows all-zero stats."""
    _login(client)
    response = client.get("/profile?date_from=2020-01-01&date_to=2020-01-31")

    assert response.status_code == 200

    # Empty-state messages for each section
    assert b"No expenses recorded yet" in response.data, \
        "Recent transactions section should show empty-state message"
    assert b"No expense data available" in response.data, \
        "Category breakdown section should show empty-state message"


# ================================================================== #
# All Three Sections Respect Filter                                  #
# ================================================================== #

def test_all_three_sections_respect_filter(client):
    """Stats, category breakdown, and recent transactions all reflect the filter."""
    _login(client)

    today = date.today()
    prev_month_end = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m-%d")

    # Add a unique-category expense (Travel) in the previous month
    _add_expense(client, 150.00, "Travel", prev_month_end, "Weekend getaway")

    # Confirm it appears in the unfiltered view
    resp_all = client.get("/profile")
    assert b"Weekend getaway" in resp_all.data, \
        "Travel expense should appear unfiltered"
    assert b"Travel" in resp_all.data, \
        "Travel category should appear in unfiltered breakdown"

    # Now filter to current month only
    first_of_month = today.replace(day=1).isoformat()
    response = client.get(
        f"/profile?date_from={first_of_month}&date_to={today.isoformat()}"
    )

    assert response.status_code == 200

    # 1. Stats must NOT include the Travel expense
    assert b"493.57" in response.data, \
        "Total spending should exclude the filtered-out Travel expense"

    # 2. Category breakdown must NOT include the filtered-out category
    assert b"Travel" not in response.data, \
        "Travel category must not appear in breakdown when filtered out"

    # 3. Recent transactions must NOT include the filtered-out description
    assert b"Weekend getaway" not in response.data, \
        "Filtered-out expense must not appear in recent transactions"

    # 4. Verify seed data that IS in the current month still appears
    assert b"Groceries" in response.data, \
        "Seed expense (current month) should still be in recent transactions"
