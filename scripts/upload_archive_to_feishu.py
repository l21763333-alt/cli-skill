#!/usr/bin/env python3
"""Upload a local Markdown archive to Feishu Docs with lark-cli."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import a Markdown file as a Feishu Docx document.")
    parser.add_argument("file", help="Path to the local Markdown file.")
    parser.add_argument("--folder-token", help="Optional Feishu Drive folder token.")
    parser.add_argument("--name", help="Optional Feishu document title. Defaults to the file stem.")
    parser.add_argument("--as", dest="identity", choices=["user", "bot"], help="lark-cli identity to use.")
    return parser.parse_args()


def extract_url(output: str) -> str | None:
    for line in output.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            data = json.loads(line)
        except json.JSONDecodeError:
            continue

        for key in ("url", "document_url", "file_url"):
            value = data.get(key)
            if isinstance(value, str) and value.startswith("http"):
                return value

        result = data.get("result") or data.get("data")
        if isinstance(result, dict):
            for key in ("url", "document_url", "file_url"):
                value = result.get(key)
                if isinstance(value, str) and value.startswith("http"):
                    return value
    return None


def main() -> int:
    args = parse_args()
    md_path = Path(args.file).resolve()

    if not md_path.exists():
        print(f"file not found: {md_path}", file=sys.stderr)
        return 2
    if md_path.suffix.lower() not in {".md", ".markdown", ".mark"}:
        print(f"expected a Markdown file, got: {md_path}", file=sys.stderr)
        return 2

    cmd = [
        "lark-cli",
        "drive",
        "+import",
        "--file",
        str(md_path),
        "--type",
        "docx",
        "--name",
        args.name or md_path.stem,
    ]

    if args.folder_token:
        cmd.extend(["--folder-token", args.folder_token])
    if args.identity:
        cmd.extend(["--as", args.identity])

    result = subprocess.run(cmd, text=True, capture_output=True)

    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        return result.returncode

    url = extract_url(result.stdout)
    if url:
        print(f"Feishu URL: {url}")
    else:
        print("Upload finished. Check lark-cli output above for the document URL or async task result.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
