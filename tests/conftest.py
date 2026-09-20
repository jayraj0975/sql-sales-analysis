import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


@pytest.fixture(scope="session")
def conn():
    from download_data import download
    from run_analysis import connect

    download()
    c = connect()
    yield c
    c.close()


@pytest.fixture(scope="session")
def results(conn):
    from run_analysis import run_queries

    return run_queries(conn)
