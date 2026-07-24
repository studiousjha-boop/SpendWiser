def test_add_expense_requires_login(client):
    """Test that adding an expense requires authentication."""
    response = client.get("/expenses/add")
    assert response.status_code == 302
    assert "/login" in response.location


def test_add_expense_success(client):
    """Test adding an expense successfully when logged in."""
    # Login as demo user
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })

    response = client.post("/expenses/add", data={
        "amount": "99.50",
        "category": "Food",
        "date": "2026-07-24",
        "description": "Dinner with friends"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Dinner with friends" in response.data
    assert b"99.50" in response.data


def test_edit_expense_success(client):
    """Test editing an existing expense."""
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })

    # Edit expense with ID 1
    response = client.post("/expenses/1/edit", data={
        "amount": "150.00",
        "category": "Shopping",
        "date": "2026-07-24",
        "description": "Updated item"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Updated item" in response.data
    assert b"150.00" in response.data


def test_delete_expense_success(client):
    """Test deleting an expense."""
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })

    response = client.post("/expenses/1/delete", follow_redirects=True)
    assert response.status_code == 200
    assert b"Expense deleted successfully!" in response.data
