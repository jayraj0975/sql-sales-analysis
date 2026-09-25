"""Check the SQL, not just that it runs.

Each result is reconciled against an independent computation (raw SQL sums or pandas on the
raw tables), so a wrong join or a dropped row shows up as a failed total.
"""

import re

import pandas as pd
import pytest

from run_analysis import query_files


def scalar(conn, sql):
    return conn.execute(sql).fetchone()[0]


# ------------------------------------------------------------ hygiene
def test_every_query_is_a_single_read_only_statement():
    for path in query_files():
        sql = path.read_text()
        code = "\n".join(line for line in sql.splitlines() if not line.strip().startswith("--"))
        assert code.strip().endswith(";"), path.name
        assert code.count(";") == 1, f"{path.name}: more than one statement"
        assert not re.search(r"\b(insert|update|delete|drop|alter|create|attach|pragma)\b", code, re.I), path.name


def test_source_data_is_internally_consistent(conn):
    # invoice totals must equal the sum of their lines, or revenue would depend on which table you use
    assert scalar(conn, """SELECT COUNT(*) FROM Invoice i
        WHERE ABS(i.Total - (SELECT SUM(UnitPrice*Quantity) FROM InvoiceLine l WHERE l.InvoiceId=i.InvoiceId)) > 0.005""") == 0


# --------------------------------------------------------------- totals
def test_all_revenue_views_add_up_to_the_same_total(conn, results):
    total = scalar(conn, "SELECT ROUND(SUM(Total), 2) FROM Invoice")
    assert results["yearly_revenue"]["revenue"].sum() == pytest.approx(total, abs=0.01)
    assert results["monthly_revenue"]["revenue"].sum() == pytest.approx(total, abs=0.01)
    assert results["customer_pareto"]["revenue"].sum() == pytest.approx(total, abs=0.01)
    assert results["revenue_by_country"]["revenue"].sum() == pytest.approx(total, abs=0.01)
    assert results["revenue_by_genre"]["revenue"].sum() == pytest.approx(total, abs=0.01)   # no genre-less revenue dropped
    assert results["rep_performance"]["revenue"].sum() == pytest.approx(total, abs=0.01)


def test_invoice_counts_add_up(conn, results):
    n = scalar(conn, "SELECT COUNT(*) FROM Invoice")
    assert results["yearly_revenue"]["invoices"].sum() == n
    assert results["monthly_revenue"]["invoices"].sum() == n
    assert results["revenue_by_country"]["invoices"].sum() == n


# ------------------------------------------------- independent recomputation
def test_yearly_revenue_matches_pandas(conn, results):
    inv = pd.read_sql_query("SELECT InvoiceDate, Total FROM Invoice", conn)
    inv["year"] = inv["InvoiceDate"].str[:4]
    expected = inv.groupby("year")["Total"].sum().round(2)
    got = results["yearly_revenue"].set_index("year")["revenue"]
    pd.testing.assert_series_equal(got, expected, check_names=False, check_dtype=False)


def test_yoy_is_consistent_with_revenue(results):
    y = results["yearly_revenue"]
    assert pd.isna(y["yoy_pct"].iloc[0])
    for i in range(1, len(y)):
        want = 100 * (y["revenue"].iloc[i] - y["revenue"].iloc[i - 1]) / y["revenue"].iloc[i - 1]
        assert y["yoy_pct"].iloc[i] == pytest.approx(want, abs=0.06)


def test_moving_average_is_the_mean_of_the_last_three_months(results):
    m = results["monthly_revenue"]
    expected = m["revenue"].rolling(3, min_periods=1).mean().round(2)
    pd.testing.assert_series_equal(m["moving_avg_3m"], expected, check_names=False, check_dtype=False, atol=0.011)


def test_country_revenue_matches_pandas(conn, results):
    inv = pd.read_sql_query("SELECT BillingCountry, Total, CustomerId FROM Invoice", conn)
    g = inv.groupby("BillingCountry").agg(revenue=("Total", "sum"), customers=("CustomerId", "nunique"))
    got = results["revenue_by_country"].set_index("country")
    assert got["revenue"].round(2).equals(g["revenue"].round(2).reindex(got.index))
    assert got["customers"].equals(g["customers"].reindex(got.index))


# -------------------------------------------------------------- pareto
def test_pareto_is_a_valid_cumulative_distribution(results):
    p = results["customer_pareto"]
    assert list(p["customer_rank"]) == list(range(1, len(p) + 1))
    assert p["revenue"].is_monotonic_decreasing
    assert p["cumulative_pct"].is_monotonic_increasing
    assert p["cumulative_pct"].iloc[-1] == pytest.approx(100.0, abs=0.05)
    # each share is rounded to 2 decimals, so the sum can drift by at most 0.005 per row
    assert p["share_pct"].sum() == pytest.approx(100.0, abs=0.005 * len(p))


def test_every_customer_appears_exactly_once(conn, results):
    n = scalar(conn, "SELECT COUNT(DISTINCT CustomerId) FROM Invoice")
    assert len(results["customer_pareto"]) == n
    assert results["customer_pareto"]["customer"].is_unique
    assert len(results["rfm_segments"]) == n
    assert results["rfm_segments"]["CustomerId"].is_unique


