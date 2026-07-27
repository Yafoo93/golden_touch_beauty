"""Temporarily keep the development Render backend warm.

Run from the repository root:
    python scripts/render_keep_awake.py

Stop with Ctrl+C. This only works while this process and its internet
connection remain active.
"""

from __future__ import annotations

import argparse
import json
import time
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_URL = "https://golden-touch-beauty.onrender.com/api/v1/ping/"
DEFAULT_INTERVAL_SECONDS = 10 * 60


def ping(url: str, timeout: int) -> None:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "GoldenTouchDevelopmentMonitor/1.0",
        },
    )
    with urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
        if response.status != 200 or payload.get("status") != "ok":
            raise RuntimeError(
                f"Unexpected ping response: HTTP {response.status} {payload}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Call the Golden Touch development ping endpoint periodically."
    )
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Seconds between calls (default: 600).",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Request timeout in seconds (default: 60).",
    )
    args = parser.parse_args()

    if args.interval < 60:
        parser.error("--interval must be at least 60 seconds")

    print(f"Calling {args.url} every {args.interval} seconds. Press Ctrl+C to stop.")
    try:
        while True:
            timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
            try:
                ping(args.url, args.timeout)
                print(f"[{timestamp}] Ping succeeded.")
            except (HTTPError, URLError, TimeoutError, RuntimeError, ValueError) as error:
                print(f"[{timestamp}] Ping failed: {error}")
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nDevelopment monitor stopped.")


if __name__ == "__main__":
    main()
