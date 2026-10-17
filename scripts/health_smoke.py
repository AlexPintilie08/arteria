"""Start the API as a real local process and verify its HTTP health response."""

from __future__ import annotations

import json
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "backend.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        cwd=ROOT,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    url = f"http://127.0.0.1:{port}/health"
    try:
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise RuntimeError(f"uvicorn exited early with code {process.returncode}")
            try:
                with urllib.request.urlopen(url, timeout=1) as response:
                    payload = json.loads(response.read())
                    if response.status != 200 or payload.get("status") != "ok":
                        raise RuntimeError(f"Unexpected /health response: {payload!r}")
                    print(f"Backend HTTP smoke test passed: {url}")
                    return 0
            except (urllib.error.URLError, TimeoutError):
                time.sleep(0.2)
        raise TimeoutError(f"Timed out waiting for {url}")
    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)


if __name__ == "__main__":
    raise SystemExit(main())
