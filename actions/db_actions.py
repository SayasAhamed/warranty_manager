# actions/db_actions.py
from __future__ import annotations

import os
import sqlite3
import base64
import hashlib
import hmac
import secrets
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

DB_FILE = str(Path(__file__).resolve().parents[1] / "warranty_manager.db")

# ------------------ Connection ------------------
def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

# ------------------ Password Hashing ------------------
_ALG = "pbkdf2_sha256"
_ITER = 260000

def _is_hashed(pw: str) -> bool:
    return isinstance(pw, str) and pw.startswith(_ALG + "$")

def _hash_password(password: str, iterations: int = _ITER) -> str:
    salt = secrets.token_bytes(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{_ALG}${iterations}${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}"

def _verify_password(password: str, stored: str) -> bool:
    try:
        alg, s_iter, s_salt, s_hash = stored.split("$", 3)
        if alg != _ALG:
            return False
        iterations = int(s_iter)
        salt = base64.b64decode(s_salt)
        expected = base64.b64decode(s_hash)
        dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False

# ------------------ Schema / Migrations ------------------
def _create_tables_and_indexes(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            warranty_start TEXT NOT NULL,
            warranty_duration INTEGER NOT NULL,
            paid INTEGER NOT NULL DEFAULT 0,
            pdf_path TEXT NOT NULL
        );
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            security_question_1 TEXT DEFAULT '',
            security_answer_1 TEXT DEFAULT '',
            security_question_2 TEXT DEFAULT '',
            security_answer_2 TEXT DEFAULT ''
        );
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_customer ON invoices(customer_name);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_date ON invoices(invoice_date);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_invoices_paid ON invoices(paid);")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_users_username ON users(username COLLATE NOCASE);")

def _ensure_default_admin(conn: sqlite3.Connection) -> None:
    row = conn.execute(
        "SELECT user_id, username, password FROM users WHERE lower(username)=lower(?);",
        ("admin",)
    ).fetchone()
    if row is None:
        hpw = _hash_password("admin123")
        conn.execute("""
            INSERT INTO users (username, password, role,
                               security_question_1, security_answer_1,
                               security_question_2, security_answer_2)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, ("admin", hpw, "admin",
              "Default question 1", "answer1",
              "Default question 2", "answer2"))
    else:
        if not _is_hashed(row["password"]):
            hpw = _hash_password(row["password"])
            conn.execute("UPDATE users SET password=? WHERE user_id=?;", (hpw, row["user_id"]))

def _migrate_existing_passwords(conn: sqlite3.Connection) -> None:
    rows = conn.execute("SELECT user_id, password FROM users;").fetchall()
    for r in rows:
        if not _is_hashed(r["password"]):
            hpw = _hash_password(r["password"])
            conn.execute("UPDATE users SET password=? WHERE user_id=?;", (hpw, r["user_id"]))

# ------------------ Public: init_db ------------------
def init_db() -> None:
    with get_conn() as conn:
        _create_tables_and_indexes(conn)
        _ensure_default_admin(conn)
        _migrate_existing_passwords(conn)
        conn.commit()

# ------------------ Invoice APIs ------------------
def insert_invoice(customer_name: str, invoice_date: str, warranty_start: str,
                   warranty_duration: int, pdf_path: str, invoice_id: Optional[int] = None) -> None:
    with get_conn() as conn:
        if invoice_id:
            conn.execute("""
                INSERT INTO invoices (id, customer_name, invoice_date, warranty_start, warranty_duration, pdf_path)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (invoice_id, customer_name, invoice_date, warranty_start, warranty_duration, pdf_path))
        else:
            conn.execute("""
                INSERT INTO invoices (customer_name, invoice_date, warranty_start, warranty_duration, pdf_path)
                VALUES (?, ?, ?, ?, ?)
            """, (customer_name, invoice_date, warranty_start, warranty_duration, pdf_path))
        conn.commit()

