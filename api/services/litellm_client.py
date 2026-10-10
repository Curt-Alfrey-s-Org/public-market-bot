"""
LiteLLM client for distributed inference via the ALFa AI brain's LiteLLM proxy.

market-pie5-bot runs on ``; the ALFa AI brain (LiteLLM proxy) runs on
``. All inference goes over the LAN to `http://192.0.2.30` using the
OpenAI-compatible API. The Docker DNS name `alfa-ai-litellm:4000` is NOT
resolvable from `` -- do not use it here.

Two surfaces are provided:
- `LiteLLMClient` (async) for FastAPI routes / async services.
- `litellm_chat_completion_sync()` for synchronous call sites (the TradingBot
  in `main.py` and `ml_param_optimizer.py`, which use `requests`).

Both degrade gracefully: on any failure they return an error object rather than
raising, so the trading bot and API keep serving when the brain is unreachable.

Environment:
    LITELLM_ENABLED              true/1/yes to enable (default: false)
    LITELLM_BASE_URL             proxy URL (default: http://192.0.2.30)
    LITELLM_API_KEY              bearer key (matches LITELLM_MASTER_KEY on )
    LITELLM_API_KEY_APP          optional key for app_authenticated zone
    LITELLM_API_KEY_INTERNAL     optional key for internal (admin) zone
    LITELLM_MODEL_CHAT           default chat alias (default: app-chat)
    LITELLM_MODEL_PAGE_QUESTION  alias for /ask narrative (else LITELLM_MODEL_CHAT)
    LITELLM_MODEL_INTERNAL       alias for internal/admin triage (default: code)
    LITELLM_TIMEOUT              request timeout in seconds (default: 600)
"""

import logging
import os
import time
from typing import Any, Dict, List, Optional

import httpx

from api.services.llm_types import LLMResponse

logger = logging.getLogger(__name__)

# Trust zones for LiteLLM routing (see docs/ALFA_AI_TRUST_ZONES_AND_ROLLOUT.md)
TRUST_ZONE_PUBLIC_WEB = "public_web"
TRUST_ZONE_APP = "app_authenticated"
TRUST_ZONE_INTERNAL = "internal"

