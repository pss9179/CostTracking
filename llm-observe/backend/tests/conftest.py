"""Pytest configuration and shared fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlmodel import SQLModel, Session

# Import models to ensure they're registered
from llmobserve.models import CostEvent


@pytest.fixture(scope="function", autouse=True)
def test_db(tmp_path):
    """Create temporary SQLite database for each test."""
    # Use a temporary file database so all connections share the same DB
    # This avoids the issue where :memory: creates a new database per connection
    db_file = tmp_path / "test.db"
    test_engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(test_engine)
    
    # Monkey patch get_session to use test engine in all modules
    import llmobserve.db
    import llmobserve.exporter
    import llmobserve.api.routes
    
    original_get_session = llmobserve.db.get_session
    
    def test_get_session():
        return Session(test_engine)
    
    # Patch in all modules that use get_session
    llmobserve.db.get_session = test_get_session
    
    # Patch exporter's _get_session function
    llmobserve.exporter._get_session = test_get_session
    llmobserve.exporter.get_session = test_get_session
    
    # Patch API routes _get_session function directly
    # This ensures routes use the test database
    llmobserve.api.routes._get_session = test_get_session
    
    # Also need to reload the routes module to ensure it picks up the patch
    # But actually, since _get_session imports get_session inside, patching
    # llmobserve.db.get_session should be enough. Let's patch both to be safe.
    
    yield test_engine
    
    # Restore original
    llmobserve.db.get_session = original_get_session
    # Restore exporter
    if hasattr(llmobserve.exporter, '_get_session'):
        # Re-import to get original
        import importlib
        import llmobserve.exporter
        importlib.reload(llmobserve.exporter)
    # Restore routes  
    if hasattr(llmobserve.api.routes, '_get_session'):
        import importlib
        import llmobserve.api.routes
        importlib.reload(llmobserve.api.routes)