def update_invoice_paid(invoice_id: int, pdf_path: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE invoices SET paid=1, pdf_path=? WHERE id=?;", (pdf_path, invoice_id))
        conn.commit()

def update_invoice_pdf(invoice_id: int, pdf_path: str) -> None:
    with get_conn() as conn:
        conn.execute("UPDATE invoices SET pdf_path=? WHERE id=?;", (pdf_path, invoice_id))
        conn.commit()

def get_invoice_pdf_path(invoice_id: int) -> Optional[str]:
    with get_conn() as conn:
        row = conn.execute("SELECT pdf_path FROM invoices WHERE id=?;", (invoice_id,)).fetchone()
        return row["pdf_path"] if row else None

def get_all_invoices() -> List[Tuple[Any, ...]]:
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT id, customer_name, paid, warranty_start, warranty_duration
            FROM invoices
            ORDER BY id DESC;
        """).fetchall()
        return [(r["id"], r["customer_name"], r["paid"], r["warranty_start"], r["warranty_duration"]) for r in rows]

def delete_invoice_by_id(invoice_id: int) -> None:
    with get_conn() as conn:
        row = conn.execute("SELECT pdf_path FROM invoices WHERE id=?;", (invoice_id,)).fetchone()
        if row:
            pdf_path = row["pdf_path"]
            if pdf_path and os.path.exists(pdf_path):
                try:
                    os.remove(pdf_path)
                except Exception:
                    pass
        conn.execute("DELETE FROM invoices WHERE id=?;", (invoice_id,))
        conn.commit()

# ------------------ Users (case-insensitive usernames) ------------------
def check_user_credentials(username: str, password: str) -> Optional[Dict[str, Any]]:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT user_id, username, role, password FROM users WHERE lower(username)=lower(?);",
            (username.strip(),)
        ).fetchone()
        if not row:
            return None
        stored = row["password"]
        ok = _verify_password(password, stored) if _is_hashed(stored) else (stored == password)
        if ok:
            return {"user_id": row["user_id"], "username": row["username"], "role": row["role"]}
        return None

def create_user(username: str, password: str, role: str = 'user',
                sq1: str = '', sa1: str = '', sq2: str = '', sa2: str = '') -> bool:
    uname = username.strip().lower()
    with get_conn() as conn:
        try:
            hpw = _hash_password(password)
            conn.execute("""
                INSERT INTO users (username, password, role,
                                   security_question_1, security_answer_1,
                                   security_question_2, security_answer_2)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (uname, hpw, role, sq1, sa1, sq2, sa2))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

def delete_user(user_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM users WHERE user_id=?;", (user_id,))
        conn.commit()

def get_all_users() -> List[Tuple[int, str, str]]:
    with get_conn() as conn:
        rows = conn.execute("SELECT user_id, username, role FROM users ORDER BY user_id ASC;").fetchall()
        return [(r["user_id"], r["username"], r["role"]) for r in rows]

def verify_security_answers(username: str, ans1: str, ans2: str) -> Optional[int]:
    with get_conn() as conn:
        row = conn.execute("""
            SELECT user_id FROM users
            WHERE lower(username)=lower(?) AND security_answer_1=? AND security_answer_2=?;
        """, (username.strip(), ans1, ans2)).fetchone()
        return int(row["user_id"]) if row else None

def update_user_password(user_id: int, new_password: str) -> None:
    with get_conn() as conn:
        hpw = _hash_password(new_password)
        conn.execute("UPDATE users SET password=? WHERE user_id=?;", (hpw, user_id))
        conn.commit()

def update_username(user_id: int, new_username: str) -> bool:
    """
    Change a user's username (case-insensitive unique). Returns True on success.
    """
    uname = new_username.strip().lower()
    if not uname:
        return False
    with get_conn() as conn:
        try:
            conn.execute("UPDATE users SET username=? WHERE user_id=?;", (uname, user_id))
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            # duplicate username
            return False

# ----- Helpers you can use if needed -----
def set_password(username: str, new_password: str) -> bool:
    """Set password for any user (case-insensitive). Returns True if user exists and was updated."""
    with get_conn() as conn:
        row = conn.execute("SELECT user_id FROM users WHERE lower(username)=lower(?);", (username.strip(),)).fetchone()
        if not row:
            return False
        hpw = _hash_password(new_password)
        conn.execute("UPDATE users SET password=? WHERE user_id=?;", (hpw, row["user_id"]))
        conn.commit()
        return True

def force_set_admin_password(new_password: str = "admin123") -> None:
    """Force-reset the admin password (case-insensitive username match)."""
    with get_conn() as conn:
        row = conn.execute("SELECT user_id FROM users WHERE lower(username)=lower('admin');").fetchone()
        if row:
            hpw = _hash_password(new_password)
            conn.execute("UPDATE users SET password=? WHERE user_id=?;", (hpw, row["user_id"]))
        else:
            hpw = _hash_password(new_password)
            conn.execute("""
                INSERT INTO users (username, password, role,
                                   security_question_1, security_answer_1,
                                   security_question_2, security_answer_2)
                VALUES ('admin', ?, 'admin', 'Default question 1', 'answer1', 'Default question 2', 'answer2');
            """, (hpw,))
        conn.commit()
