"""Tests for semantic conventions and hashing."""

from llmobserve.semantics import hash_content, hash_prompt, hash_response


def test_hash_content():
    """Test content hashing."""
    content = "test content"
    hash1 = hash_content(content)
    hash2 = hash_content(content)
    
    # Same content should produce same hash
    assert hash1 == hash2
    
    # Hash should be 16 characters (truncated)
    assert len(hash1) == 16
    
    # Different content should produce different hash
    hash3 = hash_content("different content")
    assert hash1 != hash3


def test_hash_prompt():
    """Test prompt hashing."""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there"},
    ]
    
    hash1 = hash_prompt(messages)
    hash2 = hash_prompt(messages)
    
    # Same messages should produce same hash
    assert hash1 == hash2
    
    # Different messages should produce different hash
    messages2 = [{"role": "user", "content": "Goodbye"}]
    hash3 = hash_prompt(messages2)
    assert hash1 != hash3


def test_hash_response():
    """Test response hashing."""
    content = "This is a response"
    hash1 = hash_response(content)
    hash2 = hash_response(content)
    
    # Same content should produce same hash
    assert hash1 == hash2
    
    # Different content should produce different hash
    hash3 = hash_response("Different response")
    assert hash1 != hash3

