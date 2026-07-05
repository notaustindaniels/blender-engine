#!/usr/bin/env python3
"""Append-only progress-feed manager for the Stage-1 follow-along page.

The page (index.html) fetches feed.json live and renders entries newest-first,
so this tool only ever appends. Timestamps are real (local tz). Stdlib only.

Usage:
  progress.py add --title "..." --tag milestone --body "<p>html</p>" \
      [--code "raw text block" [--code-file path]] \
      [--media "media/foo.png|caption" ...]

Tags: milestone | evidence | info | question | fail | review
"""
import argparse, json, os, sys, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
FEED = os.path.join(HERE, "feed.json")


def load():
    if not os.path.exists(FEED):
        return []
    try:
        with open(FEED) as f:
            return json.load(f)
    except Exception:
        return []


def save(entries):
    tmp = FEED + ".tmp"
    with open(tmp, "w") as f:
        json.dump(entries, f, indent=2, ensure_ascii=False)
    os.replace(tmp, FEED)


def cmd_add(args):
    entries = load()
    seq = (max((e.get("seq", 0) for e in entries), default=0)) + 1
    code = args.code
    if args.code_file:
        with open(args.code_file) as f:
            code = f.read()
    if code and len(code) > 6000:
        code = code[:6000] + "\n… (truncated)"
    media = []
    for m in args.media or []:
        src, _, cap = m.partition("|")
        media.append({"src": src.strip(), "caption": cap.strip()})
    entry = {
        "seq": seq,
        "ts": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "title": args.title,
        "tag": args.tag,
        "status": args.status,
        "body": args.body or "",
        "code": code or "",
        "media": media,
    }
    entries.append(entry)
    save(entries)
    print(f"added entry #{seq}: [{args.tag}] {args.title}")


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add")
    a.add_argument("--title", required=True)
    a.add_argument("--tag", default="info",
                   choices=["milestone", "evidence", "info", "question", "fail", "review"])
    a.add_argument("--status", default="")
    a.add_argument("--body", default="")
    a.add_argument("--code", default="")
    a.add_argument("--code-file", default="")
    a.add_argument("--media", action="append")
    a.set_defaults(func=cmd_add)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