DEFAULT_BASE_URL = "http://192.0.2.30"
DEFAULT_MODEL_CHAT = "app-chat"
DEFAULT_MODEL_INTERNAL = "code"
def _get_env(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def is_litellm_enabled() -> bool:
    return _get_env("LITELLM_ENABLED", "false").lower() in ("true", "1", "yes")


def get_litellm_base_url() -> str:
    return _get_env("LITELLM_BASE_URL", DEFAULT_BASE_URL) or DEFAULT_BASE_URL


def get_litellm_api_key() -> str:
    """No shared dev default (audit D-003 / LiteLLM virtual keys)."""
    return _get_env("LITELLM_API_KEY", "")


def litellm_missing_config() -> List[str]:
    """Names of the env vars that must be fixed before the brain can be used.

    Empty list means the LiteLLM client is configured (reachability is checked
    separately by litellm_health_sync). Used to give a clear startup error
    naming the variable instead of a generic "brain unreachable".
    """
    missing: List[str] = []
    if not is_litellm_enabled():
        missing.append("LITELLM_ENABLED")
    if not get_litellm_api_key():
        missing.append("LITELLM_API_KEY")
    return missing


def litellm_model_for_trust_zone(zone: str) -> str:
    """Alias names must exist in ALFa AI deploy/litellm_config.yaml (repo: alfa-ai/)."""
    if zone == TRUST_ZONE_INTERNAL:
        return _get_env("LITELLM_MODEL_INTERNAL", DEFAULT_MODEL_INTERNAL) or DEFAULT_MODEL_INTERNAL
    page = _get_env("LITELLM_MODEL_PAGE_QUESTION", "")
    if page:
        return page
    return _get_env("LITELLM_MODEL_CHAT", DEFAULT_MODEL_CHAT) or DEFAULT_MODEL_CHAT


def _api_key_for_trust_zone(zone: str) -> str:
    if zone == TRUST_ZONE_INTERNAL:
        return _get_env("LITELLM_API_KEY_INTERNAL") or get_litellm_api_key()
    if zone == TRUST_ZONE_APP:
        return _get_env("LITELLM_API_KEY_APP") or get_litellm_api_key()
    return get_litellm_api_key()


class LiteLLMClient:
    """
    Async client for the LiteLLM proxy (OpenAI-compatible API).

    All public methods degrade gracefully and return LLMResponse with
    `error` set rather than raising.
    """

    MAX_RETRIES = 2
    RETRY_BACKOFF_SECONDS = 2.0

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
        model_chat: Optional[str] = None,
    ):
        self.base_url = (base_url or get_litellm_base_url()).rstrip("/")
        self.api_key = (api_key if api_key is not None else get_litellm_api_key()) or ""
        if not self.api_key:
            raise ValueError(
                "LITELLM_API_KEY is required (no shared change-me default)"
            )
        self.timeout = timeout or float(_get_env("LITELLM_TIMEOUT", "600"))
        self.model_chat = model_chat or _get_env("LITELLM_MODEL_CHAT", DEFAULT_MODEL_CHAT)
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=httpx.Timeout(self.timeout, connect=15.0),
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def health(self) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            client = await self._get_client()
            resp = await client.get("/health/liveliness", timeout=10.0)
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            return {
                "status": "healthy" if resp.status_code == 200 else "degraded",
                "latency_ms": latency_ms,
                "base_url": self.base_url,
                "model_chat": self.model_chat,
            }
        except Exception as e:
            latency_ms = round((time.perf_counter() - start) * 1000, 2)
            logger.warning("LiteLLM health check failed: %s", e)
            return {
                "status": "unreachable",
                "latency_ms": latency_ms,
                "base_url": self.base_url,
                "error": str(e)[:200],
            }

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 2048,
        feature: str = "litellm_chat",
        log_metadata: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """Chat completion via the LiteLLM proxy (OpenAI format)."""
        model = model or self.model_chat
        body = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        request_text = "\n".join(
            f"[{m.get('role', '?')}] {m.get('content', '')}" for m in messages
        )
        resp = await self._post_with_retry("/v1/chat/completions", body, model)
        _log_activity(feature, model, request_text, resp, log_metadata)
        if not resp.error and resp.content:
            _maybe_capture_finetune(feature, messages, resp.content, model, log_metadata)
        return resp

    async def _post_with_retry(
        self, endpoint: str, body: Dict[str, Any], model: str
    ) -> LLMResponse:
        import asyncio

        last_error: Optional[str] = None
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                client = await self._get_client()
                start = time.perf_counter()
                resp = await client.post(endpoint, json=body)
                elapsed = time.perf_counter() - start

                if resp.status_code != 200:
                    error_text = resp.text[:300]
                    logger.warning(
                        "LiteLLM %s returned %d (attempt %d/%d): %s",
                        endpoint, resp.status_code, attempt, self.MAX_RETRIES, error_text,
                    )
                    last_error = f"HTTP {resp.status_code}: {error_text}"
                    if attempt < self.MAX_RETRIES:
                        await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * attempt)
                        continue
                    return LLMResponse(
                        content="",
                        model=model,
                        done=False,
                        error=last_error,
                        total_duration_ns=int(elapsed * 1e9),
                    )

                data = resp.json()
                choices = data.get("choices", [])
                content = ""
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                usage = data.get("usage", {})
                eval_count = usage.get("completion_tokens", 0)
                prompt_count = usage.get("prompt_tokens", 0)
                logger.info(
                    "LiteLLM %s [%s] completed in %.1fs (tokens=%d)",
                    endpoint, model, elapsed, eval_count,
                )
                return LLMResponse(
                    content=content,
                    model=data.get("model", model),
                    done=True,
                    total_duration_ns=int(elapsed * 1e9),
                    eval_count=eval_count,
                    prompt_eval_count=prompt_count,
                )
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.warning(
                    "LiteLLM %s attempt %d/%d failed: %s",
                    endpoint, attempt, self.MAX_RETRIES, last_error,
                )
                if attempt < self.MAX_RETRIES:
                    await asyncio.sleep(self.RETRY_BACKOFF_SECONDS * attempt)
            except Exception as e:
                last_error = f"{type(e).__name__}: {e}"
                logger.error("LiteLLM %s unexpected error: %s", endpoint, last_error)
                break
        return LLMResponse(content="", model=model, done=False, error=last_error)


