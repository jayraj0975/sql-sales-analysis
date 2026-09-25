"""Provide the Chinook sample database (MIT licence, Luis Rocha) at data/chinook.sqlite.

The database is committed with the repository (about 1 MB, see NOTICE), so tests and CI need no network.
It is pinned by SHA-256: a changed or truncated file is refused. If the file is missing, it is downloaded
from the upstream project and verified against the same hash.
"""

import hashlib
import sys
from pathlib import Path
from urllib.request import urlopen

URL = ("https://github.com/lerocha/chinook-database/raw/master/"
       "ChinookDatabase/DataSources/Chinook_Sqlite.sqlite")
DEST = Path(__file__).resolve().parents[1] / "data" / "chinook.sqlite"
# Checked 2026-09-25. If upstream ever changes the file, review the change, then update this on purpose.
EXPECTED_SHA256 = "7651ba378ac2fcd0dfc3c66fb101f7a7eed3ba39a612ec642b96e20702061f15"


class ChecksumMismatch(RuntimeError):
    pass


def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify(path: Path = DEST) -> str:
    digest = sha256_of(path.read_bytes())
    if digest != EXPECTED_SHA256:
        raise ChecksumMismatch(
            f"{path} has SHA-256 {digest}, expected {EXPECTED_SHA256}. Restore it from git, or "
            "update EXPECTED_SHA256 after reviewing the change."
        )
    return digest


def download() -> Path:
    if DEST.exists():
        verify(DEST)
        print(f"present and verified: {DEST}")
        return DEST
    DEST.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {URL}")
    data = urlopen(URL, timeout=60).read()
    if not data.startswith(b"SQLite format 3"):
        raise RuntimeError("download is not a SQLite file")
    if sha256_of(data) != EXPECTED_SHA256:
        raise ChecksumMismatch("the downloaded file does not match the pinned SHA-256")
    DEST.write_bytes(data)
    print(f"saved {len(data) / 1024:.0f} KB to {DEST}")
    return DEST


if __name__ == "__main__":
    try:
        download()
    except Exception as exc:  # noqa: BLE001 - command-line entry point: report and exit non-zero
        print(f"error: {exc}", file=sys.stderr)
        sys.exit(1)
