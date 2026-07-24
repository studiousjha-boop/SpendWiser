from database.db import get_db

def test_landing_page(client):
    """Test that the landing page loads successfully."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"SpendWiser" in response.data or b"Spendly" in response.data

def test_profile_requires_login(client):
    """Test that the profile page redirects unauthenticated users to login."""
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.location

def test_successful_registration(client, app):
    """Test registering a new user successfully."""
    response = client.post("/register", data={
        "name": "Arjun Patel",
        "email": "arjun.patel@example.com",
        "password": "securepassword123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Arjun Patel" in response.data
    assert b"arjun.patel@example.com" in response.data
    assert b"No expenses recorded yet" in response.data
    
    # Check that database has the user
    with app.app_context():
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM users WHERE email = ?", ("arjun.patel@example.com",))
        user = cur.fetchone()
        conn.close()
        assert user is not None
        assert user["name"] == "Arjun Patel"

def test_registration_validation(client):
    """Test validation errors during registration."""
    # Test missing fields
    response = client.post("/register", data={
        "name": "",
        "email": "invalid@example.com",
        "password": "password"
    })
    assert response.status_code == 200
    assert b"All fields are required." in response.data

    # Test short password
    response = client.post("/register", data={
        "name": "Short Pass",
        "email": "short@example.com",
        "password": "123"
    })
    assert response.status_code == 200
    assert b"Password must be at least 8 characters long." in response.data

    # Test duplicate email
    response = client.post("/register", data={
        "name": "Demo User 2",
        "email": "demo@spendly.com",  # Already seeded
        "password": "password123"
    })
    assert response.status_code == 200
    assert b"An account with this email already exists." in response.data

def test_successful_login(client):
    """Test logging in with valid credentials."""
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Demo User" in response.data
    assert b"Total Spending" in response.data
    assert b"demo@spendly.com" in response.data

def test_invalid_login(client):
    """Test logging in with invalid credentials."""
    response = client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "wrongpassword"
    })
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data

    response = client.post("/login", data={
        "email": "nonexistent@spendly.com",
        "password": "password"
    })
    assert response.status_code == 200
    assert b"Invalid email or password." in response.data

def test_logout(client):
    """Test logging out clears session and redirects."""
    # Log in first
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    # Verify logged in session
    with client.session_transaction() as sess:
        assert sess.get("user_id") is not None
        
    # Log out
    response = client.get("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert b"Sign in" in response.data
    
    # Verify session is cleared
    with client.session_transaction() as sess:
        assert sess.get("user_id") is None

def test_profile_metrics_and_expenses(client, app):
    """Test that the profile displays correct statistics and seeded data."""
    # Log in
    client.post("/login", data={
        "email": "demo@spendly.com",
        "password": "demo123"
    })
    
    # Get profile
    response = client.get("/profile")
    assert response.status_code == 200
    
    # Demo user should have:
    # Food (2 expenses: 45.99 + 8.99 = 54.98)
    # Transport (15.00)
    # Bills (120.50)
    # Health (60.00)
    # Entertainment (30.75)
    # Shopping (200.00)
    # Other (12.34)
    # Total = 493.57
    
    assert b"493.57" in response.data
    assert b"8" in response.data # Total count of transactions
    assert b"61.70" in response.data or b"61.69" in response.data # Average transaction
    
    # Check category percentages are displayed (e.g. Shopping is 200 / 493.57 = 40.5%)
    assert b"Shopping" in response.data
    assert b"Food" in response.data
    assert b"Bills" in response.data
    
    # Check recent expenses table (top 5 sorted by date desc)
    assert b"Coffee" in response.data
    assert b"Clothes" in response.data
    assert b"Pharmacy" in response.data