def litellm_health_sync(timeout: float = 10.0) -> Dict[str, Any]:
    """
    Synchronous liveliness probe for the LiteLLM proxy (the ALFa AI brain).

    Returns: {"ok": bool, "status": str, "base_url": str, "error": Optional[str]}.
    Never raises. `status` is one of: "healthy", "degraded", "unreachable",
    "disabled". When LITELLM_ENABLED is false, ok=False / status="disabled"
    (a disabled brain counts as "down" for any caller that requires it).

    Used by the bot lifecycle gate so the trader will not start/continue when
    the brain is unreachable (see BOT_REQUIRE_BRAIN in api/bot_manager.py).
    """
    import requests

    base_url = get_litellm_base_url().rstrip("/")
    if not is_litellm_enabled():
        return {"ok": False, "status": "disabled", "base_url": base_url, "error": "litellm_disabled"}
    try:
        resp = requests.get(
            f"{base_url}/health/liveliness",
            headers={"Authorization": f"Bearer {get_litellm_api_key()}"},
            timeout=timeout,
        )
        ok = resp.status_code == 200
        return {
            "ok": ok,
            "status": "healthy" if ok else "degraded",
            "base_url": base_url,
            "error": None if ok else f"HTTP {resp.status_code}",
        }
    except Exception as e:  # noqa: BLE001 - graceful degrade
        return {"ok": False, "status": "unreachable", "base_url": base_url, "error": f"{type(e).__name__}: {e}"}


