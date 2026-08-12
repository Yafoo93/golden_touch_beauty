"""Fail CI if Git tracks a file likely to contain secrets or customer data."""

from __future__ import annotations

import fnmatch
import subprocess
from pathlib import PurePosixPath


FORBIDDEN_NAMES = {
    ".env",
    ".pgpass",
    "credentials.json",
    "id_ed25519",
    "id_rsa",
}
FORBIDDEN_SUFFIXES = {
    ".bak",
    ".db",
    ".dump",
    ".key",
    ".p12",
    ".pem",
    ".pfx",
    ".sql",
    ".sqlite",
    ".sqlite3",
}
FORBIDDEN_DIRECTORIES = {"backups", "exports", "media", "uploads"}


def is_forbidden(path_text: str) -> bool:
    path = PurePosixPath(path_text)
    lowered_parts = tuple(part.lower() for part in path.parts)
    name = path.name.lower()

    if name.endswith(".env.example") or name == ".env.example":
        return False
    if name in FORBIDDEN_NAMES or name.startswith(".env."):
        return True
    if path.suffix.lower() in FORBIDDEN_SUFFIXES or name.endswith(".sql.gz"):
        return True
    if any(part in FORBIDDEN_DIRECTORIES for part in lowered_parts[:-1]):
        return True
    return fnmatch.fnmatch(name, "service-account*.json")


def main() -> int:
    result = subprocess.run(
        ["git", "ls-files", "-z"],
        check=True,
        capture_output=True,
    )
    tracked = result.stdout.decode("utf-8").split("\0")
    forbidden = sorted(path for path in tracked if path and is_forbidden(path))

    if forbidden:
        print("Refusing tracked files that may contain secrets or customer data:")
        for path in forbidden:
            print(f"- {path}")
        return 1

    print("No forbidden secret/customer-data file types are tracked.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
