#!/usr/bin/env python3
"""Profile bot: refreshes the auto-generated sections of README.md.

Each section lives between <!-- START:NAME --> and <!-- END:NAME --> markers.
Only the Python standard library is used, so no install step is needed.
"""

import datetime as dt
import json
import os
import re
import sys
import urllib.request
from pathlib import Path

USER = os.environ.get("GITHUB_USER") or os.environ.get("GITHUB_REPOSITORY_OWNER") or "PARDEEP6801"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
README = Path(__file__).resolve().parent.parent / "README.md"
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))

QUOTES = [
    ("Talk is cheap. Show me the code.", "Linus Torvalds"),
    ("First, solve the problem. Then, write the code.", "John Johnson"),
    ("Simplicity is the soul of efficiency.", "Austin Freeman"),
    ("Make it work, make it right, make it fast.", "Kent Beck"),
    ("Code is like humor. When you have to explain it, it's bad.", "Cory House"),
    ("The best way to predict the future is to invent it.", "Alan Kay"),
    ("Programs must be written for people to read.", "Harold Abelson"),
    ("Automate the boring stuff.", "Al Sweigart"),
    ("Any fool can write code that a computer can understand.", "Martin Fowler"),
    ("Done is better than perfect.", "Sheryl Sandberg"),
]


def api(path):
    req = urllib.request.Request(f"https://api.github.com{path}")
    req.add_header("Accept", "application/vnd.github+json")
    req.add_header("User-Agent", f"{USER}-profile-bot")
    if TOKEN:
        req.add_header("Authorization", f"Bearer {TOKEN}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def stats_section(profile, repos):
    own = [r for r in repos if not r["fork"]]
    stars = sum(r["stargazers_count"] for r in own)
    forks = sum(r["forks_count"] for r in own)
    return "\n".join([
        "| 📦 Public repos | ⭐ Stars earned | 🍴 Forks | 👥 Followers |",
        "|:---:|:---:|:---:|:---:|",
        f"| {profile['public_repos']} | {stars} | {forks} | {profile['followers']} |",
    ])


def repos_section(repos, limit=5):
    rows = [
        r for r in repos
        if not r["fork"] and r["name"].lower() != USER.lower()
    ][:limit]
    if not rows:
        return "_No public projects yet — coming soon!_ 🚀"
    lines = []
    for r in rows:
        desc = (r["description"] or "No description").replace("|", "\\|")
        lang = f" · `{r['language']}`" if r["language"] else ""
        lines.append(f"- [**{r['name']}**]({r['html_url']}) — {desc}{lang} · ⭐ {r['stargazers_count']}")
    return "\n".join(lines)


def describe_event(e):
    repo = e["repo"]["name"]
    link = f"[{repo}](https://github.com/{repo})"
    t, p = e["type"], e.get("payload", {})
    if t == "PushEvent":
        n = p.get("size") or len(p.get("commits", [])) or 1
        return f"⬆️ Pushed {n} commit{'s' if n != 1 else ''} to {link}"
    if t == "CreateEvent":
        return f"✨ Created {p.get('ref_type', 'repository')} in {link}"
    if t == "WatchEvent":
        return f"⭐ Starred {link}"
    if t == "ForkEvent":
        return f"🍴 Forked {link}"
    if t == "IssuesEvent":
        return f"❗ {p.get('action', 'updated').capitalize()} issue #{p['issue']['number']} in {link}"
    if t == "PullRequestEvent":
        return f"🔀 {p.get('action', 'updated').capitalize()} PR #{p['pull_request']['number']} in {link}"
    if t == "IssueCommentEvent":
        return f"💬 Commented on #{p['issue']['number']} in {link}"
    if t == "ReleaseEvent":
        return f"🏷️ Released {p['release']['tag_name']} in {link}"
    return None


def activity_section(events, limit=5):
    lines = []
    for e in events:
        text = describe_event(e)
        if text:
            lines.append(f"{len(lines) + 1}. {text}")
        if len(lines) == limit:
            break
    return "\n".join(lines) or "_No recent public activity._"


def quote_section(today):
    text, author = QUOTES[today.toordinal() % len(QUOTES)]
    return f"> 💡 _\"{text}\"_ — **{author}**"


def replace_section(content, name, body):
    pattern = re.compile(rf"(<!-- START:{name} -->)(.*?)(<!-- END:{name} -->)", re.S)
    if not pattern.search(content):
        print(f"warning: markers for {name} not found", file=sys.stderr)
        return content
    return pattern.sub(lambda m: f"{m.group(1)}\n{body}\n{m.group(3)}", content)


def main():
    now = dt.datetime.now(IST)
    profile = api(f"/users/{USER}")
    repos = api(f"/users/{USER}/repos?sort=pushed&per_page=100")
    events = api(f"/users/{USER}/events/public?per_page=50")

    content = README.read_text(encoding="utf-8")
    sections = {
        "QUOTE": quote_section(now.date()),
        "STATS": stats_section(profile, repos),
        "REPOS": repos_section(repos),
        "ACTIVITY": activity_section(events),
        "UPDATED": f"<sub>🤖 Auto-updated by profile bot on {now:%d %b %Y, %I:%M %p} IST</sub>",
    }
    for name, body in sections.items():
        content = replace_section(content, name, body)
    README.write_text(content, encoding="utf-8")
    print(f"README updated for {USER}")


if __name__ == "__main__":
    main()
