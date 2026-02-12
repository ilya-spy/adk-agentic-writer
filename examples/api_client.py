#!/usr/bin/env python3
"""Interactive HTTP API client for ADK Agentic Writer server.

CLI utility for live debugging and validation of the FastAPI backend.
Sends real HTTP GET/POST requests, displays formatted JSON payloads,
status codes, headers, and response timing.

Usage:
    python examples/api_client.py                  # default http://localhost:8000
    python examples/api_client.py --base-url http://192.168.1.5:8000
    python examples/api_client.py --base-url http://localhost:9000

Requires:
    - httpx (already in project requirements)
    - A running server:  python -m uvicorn adk_agentic_writer.backend.api:app --port 8000
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any, Dict, List, Optional

import httpx

# ─── Defaults ────────────────────────────────────────────────────────────────
DEFAULT_BASE_URL = "http://localhost:8000"
TIMEOUT = 60.0  # generous timeout for LLM-backed generation

# ─── Colour helpers (ANSI, gracefully degrades) ─────────────────────────────
_RESET = "\033[0m"
_BOLD = "\033[1m"
_DIM = "\033[2m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_RED = "\033[31m"
_CYAN = "\033[36m"
_MAGENTA = "\033[35m"
_BLUE = "\033[34m"


def _c(text: str, code: str) -> str:
    return f"{code}{text}{_RESET}"


# ─── Pretty printers ────────────────────────────────────────────────────────
def print_separator(char: str = "─", width: int = 80) -> None:
    print(_c(char * width, _DIM))


def print_header(title: str) -> None:
    print()
    print_separator("═")
    print(_c(f"  {title}", _BOLD + _CYAN))
    print_separator("═")


def print_request(method: str, url: str, body: Optional[Dict] = None) -> None:
    """Print outgoing request details."""
    print()
    print(_c("▶ REQUEST", _BOLD + _YELLOW))
    print(f"  {_c(method, _BOLD)} {_c(url, _BLUE)}")
    if body is not None:
        print(_c("  Body:", _DIM))
        print(_format_json(body, indent=4))


def print_response(resp: httpx.Response, elapsed_ms: float) -> None:
    """Print response: status, timing, headers, body."""
    # Status line
    status = resp.status_code
    if 200 <= status < 300:
        status_colour = _GREEN
    elif 300 <= status < 400:
        status_colour = _YELLOW
    else:
        status_colour = _RED

    print()
    print(_c("◀ RESPONSE", _BOLD + _GREEN))
    print(f"  Status: {_c(str(status), _BOLD + status_colour)} {resp.reason_phrase}")
    print(f"  Time:   {_c(f'{elapsed_ms:.0f}ms', _DIM)}")
    print(f"  Size:   {_c(f'{len(resp.content)} bytes', _DIM)}")

    # Selected headers
    for hdr in ("content-type", "x-request-id"):
        val = resp.headers.get(hdr)
        if val:
            print(f"  {hdr}: {val}")

    # Body
    content_type = resp.headers.get("content-type", "")
    if "json" in content_type:
        try:
            data = resp.json()
            print(_c("  Body (JSON):", _DIM))
            print(_format_json(data, indent=4))
        except Exception:
            print(_c("  Body (raw):", _DIM))
            print(f"    {resp.text[:2000]}")
    elif "html" in content_type:
        preview = resp.text[:300].replace("\n", " ").strip()
        print(_c("  Body (HTML preview):", _DIM))
        print(f"    {preview}...")
    else:
        print(_c("  Body:", _DIM))
        print(f"    {resp.text[:2000]}")


def _format_json(data: Any, indent: int = 2) -> str:
    """Return indented, coloured JSON string."""
    raw = json.dumps(data, indent=indent, ensure_ascii=False, default=str)
    # Indent each line by `indent` extra spaces for alignment under labels
    prefix = " " * indent
    return "\n".join(f"{prefix}{line}" for line in raw.splitlines())


# ─── HTTP helpers ────────────────────────────────────────────────────────────
class APIClient:
    """Thin wrapper around httpx for display and error handling."""

    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(base_url=self.base_url, timeout=TIMEOUT)

    def get(self, path: str) -> Optional[httpx.Response]:
        url = f"{self.base_url}{path}"
        print_request("GET", url)
        t0 = time.perf_counter()
        try:
            resp = self.client.get(path)
            elapsed = (time.perf_counter() - t0) * 1000
            print_response(resp, elapsed)
            return resp
        except httpx.ConnectError:
            print(_c(f"\n  ✖ Connection refused – is the server running at {self.base_url}?", _RED))
            return None
        except Exception as exc:
            print(_c(f"\n  ✖ Request failed: {exc}", _RED))
            return None

    def post(self, path: str, body: Dict) -> Optional[httpx.Response]:
        url = f"{self.base_url}{path}"
        print_request("POST", url, body)
        t0 = time.perf_counter()
        try:
            resp = self.client.post(path, json=body)
            elapsed = (time.perf_counter() - t0) * 1000
            print_response(resp, elapsed)
            return resp
        except httpx.ConnectError:
            print(_c(f"\n  ✖ Connection refused – is the server running at {self.base_url}?", _RED))
            return None
        except Exception as exc:
            print(_c(f"\n  ✖ Request failed: {exc}", _RED))
            return None

    def close(self):
        self.client.close()


# ─── Input helpers ───────────────────────────────────────────────────────────
def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"  {prompt}{suffix}: ").strip()
    return val or default


def ask_int(prompt: str, default: int, lo: int = 1, hi: int = 100) -> int:
    while True:
        raw = ask(f"{prompt} ({lo}-{hi})", str(default))
        try:
            v = int(raw)
            if lo <= v <= hi:
                return v
        except ValueError:
            pass
        print(f"    Please enter an integer between {lo} and {hi}")


def ask_choice(options: List[str], prompt: str = "Choose") -> int:
    """Return 0-based index, or -1 for cancel."""
    for i, opt in enumerate(options, 1):
        print(f"    {_c(str(i), _BOLD)}. {opt}")
    print(f"    {_c('0', _BOLD)}. Back")
    while True:
        raw = ask(prompt, "")
        try:
            v = int(raw)
            if v == 0:
                return -1
            if 1 <= v <= len(options):
                return v - 1
        except ValueError:
            pass
        print(f"    Enter 0-{len(options)}")


def choose_team() -> Optional[str]:
    idx = ask_choice(["static  – fast, template-based (no API key)",
                       "gemini  – AI-powered via Google ADK"], "Team")
    if idx < 0:
        return None
    return ["static", "gemini"][idx]


def choose_content_type() -> Optional[str]:
    types = [
        "quiz             (quiz, trivia, test)",
        "story            (story, narrative, branched_narrative)",
        "game             (game, quest_game, quest, rpg)",
        "simulation       (simulation, web_simulation, interactive)",
    ]
    idx = ask_choice(types, "Content type")
    if idx < 0:
        return None
    return ["quiz", "story", "game", "simulation"][idx]


def build_parameters(content_type: str) -> Dict[str, Any]:
    """Prompt for type-specific parameters."""
    params: Dict[str, Any] = {}

    if content_type in ("quiz", "trivia", "test"):
        params["num_questions"] = ask_int("Number of questions", 5, 3, 20)
        params["num_options"] = ask_int("Answer options per question", 4, 2, 6)
        diff_idx = ask_choice(["easy", "medium", "hard"], "Difficulty")
        params["difficulty"] = ["easy", "medium", "hard"][diff_idx] if diff_idx >= 0 else "medium"

    elif content_type in ("story", "narrative", "branched_narrative", "adventure"):
        params["num_nodes"] = ask_int("Number of story nodes", 7, 3, 20)
        params["genre"] = ask("Genre", "fantasy")

    elif content_type in ("game", "quest_game", "quest", "rpg"):
        params["num_nodes"] = ask_int("Number of game nodes", 5, 3, 15)

    elif content_type in ("simulation", "web_simulation", "interactive", "simulator"):
        params["complexity"] = ask("Complexity (low/medium/high)", "medium")

    return params


def build_multimodal_parameters() -> Dict[str, Any]:
    """Prompt for multimodal story parameters."""
    params: Dict[str, Any] = {}
    params["num_story_nodes"] = ask_int("Story nodes", 8, 3, 20)
    params["num_mini_games"] = ask_int("Embedded mini-games", 2, 0, 5)
    params["num_mini_quizzes"] = ask_int("Embedded mini-quizzes", 2, 0, 5)
    params["genre"] = ask("Genre", "adventure")
    return params


# ─── Menu actions ────────────────────────────────────────────────────────────
def action_health(client: APIClient) -> None:
    print_header("Health Check")
    client.get("/health")


def action_api_info(client: APIClient) -> None:
    print_header("API Info")
    client.get("/api")


def action_teams(client: APIClient) -> None:
    print_header("Available Teams")
    client.get("/teams")


def action_tasks(client: APIClient) -> None:
    print_header("Available Tasks")
    client.get("/tasks")


def action_content_types(client: APIClient) -> None:
    print_header("Content Types")
    client.get("/content-types")


def action_generate(client: APIClient) -> None:
    print_header("Generate Content  (POST /generate)")

    team = choose_team()
    if not team:
        return
    ct = choose_content_type()
    if ct is None:
        return
    topic = ask("Topic", "Python Programming")
    params = build_parameters(ct)

    body = {
        "team": team,
        "content_type": ct,
        "topic": topic,
        "parameters": params,
    }
    client.post("/generate", body)


def action_generate_with_validation(client: APIClient) -> None:
    print_header("Generate with Validation  (POST /generate/with-validation)")

    team = choose_team()
    if not team:
        return
    ct = choose_content_type()
    if ct is None:
        return
    topic = ask("Topic", "Space Exploration")
    params = build_parameters(ct)

    body = {
        "team": team,
        "content_type": ct,
        "topic": topic,
        "parameters": params,
    }
    client.post("/generate/with-validation", body)


def action_multimodal_story(client: APIClient) -> None:
    print_header("Multimodal Story  (POST /generate/multimodal-story)")
    print(_c("  Note: only available for static team", _DIM))

    topic = ask("Topic", "Ocean Adventure")
    params = build_multimodal_parameters()

    body = {
        "team": "static",
        "content_type": "branched_narrative",
        "topic": topic,
        "parameters": params,
    }
    client.post("/generate/multimodal-story", body)


def action_custom_request(client: APIClient) -> None:
    print_header("Custom Request")
    method_idx = ask_choice(["GET", "POST"], "Method")
    if method_idx < 0:
        return
    method = ["GET", "POST"][method_idx]
    path = ask("Path (e.g. /health)", "/health")
    if not path.startswith("/"):
        path = "/" + path

    if method == "GET":
        client.get(path)
    else:
        raw = ask("JSON body (or empty for {})", "{}")
        try:
            body = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(_c(f"  Invalid JSON: {exc}", _RED))
            return
        client.post(path, body)


# ─── Main menu ───────────────────────────────────────────────────────────────
MENU_ITEMS = [
    ("Health Check",                   "GET  /health",                   action_health),
    ("API Info",                       "GET  /api",                      action_api_info),
    ("List Teams",                     "GET  /teams",                    action_teams),
    ("List Tasks",                     "GET  /tasks",                    action_tasks),
    ("List Content Types",             "GET  /content-types",            action_content_types),
    ("Generate Content",               "POST /generate",                 action_generate),
    ("Generate with Validation",       "POST /generate/with-validation", action_generate_with_validation),
    ("Generate Multimodal Story",      "POST /generate/multimodal-story",action_multimodal_story),
    ("Custom Request",                 "any  path",                      action_custom_request),
]


def main_menu(client: APIClient) -> None:
    while True:
        print_header(f"ADK Agentic Writer – API Client  ({client.base_url})")
        print()
        for i, (label, hint, _) in enumerate(MENU_ITEMS, 1):
            print(f"    {_c(str(i), _BOLD)}.  {label:<34} {_c(hint, _DIM)}")
        print(f"    {_c('0', _BOLD)}.  Exit")
        print_separator()

        raw = ask("Choice", "")
        try:
            choice = int(raw)
        except ValueError:
            continue

        if choice == 0:
            print(_c("\nGoodbye!\n", _CYAN))
            break
        if 1 <= choice <= len(MENU_ITEMS):
            _, _, action_fn = MENU_ITEMS[choice - 1]
            try:
                action_fn(client)
            except KeyboardInterrupt:
                print(_c("\n  Interrupted.", _YELLOW))
            print()
            input(_c("  Press Enter to continue...", _DIM))
        else:
            print(_c("  Invalid choice", _RED))


# ─── Entry point ─────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="Interactive HTTP client for the ADK Agentic Writer API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python examples/api_client.py\n"
            "  python examples/api_client.py --base-url http://localhost:9000\n"
        ),
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Server base URL (default: {DEFAULT_BASE_URL})",
    )
    args = parser.parse_args()

    client = APIClient(args.base_url)
    try:
        main_menu(client)
    except KeyboardInterrupt:
        print(_c("\nInterrupted. Bye!\n", _YELLOW))
    finally:
        client.close()


if __name__ == "__main__":
    main()
