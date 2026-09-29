#!/usr/bin/env python3
"""AI Studio — local web app to chat with NVIDIA / OpenRouter models and
build your own custom LLM assistants.

Run:  python server.py        then open http://localhost:8000
"""

import json
import os
import re
import sys
import threading
import uuid
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import providers

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
ASSISTANTS_FILE = ROOT / "my_llms.json"

_lock = threading.Lock()

STARTER_LLMS = [
    {
        "id": "coder",
        "name": "Code Guru",
        "provider": "nvidia",
        "model": "qwen/qwen2.5-coder-32b-instruct",
        "system": "You are an expert programmer. Give correct, runnable code with short explanations.",
        "temperature": 0.2,
        "max_tokens": 4096,
    },
    {
        "id": "hinglish",
        "name": "Hinglish Dost",
        "provider": "nvidia",
        "model": "meta/llama-3.3-70b-instruct",
        "system": "Tum ek friendly assistant ho. Hamesha simple Hinglish (Hindi + English, Roman script) mein jawab do.",
        "temperature": 0.7,
        "max_tokens": 2048,
    },
    {
        "id": "trader",
        "name": "Trading Tutor",
        "provider": "nvidia",
        "model": "meta/llama-3.3-70b-instruct",
        "system": ("You are a trading educator. Explain technical analysis, risk management and "
                   "TradingView Pine Script clearly. Never promise profits; always mention risk."),
        "temperature": 0.5,
        "max_tokens": 2048,
    },
]


def load_llms():
    if not ASSISTANTS_FILE.exists():
        save_llms(STARTER_LLMS)
    return json.loads(ASSISTANTS_FILE.read_text(encoding="utf-8"))


def save_llms(items):
    tmp = ASSISTANTS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(ASSISTANTS_FILE)


def clean_llm(data):
    try:
        temperature = min(max(float(data.get("temperature", 0.7)), 0.0), 2.0)
        max_tokens = min(max(int(data.get("max_tokens", 2048)), 16), 32768)
    except (TypeError, ValueError):
        raise ValueError("temperature and max_tokens must be numbers")
    provider = data.get("provider", "nvidia")
    if provider not in providers.PROVIDERS:
        raise ValueError("unknown provider")
    name = str(data.get("name", "")).strip()[:60]
    model = str(data.get("model", "")).strip()
    if not name or not model:
        raise ValueError("name and model are required")
    return {
        "id": re.sub(r"[^a-z0-9-]", "", str(data.get("id") or "")) or uuid.uuid4().hex[:8],
        "name": name,
        "provider": provider,
        "model": model,
        "system": str(data.get("system", ""))[:20000],
        "temperature": temperature,
        "max_tokens": max_tokens,
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "AIStudio/1.0"

    def log_message(self, fmt, *args):
        if "/api/" in (args[0] if args else ""):
            sys.stderr.write("  %s\n" % (fmt % args))

    # ---------- helpers ----------
    def _json(self, obj, status=HTTPStatus.OK):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _error(self, msg, status=HTTPStatus.BAD_REQUEST):
        self._json({"error": msg}, status)

    def _body(self):
        length = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(length) or b"{}")

    def _query(self):
        from urllib.parse import parse_qs, urlparse
        return {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}

    @property
    def route(self):
        return self.path.split("?", 1)[0]

    # ---------- routes ----------
    def do_GET(self):
        if self.route in ("/", "/index.html"):
            body = (STATIC / "index.html").read_bytes()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        elif self.route == "/api/status":
            self._json(providers.status())
        elif self.route == "/api/models":
            q = self._query()
            try:
                models = providers.list_models(
                    q.get("provider", "nvidia"),
                    free_only=q.get("free", "1") == "1",
                    chat_only=q.get("all", "0") != "1",
                )
                self._json({"models": models})
            except providers.ProviderError as e:
                self._error(str(e), HTTPStatus.BAD_GATEWAY)
        elif self.route == "/api/llms":
            with _lock:
                self._json({"llms": load_llms()})
        else:
            self._error("not found", HTTPStatus.NOT_FOUND)

    def do_POST(self):
        try:
            data = self._body()
        except ValueError:
            return self._error("invalid JSON")
        if self.route == "/api/llms":
            try:
                llm = clean_llm(data)
            except ValueError as e:
                return self._error(str(e))
            with _lock:
                items = [x for x in load_llms() if x["id"] != llm["id"]]
                items.append(llm)
                save_llms(items)
            self._json(llm)
        elif self.route == "/api/chat":
            self._chat(data)
        else:
            self._error("not found", HTTPStatus.NOT_FOUND)

    def do_DELETE(self):
        m = re.fullmatch(r"/api/llms/([a-z0-9-]+)", self.route)
        if not m:
            return self._error("not found", HTTPStatus.NOT_FOUND)
        with _lock:
            save_llms([x for x in load_llms() if x["id"] != m.group(1)])
        self._json({"ok": True})

    def _chat(self, data):
        messages = [m for m in data.get("messages", [])
                    if m.get("role") in ("user", "assistant") and isinstance(m.get("content"), str)]
        if data.get("system"):
            messages.insert(0, {"role": "system", "content": data["system"]})
        if not data.get("model") or not messages:
            return self._error("model and messages are required")

        # Stream newline-delimited JSON events back to the browser.
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/x-ndjson")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()

        def send(kind, value):
            self.wfile.write((json.dumps({"type": kind, "v": value}) + "\n").encode())
            self.wfile.flush()

        try:
            for kind, value in providers.stream_chat(
                data.get("provider", "nvidia"), data["model"], messages,
                temperature=float(data.get("temperature", 0.7)),
                max_tokens=int(data.get("max_tokens", 2048)),
            ):
                send(kind, value)
            send("done", None)
        except providers.ProviderError as e:
            send("error", str(e))
        except (BrokenPipeError, ConnectionResetError):
            pass  # browser pressed Stop
        except Exception as e:  # keep the server alive on unexpected errors
            send("error", f"{type(e).__name__}: {e}")


def main():
    providers.load_env()
    for name, s in providers.status().items():
        state = "key found" if s["has_key"] else f"no key (set {s['key_env']} in .env)"
        print(f"  {s['label']:<11} {state}")
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT") or 8000)
    url = f"http://localhost:{port}"
    try:
        server = ThreadingHTTPServer((host, port), Handler)
    except OSError:
        sys.exit(f"\n  Port {port} already in use. .env mein PORT badlo (e.g. PORT=8080) aur dobara chalao.\n")
    print(f"\n  AI Studio running at {url}   (Ctrl+C to stop)\n")
    if "--no-browser" not in sys.argv:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")


if __name__ == "__main__":
    main()
