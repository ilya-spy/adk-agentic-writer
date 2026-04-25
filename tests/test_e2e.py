"""End-to-end integration tests that replay the showcase page flow.

These tests call real LLM endpoints and require GOOGLE_API_KEY.
Run with:  pytest tests/test_e2e.py -m integration --timeout=600
Skip with: pytest -m "not integration"
"""

import json
import os
import pytest
import httpx
from dotenv import load_dotenv

load_dotenv()

pytestmark = [pytest.mark.integration, pytest.mark.slow]

_HAS_KEY = bool(os.environ.get("GOOGLE_API_KEY"))
skip_no_key = pytest.mark.skipif(not _HAS_KEY, reason="GOOGLE_API_KEY not set")

FORMATS = ["quiz", "story", "game", "simulation"]

FORMAT_SIGNATURES = {
    "quiz": "questions",
    "story": "nodes",
    "game": "nodes",
    "simulation": "variables",
}

IDEATION_PROMPTS = {
    "quiz": (
        "The history and science behind CRISPR gene editing technology, "
        "ethical dilemmas, and its applications in treating genetic diseases"
    ),
    "story": (
        "A cryptographer who discovers that a Renaissance painting contains "
        "a coded message predicting modern geopolitical events"
    ),
    "game": (
        "The Stanford Prison Experiment where participants were assigned "
        "as guards and inmates, exploring the psychology of power and authority"
    ),
    "simulation": (
        "Modeling the cascading failures of interconnected Bronze Age "
        "trade networks during the Late Bronze Age Collapse around 1200 BCE"
    ),
}


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="module")
async def api_client():
    from src.adk_agentic_writer.backend.api import app
    from src.adk_agentic_writer.backend.runtime import lifespan

    async with lifespan(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            yield client


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def post_task(client: httpx.AsyncClient, task_id: str, params: dict,
                    session_id: str | None = None, timeout: float = 120) -> dict:
    """POST /task/{task_id} and return parsed response JSON."""
    body: dict = {"parameters": params}
    if session_id:
        body["session_id"] = session_id
    resp = await client.post(f"/task/{task_id}", json=body, timeout=timeout)
    assert resp.status_code == 200, f"/task/{task_id} returned {resp.status_code}: {resp.text[:300]}"
    return resp.json()


def assert_completed(data: dict, task_id: str, *, allow_partial: bool = False):
    """Assert the AgentResponse indicates success.

    When *allow_partial* is True, the assertion still passes if
    ``_parse_error`` is present (graceful degradation produced a stub).
    """
    content = data.get("content", {})
    if allow_partial and "_parse_error" in content:
        return
    assert data.get("status") == "completed", (
        f"{task_id}: expected status='completed', got '{data.get('status')}'. "
        f"content={str(content)[:200]}"
    )
    assert isinstance(content, dict) and content, f"{task_id}: empty content"
    assert "error" not in content, f"{task_id}: content has error: {content.get('error', '')[:200]}"


def get_default_params(fmt_name: str) -> dict:
    """Load FormatSpec default_params for a format."""
    from adk_agentic_writer.formats import get_format
    fmt = get_format(fmt_name)
    return dict(fmt.default_params) if fmt else {}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

@skip_no_key
@pytest.mark.parametrize("fmt", FORMATS, ids=FORMATS)
async def test_showcase_chain(api_client: httpx.AsyncClient, fmt: str):
    """Full showcase chain: ideate -> write -> review -> verify -> refine."""

    # -- 1. Ideate --
    ideate_resp = await post_task(api_client, "ideate", {
        "prompt": IDEATION_PROMPTS[fmt],
        "formats": [fmt],
        "domain": "realworld",
    })
    assert_completed(ideate_resp, "ideate")
    idea = ideate_resp["content"]
    topic = idea.get("topic_statement") or idea.get("topic") or IDEATION_PROMPTS[fmt]

    # -- 2. Write --
    write_params = get_default_params(fmt)
    write_params.update({
        "format": fmt,
        "topic": topic,
        "domain": "realworld",
    })
    if "creative_direction" not in write_params:
        write_params["creative_direction"] = idea.get("creative_direction", "")
    if "reasoning" not in write_params:
        write_params["reasoning"] = idea.get("reasoning", "")

    write_resp = await post_task(api_client, "write", write_params, timeout=180)
    assert_completed(write_resp, "write", allow_partial=True)
    draft = write_resp["content"]

    sig_key = FORMAT_SIGNATURES.get(fmt)
    if "_parse_error" not in draft and sig_key:
        assert sig_key in draft, (
            f"write({fmt}): expected '{sig_key}' in draft keys {list(draft.keys())}"
        )

    # -- 3. Review --
    review_resp = await post_task(api_client, "review", {
        "draft_content": draft,
        "format": fmt,
        "domain": "realworld",
    })
    assert_completed(review_resp, "review", allow_partial=True)
    review = review_resp["content"]
    if "_parse_error" not in review:
        assert "score" in review, f"review: missing 'score' in {list(review.keys())}"

    # -- 4. Verify --
    verify_resp = await post_task(api_client, "verify", {
        "draft_content": draft,
        "format": fmt,
        "domain": "realworld",
    })
    verification = verify_resp.get("content", {})

    # -- 5. Refine --
    refine_resp = await post_task(api_client, "refine", {
        "draft_content": draft,
        "format": fmt,
        "domain": "realworld",
        "review_result": review,
        "verification_result": verification,
    }, timeout=180)
    assert_completed(refine_resp, "refine", allow_partial=True)
    refined = refine_resp["content"]

    if "_parse_error" not in refined and sig_key:
        assert sig_key in refined, (
            f"refine({fmt}): expected '{sig_key}' in refined keys {list(refined.keys())}"
        )


@skip_no_key
async def test_publish_oneshot(api_client: httpx.AsyncClient):
    """One-shot publish flow without format specifier."""
    resp = await post_task(api_client, "publish", {
        "prompt": (
            "The collapse of Bronze Age civilizations around 1200 BCE - "
            "the Sea Peoples, volcanic eruptions, drought, and trade failures"
        ),
        "formats": [],
        "domain": "realworld",
    }, timeout=600)

    assert_completed(resp, "publish", allow_partial=True)
    assert resp.get("session_id"), "publish: expected session_id in response"

    content = resp["content"]
    if "_parse_error" not in content:
        format_wrapper_keys = set(FORMATS)
        signature_keys = set(FORMAT_SIGNATURES.values())
        content_keys = set(content.keys())
        has_signature = bool(content_keys & signature_keys)
        has_wrapper = bool(content_keys & format_wrapper_keys)
        assert has_signature or has_wrapper, (
            f"publish: content lacks any format signature or wrapper key. "
            f"Keys: {list(content.keys())}"
        )


# ---------------------------------------------------------------------------
# Multi-round session test
# ---------------------------------------------------------------------------

@skip_no_key
async def test_two_round_session(api_client: httpx.AsyncClient):
    """Two rounds of related prompts in a shared session.

    Round 1: ideate + write a quiz about space exploration.
    Round 2: same session, refine the prompt to focus on Mars rovers + harder.
    Verifies that both rounds produce valid ideation JSON and content, and
    that round 2 does not simply echo round 1.
    """
    # -- Create session --
    sess_resp = await api_client.post("/sessions", timeout=10)
    assert sess_resp.status_code == 200
    session_id = sess_resp.json()["session_id"]

    # -- Round 1: ideate --
    idea1_resp = await post_task(api_client, "ideate", {
        "prompt": "A fun and educational quiz about the history of space exploration",
        "formats": ["quiz"],
        "domain": "realworld",
    }, session_id=session_id)
    assert_completed(idea1_resp, "ideate (r1)")
    idea1 = idea1_resp["content"]
    assert "chosen_format" in idea1 or "topic_statement" in idea1, (
        f"ideate r1: missing ideation keys, got {list(idea1.keys())}"
    )
    topic1 = idea1.get("topic_statement") or idea1.get("topic", "space exploration")

    # -- Round 1: write --
    wp1 = get_default_params("quiz")
    wp1.update({
        "format": "quiz",
        "topic": topic1,
        "domain": "realworld",
        "creative_direction": idea1.get("creative_direction", ""),
        "reasoning": idea1.get("reasoning", ""),
    })
    write1_resp = await post_task(api_client, "write", wp1,
                                  session_id=session_id, timeout=180)
    assert_completed(write1_resp, "write (r1)", allow_partial=True)
    draft1 = write1_resp["content"]

    # -- Round 2: ideate with a RELATED but different prompt --
    idea2_resp = await post_task(api_client, "ideate", {
        "prompt": (
            "Now focus specifically on Mars rover missions - Curiosity and "
            "Perseverance. Make it harder and more technical."
        ),
        "formats": ["quiz"],
        "domain": "realworld",
    }, session_id=session_id)
    assert_completed(idea2_resp, "ideate (r2)")
    idea2 = idea2_resp["content"]

    # Round 2 ideation must still be proper ideation JSON, not raw content
    assert "chosen_format" in idea2 or "topic_statement" in idea2, (
        f"ideate r2: returned raw content instead of ideation JSON. "
        f"Keys: {list(idea2.keys())}"
    )
    # Should NOT contain quiz content keys directly
    assert "questions" not in idea2, (
        "ideate r2: returned quiz content instead of ideation brief"
    )

    topic2 = idea2.get("topic_statement") or idea2.get("topic", "Mars rovers")

    # -- Round 2: write --
    wp2 = get_default_params("quiz")
    wp2.update({
        "format": "quiz",
        "topic": topic2,
        "domain": "realworld",
        "creative_direction": idea2.get("creative_direction", ""),
        "reasoning": idea2.get("reasoning", ""),
    })
    write2_resp = await post_task(api_client, "write", wp2,
                                  session_id=session_id, timeout=180)
    assert_completed(write2_resp, "write (r2)", allow_partial=True)
    draft2 = write2_resp["content"]

    # Round 2 draft should be different from round 1
    if "_parse_error" not in draft1 and "_parse_error" not in draft2:
        title1 = draft1.get("title", "")
        title2 = draft2.get("title", "")
        assert title1 != title2, (
            f"Round 2 produced identical title to round 1: '{title1}'"
        )


# ---------------------------------------------------------------------------
# Truncation recovery (unit-level, no LLM calls)
# ---------------------------------------------------------------------------

def test_truncation_repair_nested_game():
    """Verify _repair_truncated_json handles deeply nested game JSON."""
    from src.adk_agentic_writer.utils.response import _repair_truncated_json

    truncated = json.dumps({
        "title": "Test Game",
        "start_node": "start",
        "nodes": {
            "start": {"node_id": "start", "title": "Begin", "description": "You arrive."},
            "mid": {"node_id": "mid", "title": "Middle", "description": "Halfway there."},
        },
    })[:-20]  # chop the last 20 chars

    repaired = _repair_truncated_json(truncated)
    assert repaired is not None, "repair returned None for truncated game JSON"
    parsed = json.loads(repaired, strict=False)
    assert "title" in parsed
    assert "nodes" in parsed
    assert "start" in parsed["nodes"]


def test_truncation_repair_preserves_max_content():
    """Verify repair preserves as much content as possible."""
    from src.adk_agentic_writer.utils.response import _repair_truncated_json

    full = {"items": [1, 2, 3, 4, 5], "extra": "val"}
    truncated = json.dumps(full)[:-5]
    repaired = _repair_truncated_json(truncated)
    assert repaired is not None
    parsed = json.loads(repaired)
    assert parsed["items"] == [1, 2, 3, 4, 5]


def test_double_brace_no_corruption():
    """Verify _fix_double_braces does not corrupt nested JSON."""
    from src.adk_agentic_writer.utils.response import parse_json

    nested = '{"a": {"b": {"c": 1}}, "d": 2}'
    result = parse_json(nested, "test")
    assert result == {"a": {"b": {"c": 1}}, "d": 2}


def test_graceful_degradation_on_total_failure():
    """Verify parse failure returns _parse_error stub instead of raising."""
    from src.adk_agentic_writer.agents.base import BaseAgentService

    svc = BaseAgentService.__new__(BaseAgentService)
    result = svc._parse_and_validate("not json at all {{{", "TestAgent")
    assert "_parse_error" in result
    assert "_raw_truncated" in result
