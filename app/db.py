from __future__ import annotations

import aiosqlite
from typing import Any, Dict, List, Optional, Tuple

_DB_PATH: str | None = None


def set_db_path(path: str) -> None:
    global _DB_PATH
    _DB_PATH = path


async def _get_db() -> aiosqlite.Connection:
    if not _DB_PATH:
        raise RuntimeError("DB path is not configured. Call set_db_path() first.")
    db = await aiosqlite.connect(_DB_PATH)
    await db.execute("PRAGMA foreign_keys = ON;")
    db.row_factory = aiosqlite.Row
    return db


async def init_db() -> None:
    async with await _get_db() as db:
        # Users table: passengers and potentially admins; drivers are kept in separate table
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE NOT NULL,
                full_name TEXT,
                phone TEXT
            );
            """
        )
        # Drivers table: registered by admin
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS drivers (
                tg_id INTEGER PRIMARY KEY,
                full_name TEXT,
                added_at DATETIME DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        # Orders table
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                passenger_tg_id INTEGER NOT NULL,
                pickup TEXT NOT NULL,
                destination TEXT NOT NULL,
                status TEXT NOT NULL,
                driver_tg_id INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(passenger_tg_id) REFERENCES users(tg_id) ON DELETE CASCADE
            );
            """
        )
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);")
        await db.execute("CREATE INDEX IF NOT EXISTS idx_orders_driver ON orders(driver_tg_id);")
        await db.commit()


# Users
async def upsert_user(tg_id: int, full_name: str) -> None:
    async with await _get_db() as db:
        await db.execute(
            """
            INSERT INTO users (tg_id, full_name)
            VALUES (?, ?)
            ON CONFLICT(tg_id) DO UPDATE SET full_name=excluded.full_name
            """,
            (tg_id, full_name),
        )
        await db.commit()


async def get_user(tg_id: int) -> Optional[Dict[str, Any]]:
    async with await _get_db() as db:
        async with db.execute("SELECT * FROM users WHERE tg_id=?", (tg_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def set_user_phone(tg_id: int, phone: str) -> None:
    async with await _get_db() as db:
        await db.execute("UPDATE users SET phone=? WHERE tg_id=?", (phone, tg_id))
        await db.commit()


# Drivers
async def add_driver(tg_id: int, full_name: str) -> bool:
    async with await _get_db() as db:
        try:
            await db.execute(
                "INSERT INTO drivers (tg_id, full_name) VALUES (?, ?)",
                (tg_id, full_name),
            )
            await db.commit()
            return True
        except Exception:
            return False


async def remove_driver(tg_id: int) -> int:
    async with await _get_db() as db:
        cur = await db.execute("DELETE FROM drivers WHERE tg_id=?", (tg_id,))
        await db.commit()
        return cur.rowcount


async def is_driver(tg_id: int) -> bool:
    async with await _get_db() as db:
        async with db.execute("SELECT 1 FROM drivers WHERE tg_id=?", (tg_id,)) as cur:
            return (await cur.fetchone()) is not None


async def list_drivers() -> List[Dict[str, Any]]:
    async with await _get_db() as db:
        async with db.execute("SELECT tg_id, full_name, added_at FROM drivers ORDER BY added_at DESC") as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


# Orders
async def create_order(passenger_tg_id: int, pickup: str, destination: str) -> int:
    async with await _get_db() as db:
        cur = await db.execute(
            "INSERT INTO orders (passenger_tg_id, pickup, destination, status) VALUES (?, ?, ?, 'new')",
            (passenger_tg_id, pickup, destination),
        )
        await db.commit()
        return cur.lastrowid


async def get_order(order_id: int) -> Optional[Dict[str, Any]]:
    async with await _get_db() as db:
        async with db.execute("SELECT * FROM orders WHERE id=?", (order_id,)) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def list_new_orders(limit: int = 10) -> List[Dict[str, Any]]:
    async with await _get_db() as db:
        async with db.execute(
            "SELECT * FROM orders WHERE status='new' ORDER BY created_at ASC LIMIT ?",
            (limit,),
        ) as cur:
            rows = await cur.fetchall()
            return [dict(r) for r in rows]


async def driver_accept_order(order_id: int, driver_tg_id: int) -> bool:
    async with await _get_db() as db:
        cur = await db.execute(
            """
            UPDATE orders
            SET status='accepted', driver_tg_id=?, updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND status='new'
            """,
            (driver_tg_id, order_id),
        )
        await db.commit()
        return cur.rowcount == 1


async def driver_mark_arrived(order_id: int, driver_tg_id: int) -> bool:
    async with await _get_db() as db:
        cur = await db.execute(
            """
            UPDATE orders
            SET status='arrived', updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND driver_tg_id=? AND status='accepted'
            """,
            (order_id, driver_tg_id),
        )
        await db.commit()
        return cur.rowcount == 1


async def driver_complete_order(order_id: int, driver_tg_id: int) -> bool:
    async with await _get_db() as db:
        cur = await db.execute(
            """
            UPDATE orders
            SET status='completed', updated_at=CURRENT_TIMESTAMP
            WHERE id=? AND driver_tg_id=? AND status IN ('accepted', 'arrived')
            """,
            (order_id, driver_tg_id),
        )
        await db.commit()
        return cur.rowcount == 1


async def get_driver_active_order(driver_tg_id: int) -> Optional[Dict[str, Any]]:
    async with await _get_db() as db:
        async with db.execute(
            "SELECT * FROM orders WHERE driver_tg_id=? AND status IN ('accepted','arrived') ORDER BY updated_at DESC LIMIT 1",
            (driver_tg_id,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def get_passenger_active_order(passenger_tg_id: int) -> Optional[Dict[str, Any]]:
    async with await _get_db() as db:
        async with db.execute(
            "SELECT * FROM orders WHERE passenger_tg_id=? AND status IN ('new','accepted','arrived') ORDER BY created_at DESC LIMIT 1",
            (passenger_tg_id,),
        ) as cur:
            row = await cur.fetchone()
            return dict(row) if row else None


async def order_stats() -> Dict[str, int]:
    result: Dict[str, int] = {"total": 0}
    async with await _get_db() as db:
        async with db.execute("SELECT COUNT(*) as cnt FROM orders") as cur:
            row = await cur.fetchone()
            result["total"] = int(row["cnt"]) if row else 0
        async with db.execute(
            "SELECT status, COUNT(*) as cnt FROM orders GROUP BY status"
        ) as cur:
            rows = await cur.fetchall()
            for r in rows:
                result[str(r["status"])]= int(r["cnt"])  # type: ignore[index]
    return result