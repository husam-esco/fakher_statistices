import sqlite3
import os
from datetime import date, datetime
from pathlib import Path

DB_DIR = Path(__file__).parent / "data_store"
DB_PATH = DB_DIR / "dashboard.db"


def init_db():
    DB_DIR.mkdir(exist_ok=True)
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS production_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date DATE    NOT NULL,
            product_name TEXT   NOT NULL,
            amount      REAL   DEFAULT 0,
            transfer    REAL   DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_prod_date ON production_records(report_date);

        CREATE TABLE IF NOT EXISTS sells_records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            report_date DATE    NOT NULL,
            product_name TEXT   NOT NULL,
            amount      REAL   DEFAULT 0,
            main_name   TEXT   DEFAULT '',
            transfer    REAL   DEFAULT 0,
            created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_sells_date ON sells_records(report_date);

        CREATE TABLE IF NOT EXISTS upload_log (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            file_name   TEXT    NOT NULL,
            report_date DATE    NOT NULL UNIQUE,
            records_prod INTEGER DEFAULT 0,
            records_sells INTEGER DEFAULT 0,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()


def get_conn():
    return sqlite3.connect(str(DB_PATH))


def date_exists(report_date: date) -> bool:
    conn = get_conn()
    cur = conn.execute("SELECT 1 FROM upload_log WHERE report_date = ?", (report_date.isoformat(),))
    exists = cur.fetchone() is not None
    conn.close()
    return exists


def insert_production(report_date: date, records: list[dict]):
    conn = get_conn()
    conn.executemany(
        "INSERT INTO production_records (report_date, product_name, amount, transfer) VALUES (?, ?, ?, ?)",
        [(report_date.isoformat(), r["product_name"], r["amount"], r["transfer"]) for r in records]
    )
    conn.commit()
    conn.close()


def insert_sells(report_date: date, records: list[dict]):
    conn = get_conn()
    conn.executemany(
        "INSERT INTO sells_records (report_date, product_name, amount, main_name, transfer) VALUES (?, ?, ?, ?, ?)",
        [(report_date.isoformat(), r["product_name"], r["amount"], r.get("main_name", ""), r["transfer"]) for r in records]
    )
    conn.commit()
    conn.close()


def log_upload(file_name: str, report_date: date, prod_count: int, sells_count: int):
    conn = get_conn()
    conn.execute(
        "INSERT INTO upload_log (file_name, report_date, records_prod, records_sells) VALUES (?, ?, ?, ?)",
        (file_name, report_date.isoformat(), prod_count, sells_count)
    )
    conn.commit()
    conn.close()


def get_date_range() -> tuple:
    conn = get_conn()
    cur = conn.execute("SELECT MIN(report_date), MAX(report_date) FROM upload_log")
    row = cur.fetchone()
    conn.close()
    return (datetime.strptime(row[0], "%Y-%m-%d").date() if row[0] else None,
            datetime.strptime(row[1], "%Y-%m-%d").date() if row[1] else None)


def fetch_cumulative_data(section: str, start_date: date = None, end_date: date = None) -> list[dict]:
    conn = get_conn()
    if section == "production":
        query = "SELECT report_date, product_name, amount, transfer FROM production_records"
        params = []
    else:
        query = "SELECT report_date, product_name, amount, main_name, transfer FROM sells_records"
        params = []

    conditions = []
    if start_date:
        conditions.append("report_date >= ?")
        params.append(start_date.isoformat())
    if end_date:
        conditions.append("report_date <= ?")
        params.append(end_date.isoformat())
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY report_date"

    conn.row_factory = sqlite3.Row
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_uploaded_dates() -> list[date]:
    conn = get_conn()
    rows = conn.execute("SELECT report_date FROM upload_log ORDER BY report_date").fetchall()
    conn.close()
    return [datetime.strptime(r[0], "%Y-%m-%d").date() for r in rows]


def get_upload_count() -> int:
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM upload_log").fetchone()[0]
    conn.close()
    return count


def get_upload_log() -> list[dict]:
    conn = get_conn()
    conn.row_factory = sqlite3.Row
    rows = conn.execute("""
        SELECT file_name, report_date, uploaded_at, records_prod, records_sells
        FROM upload_log
        ORDER BY report_date DESC, uploaded_at DESC
    """).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_total_production_amount() -> float:
    conn = get_conn()
    val = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM production_records").fetchone()[0]
    conn.close()
    return val


def get_total_sells_amount() -> float:
    conn = get_conn()
    val = conn.execute("SELECT COALESCE(SUM(amount), 0) FROM sells_records").fetchone()[0]
    conn.close()
    return val


def delete_date(date_str: str):
    conn = get_conn()
    conn.execute("DELETE FROM production_records WHERE report_date = ?", (date_str,))
    conn.execute("DELETE FROM sells_records WHERE report_date = ?", (date_str,))
    conn.execute("DELETE FROM upload_log WHERE report_date = ?", (date_str,))
    conn.commit()
    conn.close()


def delete_all():
    conn = get_conn()
    conn.execute("DELETE FROM production_records")
    conn.execute("DELETE FROM sells_records")
    conn.execute("DELETE FROM upload_log")
    conn.commit()
    conn.close()
