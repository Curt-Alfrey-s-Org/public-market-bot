"""
Per-page "Ask AI" narrative route.

Provides factual, plain-English narration of the data already shown on a page
(performance, decisions, settings) via the ALFa AI brain (LiteLLM,
app_authenticated zone). Hard rules:

- NOT FINANCIAL ADVICE: a disclaimer is always appended server-side and the
  system prompt forbids buy/sell recommendations or price predictions.
- Trust boundary: context is re-sanitized server-side (see
  market_ask_ai_context) so Schwab tokens/balances/secrets never leave the host.
- Graceful degrade: if LiteLLM is disabled/unreachable the endpoint returns a
  friendly message (still with the disclaimer), never a 5xx.
"""

import logging
from typing import Any, List, Literal, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from api.services.market_ask_ai_context import build_page_context, is_allowed_page

logger = logging.getLogger(__name__)

router = APIRouter()

DISCLAIMER = (
    "NOT FINANCIAL ADVICE. This is an automated, factual summary of data shown "
    "in this app for a simulated/educational trading bot. It is not a "
    "recommendation to buy or sell any security. Do your own research."
)

_SYSTEM_PROMPT = (
    "You are a factual narration assistant embedded in the market-pie5-bot "
    "trading dashboard. You explain, in plain English, the data the user is "
    "already looking at on the current page. STRICT RULES: "
    "(1) Never give financial advice, buy/sell recommendations, or price "
    "predictions. (2) Never claim to know future performance. (3) Only use the "
    "provided context; if something is not in the context, say you don't have "
    "that information. (4) Be concise (<= 180 words). (5) Do not reveal account "
    "numbers, balances, or credentials — they are intentionally not provided."
)


class HistoryTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(..., min_length=1, max_length=8000)


class AskAIRequest(BaseModel):
    page: str
    question: str
    context: Optional[Any] = None
    player_name: str = Field(default="", max_length=300)
    history: List[HistoryTurn] = Field(default_factory=list, max_length=40)
    model: Optional[str] = None


class ChatModelOption(BaseModel):
    id: str
    label: str
    description: str = ""
    available: bool
    reason: Optional[str] = None


class ModelsResponse(BaseModel):
    models: List[ChatModelOption]
    litellm_enabled: bool


class AskAIResponse(BaseModel):
    answer: str
    error: Optional[str] = None
    disclaimer: str = DISCLAIMER
    model: Optional[str] = None
    degraded: bool = False


def _degraded(message: str) -> dict:
    return {
        "answer": f"{message}\n\n{DISCLAIMER}",
        "error": None,
        "disclaimer": DISCLAIMER,
        "model": None,
        "degraded": True,
    }


def _with_disclaimer(text: str) -> str:
    body = (text or "").strip()
    if not body:
        return DISCLAIMER
    if DISCLAIMER in body:
        return body
    return f"{body}\n\n{DISCLAIMER}"


@router.get("/models", response_model=ModelsResponse)
async def list_chat_models():
    """Return the single central ALFa model (no client-side picker)."""
    try:
        from api.services.litellm_client import (
            get_litellm_client_for_trust_zone,
            TRUST_ZONE_APP,
            is_litellm_enabled,
            litellm_model_for_trust_zone,
        )
    except Exception as e:
        logger.debug("list_chat_models: litellm import failed: %s", e)
        return ModelsResponse(models=[], litellm_enabled=False)

    model_id = litellm_model_for_trust_zone(TRUST_ZONE_APP)
    enabled = is_litellm_enabled()
    client = get_litellm_client_for_trust_zone(TRUST_ZONE_APP) if enabled else None
    available = bool(enabled and client is not None)
    return ModelsResponse(
        models=[
            ChatModelOption(
                id=model_id,
                label="ALFa AI (via ALFa brain)",
                description="Central tier controlled by ALFa brain admin",
                available=available,
                reason=None if available else "ai_not_ready",
            )
        ],
        litellm_enabled=enabled,
    )


@router.post("/ask", response_model=AskAIResponse)
async def ask_ai(req: AskAIRequest) -> AskAIResponse:
    """Answer a question about the current page using factual narration only."""
    page = (req.page or "").strip().lower()
    if not is_allowed_page(page):
        d = _degraded(
            "Ask AI is not available on this page. Supported pages: dashboard, "
            "trades, pending-trades, decision-report, settings."
        )
        return AskAIResponse(**d)

    question = (req.question or "").strip()
    if not question:
        return AskAIResponse(**_degraded("Please enter a question about what you see on this page."))

    try:
        from api.services.litellm_client import (
            get_litellm_client_for_trust_zone,
            TRUST_ZONE_APP,
            is_litellm_enabled,
            litellm_model_for_trust_zone,
        )
    except Exception as e:
        logger.debug("ask_ai: litellm import failed: %s", e)
        return AskAIResponse(**_degraded("The AI assistant is currently unavailable."))

    if not is_litellm_enabled():
        return AskAIResponse(**_degraded("The AI assistant is not enabled on this deployment."))

    safe = build_page_context(page, req.context)
    client = get_litellm_client_for_trust_zone(TRUST_ZONE_APP)
    if client is None:
        return AskAIResponse(**_degraded("The AI assistant is not enabled on this deployment."))

    import asyncio
    import json

    rag_block = None
    try:
        from api.services.market_rag import build_rag_context

        rag_block = await asyncio.to_thread(build_rag_context, question, 4, 3000)
    except Exception as e:
        logger.debug("ask_ai: RAG retrieval skipped: %s", e)

    user_content = (
        f"Page: {page}\n"
        f"Question: {question[:1000]}\n\n"
        f"Context (sanitized, domain-only):\n{json.dumps(safe['context'])[:6000]}"
    )
    if rag_block:
        user_content += (
            "\n\nRelevant domain documentation (for grounding; cite only if useful):\n"
            f"{rag_block}"
        )

    history_msgs = []
    for turn in req.history or []:
        role = turn.role if turn.role in ("user", "assistant") else "user"
        content = (turn.content or "").strip()
        if content:
            history_msgs.append({"role": role, "content": content[:8000]})

    model = (req.model or "").strip() or litellm_model_for_trust_zone(TRUST_ZONE_APP)
    resp = await client.chat(
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            *history_msgs,
            {"role": "user", "content": user_content},
        ],
        model=model,
        temperature=0.2,
        max_tokens=400,
        feature=f"ask_ai_{page}",
        log_metadata={"trust_zone": TRUST_ZONE_APP, "page": page},
    )

    if resp.error or not resp.content:
        return AskAIResponse(**_degraded("The AI assistant could not reach the inference brain right now."))

    return AskAIResponse(
        answer=_with_disclaimer(resp.content),
        error=None,
        disclaimer=DISCLAIMER,
        model=resp.model,
        degraded=False,
    )
