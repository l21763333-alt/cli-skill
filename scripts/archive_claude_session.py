#!/usr/bin/env python3
"""Archive a Claude Code transcript to Markdown and upload it to Feishu Docs."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


SECRET_PATTERNS = [
    re.compile(r"(?i)(api[_-]?key|access[_-]?token|refresh[_-]?token|secret|password)\s*[:=]\s*[^\s`]+"),
    re.compile(r"(?i)authorization:\s*bearer\s+[^\s`]+"),
    re.compile(r"(?i)cookie:\s*[^\n]+"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----", re.DOTALL),
]


def redact(text: str) -> str:
    redacted = text
    for pattern in SECRET_PATTERNS:
        redacted = pattern.sub("[REDACTED]", redacted)
    return redacted


def message_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        parts: list[str] = []
        for item in value:
            if isinstance(item, dict):
                if "text" in item:
                    parts.append(str(item["text"]))
                elif "content" in item:
                    parts.append(message_text(item["content"]))
                else:
                    parts.append(json.dumps(item, ensure_ascii=False))
            else:
                parts.append(str(item))
        return "\n".join(parts)
    if isinstance(value, dict):
        if "content" in value:
            return message_text(value["content"])
        return json.dumps(value, ensure_ascii=False, indent=2)
    return str(value)


def read_transcript(path: Path) -> str:
    sections: list[str] = []
    if not path.exists():
        return f"> Transcript file not found: `{path}`\n"

    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue

        role = item.get("role") or item.get("type") or "event"
        message = item.get("message", item.get("content", item))
        text = redact(message_text(message)).strip()
        if not text:
            continue
        sections.append(f"## {role}\n\n{text}")

    return "\n\n".join(sections) if sections else "> No transcript messages were extracted.\n"


def load_payload() -> dict[str, Any]:
    if sys.stdin.isatty():
        return {}
    raw = sys.stdin.read().strip()
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw_stdin": raw}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive a Claude Code transcript and upload it to Feishu.")
    parser.add_argument("--transcript-path", help="Path to Claude Code transcript JSONL. Overrides stdin payload.")
    parser.add_argument("--folder-token", help="Optional Feishu Drive folder token.")
    parser.add_argument("--no-upload", action="store_true", help="Only create the local Markdown archive.")
    parser.add_argument("--as", dest="identity", choices=["user", "bot"], help="lark-cli identity to use.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = load_payload()
    transcript_value = args.transcript_path or payload.get("transcript_path")

    if not transcript_value:
        print("missing transcript_path. Pass --transcript-path or run as a Claude Code Stop Hook.", file=sys.stderr)
        return 2

    transcript_path = Path(transcript_value).expanduser().resolve()
    now = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    out_dir = Path("archives")
    out_dir.mkdir(parents=True, exist_ok=True)
    md_path = out_dir / f"claude-session-{now}.md"

    body = read_transcript(transcript_path)
    content = f"""# Claude Code Session Archive

- Time: {now}
- Session ID: {payload.get("session_id", "")}
- CWD: {payload.get("cwd", "")}
- Transcript: `{transcript_path}`

{body}
"""
    md_path.write_text(content, encoding="utf-8")
    print(f"Archive saved: {md_path}")

    if args.no_upload:
        return 0

    upload_cmd = [sys.executable, "scripts/upload_archive_to_feishu.py", str(md_path)]
    if args.folder_token:
        upload_cmd.extend(["--folder-token", args.folder_token])
    if args.identity:
        upload_cmd.extend(["--as", args.identity])

    result = subprocess.run(upload_cmd, text=True)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
