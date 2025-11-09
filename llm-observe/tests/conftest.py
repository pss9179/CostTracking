"""Pytest configuration and fixtures."""

import os
import pytest
from unittest.mock import Mock, patch

# Set test environment variables
os.environ["OPENAI_API_KEY"] = "test-key"
os.environ["SUPABASE_URL"] = "https://test.supabase.co"
os.environ["SUPABASE_DB_PASSWORD"] = "test-password"
os.environ["ENV"] = "test"


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    with patch("openai.OpenAI") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        
        # Mock response
        mock_response = Mock()
        mock_response.model = "gpt-3.5-turbo"
        mock_response.choices = [Mock(message=Mock(content="Test response"))]
        mock_response.usage = Mock(prompt_tokens=10, completion_tokens=20)
        
        mock_instance.chat.completions.create.return_value = mock_response
        yield mock_instance