# ------------------------------------------------------------------ RFM
def test_rfm_scores_are_valid_and_the_bands_are_usable(results):
    r = results["rfm_segments"]
    for col in ("r_score", "f_score", "m_score"):
        assert set(r[col]) <= {1, 2, 3}
    assert (r["total_score"] == r["r_score"] + r["f_score"] + r["m_score"]).all()
    assert set(r["segment"]) <= {"High value", "Middle", "Low value"}
    # Recency and Monetary vary across customers, so all three bands are used and none is empty.
    for col in ("r_score", "m_score"):
        assert set(r[col]) == {1, 2, 3}


def test_rfm_customers_with_equal_values_get_equal_scores(results):
    """The reason for PERCENT_RANK over NTILE: identical behaviour must never be scored differently
    just because of the customer id."""
    r = results["rfm_segments"]
    for measure, score in (("recency_days", "r_score"), ("frequency", "f_score"), ("monetary", "m_score")):
        assert (r.groupby(measure)[score].nunique() == 1).all(), measure


def test_rfm_frequency_is_nearly_constant_here_and_the_score_says_so(results):
    """Almost every customer has the same invoice count, so Frequency must not invent a spread."""
    r = results["rfm_segments"]
    modal = r["frequency"].mode().iloc[0]
    tied = r[r["frequency"] == modal]
    assert len(tied) >= 0.9 * len(r)                 # the data property this test relies on
    assert tied["f_score"].nunique() == 1            # ... and they all share one score
    ordered = r.sort_values("frequency")["f_score"].tolist()
    assert ordered == sorted(ordered)                # a higher count never scores lower


def test_rfm_direction_is_correct(results):
    r = results["rfm_segments"]
    top, bottom = r[r["m_score"] == 3], r[r["m_score"] == 1]
    assert top["monetary"].min() >= bottom["monetary"].max()           # higher score = more money
    fresh, stale = r[r["r_score"] == 3], r[r["r_score"] == 1]
    assert fresh["recency_days"].max() <= stale["recency_days"].min()  # higher score = more recent


# --------------------------------------------------------------- cohorts
def test_cohorts_partition_the_customers_and_retention_is_valid(conn, results):
    c = results["cohort_activity"]
    sizes = c.drop_duplicates("cohort_year").set_index("cohort_year")["customers_in_cohort"]
    assert sizes.sum() == scalar(conn, "SELECT COUNT(DISTINCT CustomerId) FROM Invoice")
    first_year = c[c["activity_year"] == c["cohort_year"]]
    assert (first_year["retention_pct"] == 100.0).all()      # everyone is active in their own cohort year
    assert c["retention_pct"].between(0, 100).all()
    assert (c["active_customers"] <= c["customers_in_cohort"]).all()


# --------------------------------------------------------------- catalogue
def test_catalogue_coverage_is_complete(conn, results):
    c = results["catalog_coverage"]
    assert c["tracks_in_catalogue"].sum() == scalar(conn, "SELECT COUNT(*) FROM Track")
    sold = scalar(conn, "SELECT COUNT(DISTINCT TrackId) FROM InvoiceLine")
    assert c["tracks_ever_sold"].sum() == sold
    assert c["never_sold_pct"].between(0, 100).all()


def test_reps_cover_every_customer(conn, results):
    assert results["rep_performance"]["customers"].sum() == scalar(conn, "SELECT COUNT(*) FROM Customer")


def test_top_artists_are_sorted_and_limited(results):
    a = results["top_artists"]
    assert len(a) == 15 and a["revenue"].is_monotonic_decreasing


# ------------------------------------------- the safety nets, exercised on purpose
def test_genre_query_keeps_revenue_from_tracks_with_no_genre(conn):
    """Every track in Chinook has a genre, so the LEFT JOIN in Q5 is never tested by the real data.
    Plant a genre-less sold track in a scratch copy and check that its revenue is still counted."""
    import sqlite3
    from pathlib import Path

    scratch = sqlite3.connect(":memory:")
    conn.backup(scratch)
    sold_track = scratch.execute("SELECT TrackId FROM InvoiceLine LIMIT 1").fetchone()[0]
    scratch.execute("UPDATE Track SET GenreId = NULL WHERE TrackId = ?", (sold_track,))
    total = scratch.execute("SELECT ROUND(SUM(UnitPrice*Quantity), 2) FROM InvoiceLine").fetchone()[0]

    sql = next(p for p in query_files() if p.stem.endswith("revenue_by_genre")).read_text()
    df = pd.read_sql_query(sql, scratch)
    assert "Unknown" in set(df["genre"])
    assert df["revenue"].sum() == pytest.approx(total, abs=0.01)
    scratch.close()


# ------------------------------------------------------------- the pinned database
def test_the_bundled_database_matches_its_pinned_checksum():
    import download_data
    assert download_data.verify(download_data.DEST) == download_data.EXPECTED_SHA256


def test_a_changed_database_is_refused(tmp_path):
    import pytest

    import download_data
    bad = tmp_path / "chinook.sqlite"
    bad.write_bytes(b"SQLite format 3\x00 not the real file")
    with pytest.raises(download_data.ChecksumMismatch):
        download_data.verify(bad)
