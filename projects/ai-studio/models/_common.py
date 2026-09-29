"""Shared helper for the per-model scripts in this folder.

Each model file only sets MODEL + settings and calls run(). Usage:
    python <model-file>.py "your question"
    python <model-file>.py "describe this image" --image photo.jpg
    python <model-file>.py            (interactive chat)
"""

import base64
import mimetypes
import os
import sys
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    sys.exit("openai package nahi mila. Pehle chalao:  pip install -r requirements.txt")

ROOT = Path(__file__).resolve().parent.parent

if os.name == "nt":
    os.system("")  # enables ANSI colours in the Windows terminal


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def image_part(path):
    p = Path(path)
    if not p.exists():
        sys.exit(f"Image nahi mili: {p}")
    mime = mimetypes.guess_type(p.name)[0] or "image/jpeg"
    data = base64.b64encode(p.read_bytes()).decode()
    return {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{data}"}}


def user_message(text, image=None):
    if not image:
        return {"role": "user", "content": text}
    return {"role": "user", "content": [{"type": "text", "text": text}, image_part(image)]}


def ask(client, model, messages, settings):
    """Stream the answer to the terminal and return the full text."""
    stream = client.chat.completions.create(model=model, messages=messages, stream=True, **settings)
    answer, thinking = [], False
    for chunk in stream:
        if not chunk.choices:
            continue
        delta = chunk.choices[0].delta
        reasoning = getattr(delta, "reasoning_content", None) or getattr(delta, "reasoning", None)
        if reasoning:
            if not thinking:
                print("\033[2m[thinking] ", end="")
                thinking = True
            print(reasoning, end="", flush=True)
        if delta.content:
            if thinking:
                print("\033[0m\n")
                thinking = False
            answer.append(delta.content)
            print(delta.content, end="", flush=True)
    print("\033[0m" if thinking else "")
    return "".join(answer)


def run(model, settings, system=None):
    load_env()
    key = os.environ.get("NVIDIA_API_KEY", "").strip()
    if not key:
        sys.exit("NVIDIA_API_KEY nahi mili. ai-studio/.env file mein key daalo.")
    client = OpenAI(base_url=os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"), api_key=key)

    args = sys.argv[1:]
    image = None
    if "--image" in args:
        i = args.index("--image")
        if i + 1 >= len(args):
            sys.exit("--image ke baad image ka path do")
        image = args[i + 1]
        del args[i:i + 2]

    messages = [{"role": "system", "content": system}] if system else []

    if args:  # one question from the command line
        messages.append(user_message(" ".join(args), image))
        ask(client, model, messages, settings)
        return

    print(f"Model: {model}   (exit likh ke band karo, 'image <path> <sawal>' se image bhejo)\n")
    while True:
        try:
            text = input("Aap: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not text:
            continue
        if text.lower() in ("exit", "quit"):
            break
        img = None
        if text.startswith("image "):
            parts = text.split(maxsplit=2)
            if len(parts) < 3:
                print("Aise likho: image photo.jpg is photo mein kya hai?")
                continue
            img, text = parts[1], parts[2]
        messages.append(user_message(text, img))
        print("AI: ", end="")
        try:
            messages.append({"role": "assistant", "content": ask(client, model, messages, settings)})
        except Exception as e:  # show API errors without crashing the chat
            messages.pop()
            print(f"\nError: {e}")
