"""Shared test fixtures."""

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_db_session():
    """Create a mock database session with managed_session context manager wiring."""
    mock_db = MagicMock()
    return mock_db


@pytest.fixture
def mock_managed_session(mock_db_session):
    """Return a mock context manager that yields mock_db_session."""
    ctx = MagicMock()
    ctx.__enter__ = MagicMock(return_value=mock_db_session)
    ctx.__exit__ = MagicMock(return_value=False)

    def factory():
        return ctx

    return factory
