import sqlite3
import os

DB_FILE = 'warranty_manager.db'

# ------------------ Database Initialization ------------------
def init_db():
    """Initialize database with invoices and users tables."""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Invoices table
    c.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            invoice_date TEXT NOT NULL,
            warranty_start TEXT NOT NULL,
            warranty_duration INTEGER NOT NULL,
            paid INTEGER DEFAULT 0,
            pdf_path TEXT NOT NULL
        )
    ''')

    # Users table
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'user',
            security_question_1 TEXT DEFAULT '',
            security_answer_1 TEXT DEFAULT '',
            security_question_2 TEXT DEFAULT '',
            security_answer_2 TEXT DEFAULT ''
        )
    ''')

    # Create default admin if not exists
    c.execute("SELECT * FROM users WHERE username='admin'")
    if not c.fetchone():
        c.execute('''
            INSERT INTO users (username, password, role, 
                               security_question_1, security_answer_1,
                               security_question_2, security_answer_2)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', ('admin', 'admin123', 'admin',
              'Default question 1', 'answer1',
              'Default question 2', 'answer2'))

    conn.commit()
    conn.close()


    conn = sqlite3.connect('warranty_manager.db')
    c = conn.cursor()

    # Add missing columns if they don't exist
    try:
        c.execute("ALTER TABLE users ADD COLUMN security_question_1 TEXT DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN security_answer_1 TEXT DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN security_question_2 TEXT DEFAULT ''")
        c.execute("ALTER TABLE users ADD COLUMN security_answer_2 TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass  # columns already exist

    conn.commit()
    conn.close()

# ------------------ Invoice Functions ------------------
def insert_invoice(customer_name, invoice_date, warranty_start, warranty_duration, pdf_path, invoice_id=None):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    if invoice_id:
        c.execute('''
            INSERT INTO invoices (id, customer_name, invoice_date, warranty_start, warranty_duration, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (invoice_id, customer_name, invoice_date, warranty_start, warranty_duration, pdf_path))
    else:
        c.execute('''
            INSERT INTO invoices (customer_name, invoice_date, warranty_start, warranty_duration, pdf_path)
            VALUES (?, ?, ?, ?, ?)
        ''', (customer_name, invoice_date, warranty_start, warranty_duration, pdf_path))
    conn.commit()
    conn.close()


def update_invoice_paid(invoice_id, pdf_path):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE invoices SET paid=1, pdf_path=? WHERE id=?', (pdf_path, invoice_id))
    conn.commit()
    conn.close()


def update_invoice_pdf(invoice_id, pdf_path):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('UPDATE invoices SET pdf_path=? WHERE id=?', (pdf_path, invoice_id))
    conn.commit()
    conn.close()


def get_invoice_pdf_path(invoice_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT pdf_path FROM invoices WHERE id=?', (invoice_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def get_all_invoices():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('SELECT id, customer_name, paid, warranty_start, warranty_duration FROM invoices')
    invoices = c.fetchall()
    conn.close()
    return invoices


def delete_invoice_by_id(invoice_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('SELECT pdf_path FROM invoices WHERE id=?', (invoice_id,))
        result = c.fetchone()
        if result:
            pdf_path = result[0]
            if pdf_path and os.path.exists(pdf_path):
                os.remove(pdf_path)
        c.execute('DELETE FROM invoices WHERE id=?', (invoice_id,))
        conn.commit()
    finally:
        conn.close()


# ------------------ User Login Functions ------------------
def check_user_credentials(username, password):
    """Return user dict if login successful, else None"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, username, role FROM users WHERE username=? AND password=?", (username, password))
    row = c.fetchone()
    conn.close()
    if row:
        return {"user_id": row[0], "username": row[1], "role": row[2]}
    return None


def create_user(username, password, role='user', sq1='', sa1='', sq2='', sa2=''):
    """Add new user (admin or normal) with security questions"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO users (username, password, role, 
                               security_question_1, security_answer_1,
                               security_question_2, security_answer_2)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (username, password, role, sq1, sa1, sq2, sa2))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()


def delete_user(user_id):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()


def get_all_users():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT user_id, username, role FROM users")
    users = c.fetchall()
    conn.close()
    return users


def verify_security_answers(username, ans1, ans2):
    """Check if security answers are correct"""
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        SELECT user_id FROM users 
        WHERE username=? AND security_answer_1=? AND security_answer_2=?
    ''', (username, ans1, ans2))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None


def update_user_password(user_id, new_password):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("UPDATE users SET password=? WHERE user_id=?", (new_password, user_id))
    conn.commit()
    conn.close()
