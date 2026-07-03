"""Configuration for the self-correcting agent.

Everything is overridable via environment variables so you can drop the
package into any project without editing code.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field


def _env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, str(default)))


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.lower() in {"1", "true", "yes", "on"}


@dataclass
class Config:
    # Which Claude model the Author/Grader roles use.
    model: str = field(default_factory=lambda: os.environ.get("SELFCORRECT_MODEL", "claude-sonnet-4-6"))
    # Max self-correction attempts before the agent escalates to a human.
    max_attempts: int = field(default_factory=lambda: _env_int("SELFCORRECT_MAX_ATTEMPTS", 4))
    # Hard timeout (seconds) for each sandboxed pytest run.
    test_timeout: int = field(default_factory=lambda: _env_int("SELFCORRECT_TEST_TIMEOUT", 60))
    # Max tokens per LLM call.
    max_tokens: int = field(default_factory=lambda: _env_int("SELFCORRECT_MAX_TOKENS", 4096))
    # Web UI host/port.
    host: str = field(default_factory=lambda: os.environ.get("SELFCORRECT_HOST", "127.0.0.1"))
    port: int = field(default_factory=lambda: _env_int("SELFCORRECT_PORT", 8765))
    # Use the deterministic offline provider instead of the real API.
    use_mock: bool = field(default_factory=lambda: _env_bool("SELFCORRECT_MOCK"))

    @property
    def has_api_key(self) -> bool:
        return bool(os.environ.get("ANTHROPIC_API_KEY"))
