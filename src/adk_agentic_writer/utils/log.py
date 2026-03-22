"""Centralized logging configuration.

Environment knobs (all optional, sensible defaults):

    LOG_LEVEL          – root level for the app          (default: INFO)
    LOG_LLM_IO         – log full prompts & JSON replies (default: false)
    LOG_LLM_IO_MAX     – max chars to print per payload  (default: 2000)
    LOG_LEVEL_LLM      – level for LLM I/O messages      (default: DEBUG)
    LOG_LEVEL_AGENTS   – level for agents.* loggers       (default: INFO)
    LOG_LEVEL_API      – level for backend.api logger     (default: INFO)
    LOG_LEVEL_HTTPX    – level for httpx (HTTP requests)  (default: WARNING)
    LOG_LEVEL_ADK      – level for google_adk.* loggers   (default: WARNING)
    LOG_FORMAT         – "text" (human) or "json"         (default: text)

Usage:
    from adk_agentic_writer.utils.log import configure_logging
    configure_logging()                 # reads env vars
    configure_logging(log_level="DEBUG", log_llm_io=True)  # explicit
"""

import json
import logging
import os
import textwrap
from typing import Optional

# ---------------------------------------------------------------------------
# Env helpers
# ---------------------------------------------------------------------------

_TRUTHY = frozenset({"1", "true", "yes", "on"})


def _env_bool(key: str, default: bool = False) -> bool:
    return os.environ.get(key, str(default)).strip().lower() in _TRUTHY


def _env_int(key: str, default: int) -> int:
    try:
        return int(os.environ.get(key, default))
    except (TypeError, ValueError):
        return default


def _env_level(key: str, default: str = "INFO") -> int:
    name = os.environ.get(key, default).strip().upper()
    return getattr(logging, name, logging.INFO)


# ---------------------------------------------------------------------------
# Public settings (populated by configure_logging, readable afterwards)
# ---------------------------------------------------------------------------

LOG_LLM_IO: bool = False
LOG_LLM_IO_MAX: int = 2000


# ---------------------------------------------------------------------------
# JSON formatter (optional)
# ---------------------------------------------------------------------------

class _JsonFormatter(logging.Formatter):
    """Compact single-line JSON log records."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info and record.exc_info[0]:
            entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)


# ---------------------------------------------------------------------------
# configure_logging
# ---------------------------------------------------------------------------

def configure_logging(
    *,
    log_level: Optional[str] = None,
    log_llm_io: Optional[bool] = None,
    log_llm_io_max: Optional[int] = None,
    log_format: Optional[str] = None,
) -> None:
    """Apply centralized logging configuration.

    Parameters override env vars which override defaults.
    Safe to call multiple times (idempotent handler setup).
    """
    global LOG_LLM_IO, LOG_LLM_IO_MAX

    # Resolve values: explicit arg > env var > default
    root_level = getattr(logging, (log_level or os.environ.get("LOG_LEVEL", "INFO")).upper(), logging.INFO)
    LOG_LLM_IO = log_llm_io if log_llm_io is not None else _env_bool("LOG_LLM_IO")
    LOG_LLM_IO_MAX = log_llm_io_max if log_llm_io_max is not None else _env_int("LOG_LLM_IO_MAX", 2000)

    # In verbose LLM mode, disable truncation so developers see full payloads
    if LOG_LLM_IO and LOG_LLM_IO_MAX > 0 and log_llm_io_max is None:
        if not os.environ.get("LOG_LLM_IO_MAX"):
            LOG_LLM_IO_MAX = 0

    fmt_name = (log_format or os.environ.get("LOG_FORMAT", "text")).strip().lower()

    # ---------- root handler ----------
    root = logging.getLogger()
    root.setLevel(root_level)

    # Remove pre-existing handlers to make this idempotent
    if root.handlers:
        root.handlers.clear()

    handler = logging.StreamHandler()
    handler.setLevel(logging.DEBUG)  # handler passes everything; loggers decide

    if fmt_name == "json":
        handler.setFormatter(_JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-7s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        ))
    root.addHandler(handler)

    # ---------- per-namespace levels ----------
    _namespace_levels = {
        "adk_agentic_writer.agents":    _env_level("LOG_LEVEL_AGENTS", "INFO"),
        "adk_agentic_writer.backend":   _env_level("LOG_LEVEL_API", "INFO"),
        "httpx":                        _env_level("LOG_LEVEL_HTTPX", "WARNING"),
        "google_adk":                   _env_level("LOG_LEVEL_ADK", "WARNING"),
        "google_genai":                 _env_level("LOG_LEVEL_ADK", "WARNING"),
        # Suppress uvicorn's access log; our request_trace middleware covers it
        "uvicorn.access":               logging.WARNING,
    }
    for ns, lvl in _namespace_levels.items():
        logging.getLogger(ns).setLevel(lvl)

    # Suppress false-positive "App name mismatch" from ADK runners.
    # The heuristic fires because google.adk.agents lives under the venv
    # inside the project root, making the ADK think "agents" is the app name.
    _adk_runner_log = logging.getLogger("google_adk.google.adk.runners")
    _adk_runner_log.addFilter(
        lambda r: "App name mismatch" not in r.getMessage()
    )

    if LOG_LLM_IO:
        logging.getLogger("adk_agentic_writer.agents").setLevel(logging.DEBUG)


# ---------------------------------------------------------------------------
# Helpers for LLM I/O logging
# ---------------------------------------------------------------------------

_SEPARATOR = "─" * 72


def _maybe_truncate(text: str) -> str:
    if LOG_LLM_IO_MAX and len(text) > LOG_LLM_IO_MAX:
        return text[:LOG_LLM_IO_MAX] + f"\n… [{len(text)} chars total, truncated]"
    return text


def log_llm_prompt(logger: logging.Logger, agent_name: str, prompt: str) -> None:
    """Log the full assembled prompt sent to the LLM."""
    if not LOG_LLM_IO:
        return
    level = _env_level("LOG_LEVEL_LLM", "DEBUG")
    body = _maybe_truncate(prompt)
    logger.log(
        level,
        "\n%s\n[%s] PROMPT  (%d chars)\n%s\n%s\n%s",
        _SEPARATOR, agent_name, len(prompt), _SEPARATOR,
        body, _SEPARATOR,
    )


def log_llm_response(logger: logging.Logger, agent_name: str, response: dict) -> None:
    """Log the parsed JSON response from the LLM."""
    if not LOG_LLM_IO:
        return
    level = _env_level("LOG_LEVEL_LLM", "DEBUG")
    text = json.dumps(response, indent=2, ensure_ascii=False)
    body = _maybe_truncate(text)
    logger.log(
        level,
        "\n%s\n[%s] RESPONSE  (%d chars)\n%s\n%s\n%s",
        _SEPARATOR, agent_name, len(text), _SEPARATOR,
        body, _SEPARATOR,
    )


def log_settings_summary() -> None:
    """Log current logging configuration at INFO level."""
    logger = logging.getLogger("adk_agentic_writer.log_config")
    logger.info(
        "Logging configured: root=%s, llm_io=%s (max=%d chars), format=%s",
        logging.getLevelName(logging.getLogger().level),
        LOG_LLM_IO,
        LOG_LLM_IO_MAX,
        "json" if isinstance(logging.getLogger().handlers[0].formatter, _JsonFormatter) else "text",
    )
