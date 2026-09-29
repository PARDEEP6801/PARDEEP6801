"""Model providers (NVIDIA NIM, OpenRouter) behind one OpenAI-compatible client.

Only the Python standard library is used.
"""

import json
import os
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent

PROVIDERS = {
    "nvidia": {
        "label": "NVIDIA",
        "base_url": "https://integrate.api.nvidia.com/v1",
        "key_env": "NVIDIA_API_KEY",
        "key_url": "https://build.nvidia.com",
        # Shown first in the dropdown; the live list from the API is added after.
        "favorites": [
            "meta/llama-3.3-70b-instruct",
            "meta/llama-3.1-405b-instruct",
            "meta/llama-3.1-8b-instruct",
            "deepseek-ai/deepseek-r1",
            "qwen/qwen2.5-coder-32b-instruct",
            "nvidia/llama-3.1-nemotron-70b-instruct",
            "mistralai/mixtral-8x22b-instruct-v0.1",
            "google/gemma-2-27b-it",
        ],
    },
    "openrouter": {
        "label": "OpenRouter",
        "base_url": "https://openrouter.ai/api/v1",
        "key_env": "OPENROUTER_API_KEY",
        "key_url": "https://openrouter.ai/keys",
        "favorites": [],
    },
}

# Model ids containing these are not chat models (embeddings, safety, vision parsers...).
NON_CHAT_HINTS = ("embed", "rerank", "reward", "guard", "safety", "clip", "parse",
                  "ocr", "detect", "retriever", "paddle", "deplot", "kosmos")

_model_cache = {}
CACHE_SECONDS = 600


class ProviderError(Exception):
    pass


def load_env(path=ROOT / ".env"):
    """Minimal .env loader: KEY=value lines, # comments ignored."""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def api_key(provider):
    return os.environ.get(PROVIDERS[provider]["key_env"], "").strip()


def status():
    return {
        name: {"label": p["label"], "has_key": bool(api_key(name)),
               "key_env": p["key_env"], "key_url": p["key_url"]}
        for name, p in PROVIDERS.items()
    }


def _request(provider, path, payload=None):
    if provider not in PROVIDERS:
        raise ProviderError(f"Unknown provider: {provider}")
    key = api_key(provider)
    if not key:
        raise ProviderError(f"{PROVIDERS[provider]['key_env']} is not set. Add it to the .env file and restart.")
    req = urllib.request.Request(PROVIDERS[provider]["base_url"] + path)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Accept", "application/json")
    if provider == "openrouter":
        req.add_header("HTTP-Referer", "http://localhost")
        req.add_header("X-Title", "AI Studio")
    if payload is not None:
        req.add_header("Content-Type", "application/json")
        req.data = json.dumps(payload).encode()
    try:
        return urllib.request.urlopen(req, timeout=300)
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            detail = json.loads(body)
            detail = detail.get("detail") or detail.get("error", {}).get("message") or body
        except (ValueError, AttributeError):
            detail = body
        raise ProviderError(f"{PROVIDERS[provider]['label']} error {e.code}: {str(detail)[:500]}") from None
    except urllib.error.URLError as e:
        raise ProviderError(f"Could not reach {PROVIDERS[provider]['label']}: {e.reason}") from None


def _is_free_openrouter(m):
    pricing = m.get("pricing") or {}
    return m["id"].endswith(":free") or (
        str(pricing.get("prompt")) in ("0", "0.0") and str(pricing.get("completion")) in ("0", "0.0"))


def list_models(provider, free_only=True, chat_only=True):
    """Return [{"id", "favorite"}] with favorites first, then the rest A-Z."""
    cache_key = (provider, free_only, chat_only)
    cached = _model_cache.get(cache_key)
    if cached and time.time() - cached[0] < CACHE_SECONDS:
        return cached[1]

    with _request(provider, "/models") as resp:
        data = json.load(resp).get("data", [])

    ids = set()
    for m in data:
        mid = m.get("id", "")
        if not mid:
            continue
        if chat_only and any(h in mid.lower() for h in NON_CHAT_HINTS):
            continue
        if provider == "openrouter" and free_only and not _is_free_openrouter(m):
            continue
        ids.add(mid)

    favorites = [m for m in PROVIDERS[provider]["favorites"] if m in ids]
    models = [{"id": m, "favorite": True} for m in favorites]
    models += [{"id": m, "favorite": False} for m in sorted(ids - set(favorites))]
    _model_cache[cache_key] = (time.time(), models)
    return models


def stream_chat(provider, model, messages, temperature=0.7, max_tokens=2048, top_p=0.95):
    """Yield ("text" | "reasoning", chunk) tuples, then ("usage", dict) if sent."""
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": True,
    }
    with _request(provider, "/chat/completions", payload) as resp:
        for raw in resp:
            line = raw.decode("utf-8", errors="replace").strip()
            # Blank lines separate events; lines starting with ":" are keep-alive comments.
            if not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if data == "[DONE]":
                break
            try:
                event = json.loads(data)
            except ValueError:
                continue
            if "error" in event:
                raise ProviderError(str(event["error"].get("message", event["error"])))
            for choice in event.get("choices", []):
                delta = choice.get("delta") or {}
                reasoning = delta.get("reasoning_content") or delta.get("reasoning")
                if reasoning:
                    yield "reasoning", reasoning
                if delta.get("content"):
                    yield "text", delta["content"]
            if event.get("usage"):
                yield "usage", event["usage"]