def litellm_embeddings_sync(
    texts: List[str],
    model: Optional[str] = None,
    timeout: Optional[float] = None,
    trust_zone: str = TRUST_ZONE_APP,
) -> Dict[str, Any]:
    """
    Synchronous embeddings against the LiteLLM proxy (`/v1/embeddings`).

    Returns: {"vectors": List[List[float]], "model": str, "error": Optional[str]}.
    Never raises. Used by the RAG indexer/retriever.
    """
    import requests

    if not is_litellm_enabled():
        return {"vectors": [], "model": model or "", "error": "litellm_disabled"}
    if not texts:
        return {"vectors": [], "model": model or "", "error": None}

    base_url = get_litellm_base_url().rstrip("/")
    api_key = _api_key_for_trust_zone(trust_zone)
    resolved_model = model or _get_env("LITELLM_MODEL_EMBED", "embed") or "embed"
    req_timeout = timeout if timeout is not None else float(_get_env("LITELLM_TIMEOUT", "600"))

    try:
        resp = requests.post(
            f"{base_url}/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": resolved_model, "input": texts},
            timeout=req_timeout,
        )
        if resp.status_code != 200:
            return {"vectors": [], "model": resolved_model, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        data = resp.json()
        items = sorted(data.get("data", []), key=lambda d: d.get("index", 0))
        vectors = [it.get("embedding", []) for it in items]
        return {"vectors": vectors, "model": data.get("model", resolved_model), "error": None}
    except requests.exceptions.Timeout:
        return {"vectors": [], "model": resolved_model, "error": "Request timeout"}
    except Exception as e:  # noqa: BLE001 - graceful degrade
        return {"vectors": [], "model": resolved_model, "error": f"{type(e).__name__}: {e}"}


def _maybe_capture_finetune(
    feature: str,
    messages: List[Dict[str, str]],
    completion: str,
    model: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Opt-in fine-tune capture (no-op unless FINETUNE_CAPTURE_ENABLED). Never raises."""
    try:
        from api.services.finetune_capture import capture_sample, is_capture_enabled

        if not is_capture_enabled():
            return
        zone = (metadata or {}).get("trust_zone", TRUST_ZONE_APP)
        capture_sample(feature, messages, completion, model=model, trust_zone=zone)
    except Exception:
        pass


def _log_activity(
    feature: str,
    model: str,
    request_text: str,
    resp: LLMResponse,
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """Best-effort log to the ollama_activity_log table. Never raises."""
    try:
        from api.services.ollama_activity_log import log_ollama_activity

        log_ollama_activity(
            feature=feature,
            model=f"litellm/{model}",
            request_text=request_text,
            response_text=resp.content,
            duration_seconds=resp.duration_seconds,
            eval_tokens=resp.eval_count,
            prompt_tokens=resp.prompt_eval_count,
            status="success" if not resp.error else "error",
            error_message=resp.error,
            metadata=metadata,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Per-trust-zone async clients
# ---------------------------------------------------------------------------

_clients_by_zone: Dict[str, LiteLLMClient] = {}


def get_litellm_client_for_trust_zone(zone: str) -> Optional[LiteLLMClient]:
    """Return a LiteLLM client for the given trust zone if LITELLM_ENABLED=true."""
    if not is_litellm_enabled():
        return None
    if zone not in _clients_by_zone:
        _clients_by_zone[zone] = LiteLLMClient(api_key=_api_key_for_trust_zone(zone))
        logger.info(
            "LiteLLMClient initialized for zone=%s base_url=%s default_model=%s",
            zone,
            _clients_by_zone[zone].base_url,
            _clients_by_zone[zone].model_chat,
        )
    return _clients_by_zone[zone]


def get_litellm_client() -> Optional[LiteLLMClient]:
    """Shared app-trust-zone client (backward compatible)."""
    return get_litellm_client_for_trust_zone(TRUST_ZONE_APP)


# ---------------------------------------------------------------------------
# Synchronous helper for the TradingBot (main.py, ml_param_optimizer.py)
# ---------------------------------------------------------------------------


def litellm_chat_completion_sync(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.3,
    max_tokens: int = 1000,
    timeout: Optional[float] = None,
    feature: str = "trading_bot",
    trust_zone: str = TRUST_ZONE_APP,
) -> Dict[str, Any]:
    """
    Synchronous chat completion against the LiteLLM proxy using `requests`.

    Designed for the synchronous TradingBot call sites. Returns a dict:
        {"content": str, "model": str, "error": Optional[str], "raw": dict}

    Never raises. If LITELLM_ENABLED is false or the brain is unreachable, the
    returned dict has `error` set and empty `content`.
    """
    import requests

    if not is_litellm_enabled():
        return {"content": "", "model": model or "", "error": "litellm_disabled", "raw": {}}

    base_url = get_litellm_base_url().rstrip("/")
    api_key = _api_key_for_trust_zone(trust_zone)
    resolved_model = model or litellm_model_for_trust_zone(trust_zone)
    req_timeout = timeout if timeout is not None else float(_get_env("LITELLM_TIMEOUT", "600"))

    payload = {
        "model": resolved_model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    request_text = "\n".join(
        f"[{m.get('role', '?')}] {m.get('content', '')}" for m in messages
    )

    start = time.perf_counter()
    content = ""
    error: Optional[str] = None
    raw: Dict[str, Any] = {}
    eval_tokens = 0
    prompt_tokens = 0
    try:
        resp = requests.post(
            f"{base_url}/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=req_timeout,
        )
        if resp.status_code == 200:
            raw = resp.json()
            choices = raw.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
            usage = raw.get("usage", {})
            eval_tokens = usage.get("completion_tokens", 0)
            prompt_tokens = usage.get("prompt_tokens", 0)
        else:
            error = f"HTTP {resp.status_code}: {resp.text[:300]}"
    except requests.exceptions.Timeout:
        error = "Request timeout"
    except Exception as e:  # noqa: BLE001 - graceful degrade
        error = f"{type(e).__name__}: {e}"

    elapsed = time.perf_counter() - start
    try:
        from api.services.ollama_activity_log import log_ollama_activity

        log_ollama_activity(
            feature=feature,
            model=f"litellm/{resolved_model}",
            request_text=request_text,
            response_text=content,
            duration_seconds=elapsed,
            eval_tokens=eval_tokens,
            prompt_tokens=prompt_tokens,
            status="success" if not error else "error",
            error_message=error,
            metadata={"trust_zone": trust_zone, "sync": True},
        )
    except Exception:
        pass

    if not error and content:
        _maybe_capture_finetune(
            feature, messages, content, resolved_model, {"trust_zone": trust_zone}
        )

    return {"content": content, "model": resolved_model, "error": error, "raw": raw}
