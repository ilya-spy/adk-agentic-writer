"""Google API connectivity smoke tests.

Validates that the API key works and the Gemini API is reachable.
Skipped automatically when GOOGLE_API_KEY is not set.

Usage:
    pytest tests/integration/test_google_connectivity.py -v
"""

import os

import pytest

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
MODELS_URL = "https://generativelanguage.googleapis.com/v1beta/models"

requires_key = pytest.mark.skipif(
    not GOOGLE_API_KEY,
    reason="GOOGLE_API_KEY not set — skipping connectivity tests",
)


@requires_key
class TestGoogleConnectivity:
    """Smoke tests for Google API reachability."""

    def test_api_key_format(self):
        """API key should be a non-empty string."""
        assert GOOGLE_API_KEY, "GOOGLE_API_KEY is empty"
        assert len(GOOGLE_API_KEY) > 10, "GOOGLE_API_KEY looks too short"

    def test_direct_connection(self):
        """Direct HTTPS call to Gemini models endpoint succeeds."""
        import httpx

        with httpx.Client(trust_env=False, timeout=30) as client:
            r = client.get(MODELS_URL, params={"key": GOOGLE_API_KEY})

        assert r.status_code == 200, f"API returned {r.status_code}: {r.text[:200]}"

        data = r.json()
        models = data.get("models", [])
        assert len(models) > 0, "No models returned from API"

    def test_models_include_gemini(self):
        """At least one Gemini model should be listed."""
        import httpx

        with httpx.Client(trust_env=False, timeout=30) as client:
            r = client.get(MODELS_URL, params={"key": GOOGLE_API_KEY})

        models = r.json().get("models", [])
        gemini_models = [m for m in models if "gemini" in m.get("name", "").lower()]
        assert len(gemini_models) > 0, "No Gemini models found in API response"

    def test_proxy_env_diagnostics(self, capfd):
        """Log proxy environment for debugging (always passes)."""
        proxy_vars = [
            "HTTP_PROXY",
            "HTTPS_PROXY",
            "ALL_PROXY",
            "NO_PROXY",
            "http_proxy",
            "https_proxy",
            "all_proxy",
            "no_proxy",
        ]
        for var in proxy_vars:
            value = os.environ.get(var, "(not set)")
            print(f"  {var}: {value}")

        # This test is informational — always passes
        assert True
