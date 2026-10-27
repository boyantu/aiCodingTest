"""数据访问层：SQLite 连接管理、建表、CRUD 与统计。

全项目唯一含 SQL 的文件；页面只依赖本模块暴露的函数与常量。
"""

import sqlite3
from contextlib import contextmanager
from pathlib import Path

# 数据库文件锚定本文件所在目录（而非 cwd），换目录启动不会另建空库
DB_PATH = Path(__file__).resolve().parent / "data" / "finance.db"

# 分类唯一真源：添加表单、筛选下拉、统计补齐三处共用
CATEGORIES = ("餐饮", "交通", "购物", "娱乐", "居住", "其他")

ALL_MONTHS = "全部月份"
ALL_CATEGORIES = "全部分类"

_SCHEMA = """
CREATE TABLE IF NOT EXISTS records (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    amount   INTEGER NOT NULL CHECK (amount > 0),  -- 单位：分
    category TEXT    NOT NULL,
    date     TEXT    NOT NULL,                     -- 'YYYY-MM-DD'
    note     TEXT    NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS idx_records_date ON records(date);
"""


@contextmanager
def get_conn():
    """每次操作新建短连接：天然线程安全，写后读永远是最新数据。

    注意 `with sqlite3.connect(...)` 只管理事务、不会关闭连接，
    所以这里必须手动 close()。
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """幂等建表，每个页面顶部调用一次即可。"""
    with get_conn() as conn:
        conn.executescript(_SCHEMA)


def add_record(amount_fen: int, category: str, date_str: str, note: str = "") -> int:
    """添加一条账目，返回新记录 ID。amount_fen 单位为分。"""
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO records (amount, category, date, note) VALUES (?, ?, ?, ?)",
            (amount_fen, category, date_str, note),
        )
        return cur.lastrowid


def delete_record(record_id: int) -> int:
    """按 ID 删除，返回实际删除行数（ID 不存在时为 0）。"""
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
        return cur.rowcount


def list_months() -> list:
    """所有有账目的月份，倒序，如 ['2026-10', '2026-09']。"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT substr(date, 1, 7) AS m FROM records ORDER BY m DESC"
        ).fetchall()
    return [r["m"] for r in rows]


def list_records(month=ALL_MONTHS, category=ALL_CATEGORIES) -> list:
    """按月份/分类筛选账目列表，按日期与 ID 倒序。"""
    sql = "SELECT id, amount, category, date, note FROM records"
    conditions, params = [], []
    if month != ALL_MONTHS:
        conditions.append("substr(date, 1, 7) = ?")
        params.append(month)
    if category != ALL_CATEGORIES:
        conditions.append("category = ?")
        params.append(category)
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY date DESC, id DESC"
    with get_conn() as conn:
        return conn.execute(sql, params).fetchall()


def stats_by_category(month=ALL_MONTHS) -> list:
    """按分类统计笔数与金额（分），补齐为固定 6 行，按金额降序。"""
    sql = "SELECT category, COUNT(*) AS cnt, SUM(amount) AS total_fen FROM records"
    params = []
    if month != ALL_MONTHS:
        sql += " WHERE substr(date, 1, 7) = ?"
        params.append(month)
    sql += " GROUP BY category"
    with get_conn() as conn:
        found = {r["category"]: r for r in conn.execute(sql, params).fetchall()}
    stats = [
        {
            "category": c,
            "count": found[c]["cnt"] if c in found else 0,
            "total_fen": found[c]["total_fen"] if c in found else 0,
        }
        for c in CATEGORIES
    ]
    stats.sort(key=lambda s: s["total_fen"], reverse=True)
    return stats


def month_summary(month: str) -> tuple:
    """某月总支出（分）与笔数，返回 (total_fen, count)；无记录时为 (0, 0)。"""
    with get_conn() as conn:
        row = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total_fen, COUNT(*) AS cnt "
            "FROM records WHERE substr(date, 1, 7) = ?",
            (month,),
        ).fetchone()
    return row["total_fen"], row["cnt"]
