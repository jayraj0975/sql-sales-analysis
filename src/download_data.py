"""Fetch the Chinook sample database (MIT licence, Luis Rocha) into data/."""

from pathlib import Path
from urllib.request import urlopen

URL = ("https://github.com/lerocha/chinook-database/raw/master/"
       "ChinookDatabase/DataSources/Chinook_Sqlite.sqlite")
DEST = Path(__file__).resolve().parents[1] / "data" / "chinook.sqlite"


def download() -> Path:
    if DEST.exists():
        print(f"already present: {DEST}")
        return DEST
    DEST.parent.mkdir(parents=True, exist_ok=True)
    print(f"downloading {URL}")
    data = urlopen(URL, timeout=60).read()
    if not data.startswith(b"SQLite format 3"):
        raise RuntimeError("download is not a SQLite file")
    DEST.write_bytes(data)
    print(f"saved {len(data) / 1024:.0f} KB to {DEST}")
    return DEST


if __name__ == "__main__":
    download()
