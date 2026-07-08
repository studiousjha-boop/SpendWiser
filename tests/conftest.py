import os
import tempfile
import pytest
import sys
from pathlib import Path

# Add project root to sys.path so we can import app and database
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import app as flask_app
from database.db import init_db, seed_db

@pytest.fixture
def app():
    # Create a temporary file for the SQLite database
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure the app for testing
    flask_app.config.update({
        "TESTING": True,
        "DATABASE": db_path,
        "SECRET_KEY": "test-secret-key"
    })
    
    # Initialize and seed the temporary database
    with flask_app.app_context():
        init_db()
        seed_db()
        
    yield flask_app
    
    # Close and remove the temporary database after the test
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()
