"""Proxy utilities for bypassing system proxy settings.

Clears proxy environment variables to allow direct connections
to Google API and other external services.
"""

import os

PROXY_VARS = [
    "HTTP_PROXY",
    "HTTPS_PROXY",
    "ALL_PROXY",
    "http_proxy",
    "https_proxy",
    "all_proxy",
]


def clear_proxy_env() -> None:
    """Clear all proxy environment variables.

    Call this before importing httpx-based libraries (like google.adk)
    to bypass system proxy settings that may cause connection failures.
    """
    for var in PROXY_VARS:
        os.environ.pop(var, None)


def get_proxy_diagnostics() -> dict:
    """Get current proxy environment variable settings."""
    return {var: os.environ.get(var, "(not set)") for var in PROXY_VARS}


# Auto-clear on import for convenience
clear_proxy_env()
