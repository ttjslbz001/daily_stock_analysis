# -*- coding: utf-8 -*-
"""
MCP Authentication Module

Validates API key for MCP requests.
"""

from typing import Optional


def validate_mcp_api_key(provided_key: Optional[str], expected_key: Optional[str]) -> bool:
    """
    Validate MCP API key.

    Args:
        provided_key: Key from request header
        expected_key: Expected key from config

    Returns:
        True if valid, False otherwise
    """
    if not expected_key:
        # No key configured - allow access
        return True

    if not provided_key:
        return False

    return provided_key == expected_key
