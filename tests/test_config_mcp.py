"""Tests for MCP configuration fields."""
import pytest
from src.config import Config


def test_mcp_enabled_default():
    """MCP should be disabled by default."""
    config = Config()
    assert config.mcp_enabled is False


def test_mcp_api_key_default():
    """MCP API key should be None by default."""
    config = Config()
    assert config.mcp_api_key is None


def test_mcp_api_key_from_env(monkeypatch):
    """MCP API key should be loaded from environment."""
    monkeypatch.setenv("MCP_API_KEY", "test-key-123")
    Config._instance = None  # Reset singleton
    config = Config.get_instance()
    assert config.mcp_api_key == "test-key-123"
    Config._instance = None  # Cleanup
