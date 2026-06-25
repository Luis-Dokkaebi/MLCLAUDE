"""
CR-02 regression (OWASP A03): report export must use bound parameters, not
f-string interpolation of GUI input. A classic injection payload in the date
field must NOT dump the whole table.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

import pandas as pd
import pytest
from src.storage.database_manager import DatabaseManager
from src.analysis.report_generator import DatabaseWorker

_DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


@pytest.fixture
def db(tmp_path):
    d = DatabaseManager(db_path=str(tmp_path / "db" / "t.db"))
    # Seed rows on two distinct dates by writing the timestamp directly.
    conn = d._get_connection()
    conn.execute("INSERT INTO tracking (track_id, timestamp, x, y, zone, inside_zone, employee_name) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?)", (1, "2026-03-15T10:00:00", 1, 2, "Z", 1, "Alice"))
    conn.execute("INSERT INTO tracking (track_id, timestamp, x, y, zone, inside_zone, employee_name) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?)", (2, "2026-09-20T10:00:00", 1, 2, "Z", 1, "Bob"))
    conn.commit()
    conn.close()
    return d


def test_parametrized_export_respects_range(db, tmp_path):
    worker = DatabaseWorker(db)
    out = str(tmp_path / "rep.xlsx")
    done = {}
    query = ("SELECT employee_name, date(timestamp) as fecha, zone, inside_zone "
             "FROM tracking WHERE date(timestamp) BETWEEN ? AND ?")
    worker.generate_excel_async(query, out,
                                on_success=lambda p, n: done.update(rows=n),
                                on_error=lambda e: done.update(err=e),
                                params=("2026-01-01", "2026-06-30"))
    for _ in range(50):
        if done:
            break
        time.sleep(0.05)
    assert done.get("rows") == 1, f"expected only the in-range row, got {done}"
    df = pd.read_excel(out)
    assert list(df["employee_name"]) == ["Alice"]


def test_injection_payload_is_inert_with_params(db, tmp_path):
    """Tautology payload that dumps the table under f-string must NOT under params.

    With end = "1900-01-01' OR '1'='1":
      - f-string  -> ... BETWEEN '2026-01-01' AND '1900-01-01' OR '1'='1'  (tautology -> 2 rows)
      - params    -> upper bound is the literal string, no date matches    (-> 0 rows)
    """
    payload_end = "1900-01-01' OR '1'='1"

    # Demonstrate the OLD vulnerability the fix removes (tautology dumps all rows).
    conn = db._get_connection()
    vulnerable = ("SELECT * FROM tracking WHERE date(timestamp) BETWEEN "
                  f"'2026-01-01' AND '{payload_end}'")
    vuln_rows = len(pd.read_sql_query(vulnerable, conn))
    conn.close()
    assert vuln_rows == 2, "sanity: f-string interpolation is a tautology (the bug)"

    # The fixed path: bound params -> payload is an inert literal -> 0 rows.
    worker = DatabaseWorker(db)
    out = str(tmp_path / "rep2.xlsx")
    done = {}
    query = ("SELECT employee_name, date(timestamp) as fecha, zone, inside_zone "
             "FROM tracking WHERE date(timestamp) BETWEEN ? AND ?")
    worker.generate_excel_async(query, out,
                                on_success=lambda p, n: done.update(rows=n),
                                on_error=lambda e: done.update(err=e),
                                params=("2026-01-01", payload_end))
    for _ in range(50):
        if done:
            break
        time.sleep(0.05)
    assert done.get("rows") == 0, f"injection leaked rows via params: {done}"


def test_date_validation_regex_rejects_injection():
    assert _DATE_RE.match("2026-12-31")
    assert not _DATE_RE.match("2026-12-31' OR '1'='1")
    assert not _DATE_RE.match("2026/12/31")
