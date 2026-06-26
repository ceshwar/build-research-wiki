#!/usr/bin/env python3
"""Thin LLM client for Portolan — Ollama (local) and optional frontier APIs."""

import json
import os
import urllib.error
import urllib.request

from llm_grounding import sanitize_llm_output

DEFAULT_OLLAMA = "http://127.0.0.1:11500"
DEFAULT_TIMEOUT = 180


def _ollama_unreachable(url, exc):
    detail = str(exc)
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read().decode() if exc.fp else ""
            if body:
                detail = body[:240]
        except Exception:
            pass
        if "permission denied" in detail.lower() or "ollama-models" in detail.lower():
            return RuntimeError(
                "Ollama server error at {} — models path not writable. "
                "On the GPU server run: chmod o+x /home/eshwar && "
                "sudo chown -R ollama:ollama /home/eshwar/ollama-models && "
                "sudo systemctl restart ollama. ({})".format(url, detail[:120])
            )
    return RuntimeError(
        "Ollama unreachable at {} — start the SSH tunnel "
        "(ssh -N -L 127.0.0.1:11500:127.0.0.1:11434 …) or check Settings. {}".format(url, detail)
    )


def chat_ollama(
    model,
    messages,
    ollama_url=None,
    think=False,
    temperature=0.2,
    num_predict=1200,
    timeout=DEFAULT_TIMEOUT,
    json_format=False,
):
    url = (ollama_url or os.environ.get("OLLAMA_URL") or DEFAULT_OLLAMA).rstrip("/")
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "think": bool(think),
        "options": {"temperature": temperature, "num_predict": num_predict},
    }
    if json_format:
        payload["format"] = "json"
    req = urllib.request.Request(
        f"{url}/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.URLError as exc:
        raise _ollama_unreachable(url, exc) from exc
    msg = data.get("message") or {}
    content = sanitize_llm_output(msg.get("content", ""))
    return {
        "content": content,
        "eval_count": data.get("eval_count"),
        "model": model,
        "provider": "ollama",
    }


def chat_ollama_json(model, messages, ollama_url=None, think=False, **opts):
    """Ollama chat with structured JSON output (format: json)."""
    result = chat_ollama(
        model, messages, ollama_url=ollama_url, think=think, json_format=True, **opts
    )
    raw = result.get("content") or ""
    try:
        result["json"] = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise RuntimeError("LLM returned invalid JSON: {}".format(exc)) from exc
    return result


def chat_frontier(model, messages, provider="anthropic", api_key=None, timeout=300):
    """Frontier chat — Anthropic or OpenAI. Requires API key in env or argument."""
    provider = (provider or "anthropic").lower()
    if provider == "anthropic":
        api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set — configure in Settings or environment.")
        system_parts = [m["content"] for m in messages if m.get("role") == "system"]
        user_parts = [m for m in messages if m.get("role") != "system"]
        body = {
            "model": model,
            "max_tokens": 4096,
            "temperature": 0.2,
            "messages": [{"role": m["role"], "content": m["content"]} for m in user_parts],
        }
        if system_parts:
            body["system"] = "\n\n".join(system_parts)
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages",
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.URLError as exc:
            raise RuntimeError("Frontier API unreachable: {}".format(exc)) from exc
        blocks = data.get("content") or []
        text = sanitize_llm_output("".join(b.get("text", "") for b in blocks if b.get("type") == "text"))
        return {"content": text, "eval_count": None, "model": model, "provider": "anthropic"}

    if provider == "openai":
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set — configure in Settings or environment.")
        body = {"model": model, "messages": messages, "temperature": 0.2}
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {api_key}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.URLError as exc:
            raise RuntimeError("Frontier API unreachable: {}".format(exc)) from exc
        choice = (data.get("choices") or [{}])[0]
        text = sanitize_llm_output((choice.get("message") or {}).get("content", ""))
        return {"content": text, "eval_count": None, "model": model, "provider": "openai"}

    raise ValueError(f"Unknown frontier provider: {provider}")


def chat_json(provider_kind, model, messages, ollama_url=None, frontier_provider=None, think=False, **opts):
    """Structured JSON — Ollama uses format:json; frontier parses JSON from text."""
    if provider_kind == "frontier":
        result = chat_frontier(model, messages, provider=frontier_provider or "anthropic", **opts)
        raw = result.get("content") or ""
        try:
            result["json"] = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Frontier model returned invalid JSON: {}".format(exc)) from exc
        return result
    return chat_ollama_json(model, messages, ollama_url=ollama_url, think=think, **opts)


def chat(provider_kind, model, messages, ollama_url=None, frontier_provider=None, think=False, **ollama_opts):
    """Unified chat — provider_kind: 'local' | 'frontier'."""
    if provider_kind == "frontier":
        return chat_frontier(model, messages, provider=frontier_provider or "anthropic", **ollama_opts)
    return chat_ollama(model, messages, ollama_url=ollama_url, think=think, **ollama_opts)
