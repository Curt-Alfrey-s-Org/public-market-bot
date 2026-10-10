#!/usr/bin/env python3
"""
Dev-time code helper backed by the ALFa AI brain (LiteLLM `code` alias).

A thin CLI for code review / explain / docstring drafting during development.
Internal trust zone only — uses the `code` model. Never wire this into the
request path; it is a developer tool.

Usage (from , with LITELLM_ENABLED=true):
    python3 scripts/codegen/ai_codegen.py review path/to/file.py
    python3 scripts/codegen/ai_codegen.py explain path/to/file.py
    git diff | python3 scripts/codegen/ai_codegen.py review -   # read stdin
"""

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

_PROMPTS = {
    "review": (
        "You are a senior Python/TypeScript reviewer for the market-pie5-bot "
        "trading app. Review the following code for correctness, security "
        "(secret handling, injection), error handling, and clarity. Be concise "
        "and list issues as Critical / Warning / Suggestion."
    ),
    "explain": (
        "Explain what the following code does in plain English for a new "
        "contributor. Note any non-obvious behavior or risks."
    ),
    "docstring": (
        "Draft concise docstrings for the public functions/classes in the "
        "following code. Return only the docstrings keyed by symbol name."
    ),
}


def _read_input(target: str) -> str:
    if target == "-":
        return sys.stdin.read()
    p = Path(target)
    if not p.is_absolute():
        p = (PROJECT_ROOT / target).resolve()
    if not str(p).startswith(str(PROJECT_ROOT)):
        raise SystemExit("Refusing to read outside the repository.")
    return p.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description="ALFa AI dev code helper (LiteLLM code)")
    parser.add_argument("mode", choices=sorted(_PROMPTS.keys()))
    parser.add_argument("target", help="File path, or '-' to read stdin")
    parser.add_argument("--max-tokens", type=int, default=1200)
    args = parser.parse_args()

    from api.services.litellm_client import (
        is_litellm_enabled,
        litellm_chat_completion_sync,
        litellm_model_for_trust_zone,
        TRUST_ZONE_INTERNAL,
    )

    if not is_litellm_enabled():
        print("ERROR: LITELLM_ENABLED is not true. Enable the ALFa AI brain first.")
        return 2

    content = _read_input(args.target)
    if not content.strip():
        print("ERROR: empty input.")
        return 1

    model = litellm_model_for_trust_zone(TRUST_ZONE_INTERNAL)
    result = litellm_chat_completion_sync(
        [
            {"role": "system", "content": _PROMPTS[args.mode]},
            {"role": "user", "content": content[:24000]},
        ],
        model=model,
        temperature=0.1,
        max_tokens=args.max_tokens,
        feature=f"codegen_{args.mode}",
        trust_zone="internal",
    )
    if result.get("error"):
        print(f"ERROR: {result['error']}")
        return 3
    print(result.get("content", ""))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
