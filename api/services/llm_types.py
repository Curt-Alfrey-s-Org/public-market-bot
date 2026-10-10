"""
Shared LLM response type for the ALFa AI brain (LiteLLM) call sites.

The ALFa AI brain is the single AI provider for this repo. This module defines
the structured response returned by `api/services/litellm_client.py`. It was
previously defined in `ollama_client.py`; the direct-Ollama client has been
removed (all inference goes through the brain's LiteLLM proxy on ``).
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class LLMResponse:
    """Structured response from an LLM call via the ALFa AI brain (LiteLLM)."""

    content: str
    model: str
    done: bool = True
    total_duration_ns: int = 0
    eval_count: int = 0
    prompt_eval_count: int = 0
    error: Optional[str] = None

    @property
    def eval_tokens(self) -> int:
        return self.eval_count

    @property
    def prompt_tokens(self) -> int:
        return self.prompt_eval_count

    @property
    def duration_seconds(self) -> float:
        return self.total_duration_ns / 1e9 if self.total_duration_ns else 0.0


# Backward-compatible alias: some call sites and tests still import the old name.
OllamaResponse = LLMResponse
