#!/usr/bin/env python3
"""File locking for ~/.command-center/ shared state (todos, missions)."""

from __future__ import annotations

import fcntl
import os
import subprocess
import sys
from contextlib import contextmanager
from pathlib import Path

CC_DIR = Path.home() / ".command-center"
LOCK_DIR = CC_DIR / "locks"


@contextmanager
def file_lock(name: str, timeout: float = 10.0):
    LOCK_DIR.mkdir(parents=True, exist_ok=True)
    lock_path = LOCK_DIR / f"{name}.lock"
    with lock_path.open("a+", encoding="utf-8") as fh:
        import time

        deadline = time.time() + timeout
        while True:
            try:
                fcntl.flock(fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except BlockingIOError:
                if time.time() >= deadline:
                    raise TimeoutError(f"Could not acquire lock {name} within {timeout}s")
                time.sleep(0.1)
        try:
            yield
        finally:
            fcntl.flock(fh.fileno(), fcntl.LOCK_UN)


def locked_write(lock_name: str, target: Path, content: str) -> None:
    target = target.expanduser()
    with file_lock(lock_name):
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(content, encoding="utf-8")
        os.replace(tmp, target)


def main() -> int:
    if len(sys.argv) < 2:
        print(f"Usage: {sys.argv[0]} write <lock> <path>   # read content from stdin", file=sys.stderr)
        print(f"       {sys.argv[0]} wrap <lock> -- <cmd...>", file=sys.stderr)
        return 1

    cmd = sys.argv[1]
    if cmd == "write":
        if len(sys.argv) != 4:
            print(f"Usage: {sys.argv[0]} write <lock> <path>", file=sys.stderr)
            return 1
        locked_write(sys.argv[2], Path(sys.argv[3]), sys.stdin.read())
        return 0

    if cmd == "wrap":
        if "--" not in sys.argv:
            print(f"Usage: {sys.argv[0]} wrap <lock> -- <cmd...>", file=sys.stderr)
            return 1
        idx = sys.argv.index("--")
        lock_name = sys.argv[2]
        child = sys.argv[idx + 1 :]
        if not child:
            print("wrap requires a command after --", file=sys.stderr)
            return 1
        with file_lock(lock_name):
            return subprocess.call(child)

    print(f"Unknown command: {cmd}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
