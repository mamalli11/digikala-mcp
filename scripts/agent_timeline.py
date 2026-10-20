"""Print what the subagents of a Claude Code session did: task, every tool call, final answer.

    python scripts/agent_timeline.py              # latest session of this project
    python scripts/agent_timeline.py --full       # do not cut the final answers
    python scripts/agent_timeline.py <subagents-dir>

Claude Code saves each subagent as ~/.claude/projects/<project>/<session>/subagents/agent-<id>.jsonl.
"""

import glob
import json
import os
import re
import sys
from datetime import datetime


def latest_subagents_dir() -> str:
    key = re.sub(r"[^A-Za-z0-9]", "-", os.getcwd()).lower()
    root = os.path.join(os.path.expanduser("~"), ".claude", "projects")
    for name in os.listdir(root):
        if name.lower() == key:
            dirs = glob.glob(os.path.join(root, name, "*", "subagents"))
            if dirs:
                return max(dirs, key=lambda d: max(os.path.getmtime(f) for f in glob.glob(os.path.join(d, "*"))))
    sys.exit("No subagent transcripts found for this folder. Pass the subagents directory explicitly.")


def clip(text, n):
    text = " ".join(str(text).split())
    return text if n is None or len(text) <= n else text[:n] + "..."


def local_time(stamp):
    try:
        return datetime.fromisoformat(stamp.replace("Z", "+00:00")).astimezone().strftime("%H:%M:%S")
    except ValueError:
        return "?"


def show(path, full):
    rows = [json.loads(line) for line in open(path, encoding="utf-8") if line.strip()]
    print("=" * 100)
    print(f"{os.path.basename(path)} | started {local_time(rows[0].get('timestamp', ''))} | {len(rows)} messages")
    calls, task, last = 0, None, ""
    for r in rows:
        message = r.get("message") or {}
        content = message.get("content")
        if task is None and r.get("type") == "user" and isinstance(content, str):
            task = content
            print("  TASK:", clip(task, 300))
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use":
                calls += 1
                args = json.dumps(block.get("input"), ensure_ascii=False)
                print(f"  [{calls:02d}] {block.get('name', '').replace('mcp__digikala__', '')}  {clip(args, 130)}")
            elif block.get("type") == "text" and message.get("role") == "assistant":
                last = block.get("text", "")
    print("  FINAL:", clip(last, None if full else 600))


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--full"]
    folder = args[0] if args else latest_subagents_dir()
    for f in sorted(glob.glob(os.path.join(folder, "agent-*.jsonl")), key=os.path.getmtime):
        show(f, "--full" in sys.argv)
