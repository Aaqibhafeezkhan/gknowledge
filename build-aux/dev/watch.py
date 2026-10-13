"""Run gknowledge and restart it whenever the source changes.

Usage: python3 build-aux/dev/watch.py [app arguments...]

Watches gknowledge/**/*.py, *.css and data/**/*.desktop-like resources using
plain mtime polling (no extra dependencies). On change the running app is
terminated and started again, so edits show up immediately.
"""
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WATCH = [ROOT / "gknowledge"]
EXTS = {".py", ".css", ".ui", ".xml"}
INTERVAL = 0.4
DEBOUNCE = 0.3


def snapshot() -> dict[str, float]:
    state = {}
    for base in WATCH:
        for p in base.rglob("*"):
            if p.suffix in EXTS and "__pycache__" not in p.parts:
                try:
                    state[str(p)] = p.stat().st_mtime
                except OSError:
                    pass
    return state


def start() -> subprocess.Popen:
    env = dict(os.environ, PYTHONPATH=str(ROOT), PYTHONUNBUFFERED="1")
    return subprocess.Popen([sys.executable, "-m", "gknowledge", *sys.argv[1:]],
                            cwd=ROOT, env=env)


def stop(proc: subprocess.Popen) -> None:
    if proc.poll() is None:
        proc.terminate()
        try:
            proc.wait(timeout=3)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()


def changed_files(old: dict, new: dict) -> list[str]:
    return sorted({k for k in old.keys() | new.keys() if old.get(k) != new.get(k)})


def main() -> int:
    sys.stdout.reconfigure(line_buffering=True)
    print("[watch] starting gknowledge; edit files under gknowledge/ to reload (Ctrl+C to quit)")
    state = snapshot()
    proc = start()
    try:
        while True:
            time.sleep(INTERVAL)
            new = snapshot()
            diff = changed_files(state, new)
            if diff:
                time.sleep(DEBOUNCE)          # let editors finish writing
                new = snapshot()
                names = ", ".join(Path(p).name for p in diff[:3])
                print(f"[watch] change detected ({names}); restarting…")
                stop(proc)
                state = new
                proc = start()
            elif proc.poll() is not None:
                code = proc.returncode
                if code == 0:
                    print("[watch] app closed; exiting")
                    return 0
                print(f"[watch] app crashed (exit {code}); waiting for a change to retry…")
                while snapshot() == state:
                    time.sleep(INTERVAL)
                state = snapshot()
                proc = start()
    except KeyboardInterrupt:
        stop(proc)
        return 0


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(KeyboardInterrupt))
    sys.exit(main())
