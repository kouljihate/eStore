import sqlite3
import os
import bcrypt

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "app.db")


def _get_connection():
    os.makedirs(DB_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def check_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))


def init_db():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            quantity REAL DEFAULT 0,
            price REAL DEFAULT 0,
            buying_price REAL DEFAULT 0,
            category TEXT DEFAULT '',
            packaging TEXT DEFAULT '',
            description TEXT DEFAULT '',
            low_stock_qty REAL DEFAULT 5,
            supplier_name TEXT DEFAULT '',
            supplier_whatsapp TEXT DEFAULT '',
            supplier_email TEXT DEFAULT '',
            barcode TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('in','out')),
            quantity REAL NOT NULL,
            date TEXT DEFAULT (datetime('now')),
            note TEXT DEFAULT '',
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income','expense')),
            amount REAL NOT NULL,
            category TEXT DEFAULT '',
            date TEXT DEFAULT (datetime('now')),
            description TEXT DEFAULT '',
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS credit_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            customer_id INTEGER NOT NULL,
            total_amount REAL NOT NULL,
            paid_amount REAL DEFAULT 0,
            status TEXT DEFAULT 'open' CHECK(status IN ('open','closed')),
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS credit_note_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_note_id INTEGER NOT NULL,
            product_id INTEGER,
            product_name TEXT NOT NULL,
            quantity REAL NOT NULL,
            unit_price REAL NOT NULL,
            total_price REAL NOT NULL,
            FOREIGN KEY (credit_note_id) REFERENCES credit_notes(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE SET NULL
        );

        CREATE TABLE IF NOT EXISTS credit_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            credit_note_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            date TEXT DEFAULT (datetime('now')),
            note TEXT DEFAULT '',
            FOREIGN KEY (credit_note_id) REFERENCES credit_notes(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()


def user_count() -> int:
    conn = _get_connection()
    row = conn.execute("SELECT COUNT(*) as cnt FROM users").fetchone()
    conn.close()
    return row["cnt"]


def create_user(name: str, email: str, password: str) -> int:
    conn = _get_connection()
    try:
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, hash_password(password)),
        )
        conn.commit()
        return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(email: str, password: str):
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE email = ?",
        (email,),
    ).fetchone()
    conn.close()
    if row and check_password(password, row["password_hash"]):
        return dict(row)
    return None


def get_user(user_id: int):
    conn = _get_connection()
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_product(user_id: int, name: str, quantity: float, price: float, buying_price: float,
                category: str, packaging: str, description: str, low_stock_qty: float,
                supplier_name: str = "", supplier_whatsapp: str = "", supplier_email: str = "",
                barcode: str = "") -> int:
    quantity = max(0, quantity)
    price = max(0, price)
    buying_price = max(0, buying_price)
    low_stock_qty = max(0, low_stock_qty)
    conn = _get_connection()
    cursor = conn.execute(
        """INSERT INTO products (user_id, name, quantity, price, buying_price, category, packaging,
           description, low_stock_qty, supplier_name, supplier_whatsapp, supplier_email, barcode)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (user_id, name, quantity, price, buying_price, category, packaging,
         description, low_stock_qty, supplier_name, supplier_whatsapp, supplier_email, barcode),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def update_product(product_id: int, name: str, quantity: float, price: float, buying_price: float,
                   category: str, packaging: str, description: str, low_stock_qty: float,
                   supplier_name: str = "", supplier_whatsapp: str = "", supplier_email: str = "",
                   barcode: str = ""):
    quantity = max(0, quantity)
    price = max(0, price)
    buying_price = max(0, buying_price)
    low_stock_qty = max(0, low_stock_qty)
    conn = _get_connection()
    conn.execute(
        """UPDATE products SET name=?, quantity=?, price=?, buying_price=?, category=?, packaging=?,
           description=?, low_stock_qty=?, supplier_name=?, supplier_whatsapp=?, supplier_email=?,
           barcode=?, updated_at=datetime('now') WHERE id=?""",
        (name, quantity, price, buying_price, category, packaging, description,
         low_stock_qty, supplier_name, supplier_whatsapp, supplier_email, barcode, product_id),
    )
    conn.commit()
    conn.close()


def delete_product(product_id: int):
    conn = _get_connection()
    conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()


def get_products(user_id: int):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM products WHERE user_id = ? ORDER BY name", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_product(product_id: int):
    conn = _get_connection()
    row = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_product_by_barcode(barcode: str, user_id: int):
    conn = _get_connection()
    row = conn.execute(
        "SELECT * FROM products WHERE barcode = ? AND user_id = ?", (barcode, user_id)
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def add_stock_movement(product_id: int, user_id: int, mtype: str, quantity: float, note: str):
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    conn = _get_connection()
    try:
        product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
        if not product:
            raise ValueError("Product not found")
        if mtype == "out" and quantity > product["quantity"]:
            raise ValueError("Insufficient stock")
        new_qty = product["quantity"] + quantity if mtype == "in" else product["quantity"] - quantity
        conn.execute("UPDATE products SET quantity=?, updated_at=datetime('now') WHERE id=?",
                     (new_qty, product_id))
        conn.execute(
            "INSERT INTO stock_movements (product_id, user_id, type, quantity, note) VALUES (?,?,?,?,?)",
            (product_id, user_id, mtype, quantity, note),
        )
        conn.commit()
    finally:
        conn.close()


def get_stock_movements(user_id: int, limit: int = 50):
    conn = _get_connection()
    rows = conn.execute(
        """SELECT sm.*, p.name as product_name FROM stock_movements sm
           JOIN products p ON sm.product_id = p.id
           WHERE sm.user_id = ? ORDER BY sm.date DESC LIMIT ?""",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_stock_movements_by_product(user_id: int, product_id: int, limit: int = 50):
    conn = _get_connection()
    rows = conn.execute(
        """SELECT sm.*, p.name as product_name FROM stock_movements sm
           JOIN products p ON sm.product_id = p.id
           WHERE sm.user_id = ? AND sm.product_id = ? ORDER BY sm.date DESC LIMIT ?""",
        (user_id, product_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_transaction(user_id: int, ttype: str, amount: float, category: str, description: str):
    if amount <= 0:
        raise ValueError("Amount must be positive")
    conn = _get_connection()
    conn.execute(
        "INSERT INTO transactions (user_id, type, amount, category, description) VALUES (?,?,?,?,?)",
        (user_id, ttype, amount, category, description),
    )
    conn.commit()
    conn.close()


def get_transactions(user_id: int, limit: int = 50):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM transactions WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_customer(user_id: int, name: str, phone: str = "") -> int:
    if not name.strip():
        raise ValueError("Customer name is required")
    conn = _get_connection()
    cursor = conn.execute(
        "INSERT INTO customers (user_id, name, phone) VALUES (?, ?, ?)",
        (user_id, name, phone),
    )
    conn.commit()
    conn.close()
    return cursor.lastrowid


def get_customers(user_id: int):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM customers WHERE user_id = ? ORDER BY name", (user_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_customer(customer_id: int):
    conn = _get_connection()
    row = conn.execute("SELECT * FROM customers WHERE id = ?", (customer_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def add_credit_note(user_id: int, customer_id: int, items: list):
    if not items:
        raise ValueError("Credit note must have at least one item")
    conn = _get_connection()
    try:
        total_amount = sum(item[4] for item in items)
        cursor = conn.execute(
            "INSERT INTO credit_notes (user_id, customer_id, total_amount) VALUES (?, ?, ?)",
            (user_id, customer_id, total_amount),
        )
        cn_id = cursor.lastrowid
        for item in items:
            product_id = item[0]
            qty = item[2]
            product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
            if product:
                if qty > product["quantity"]:
                    raise ValueError("Insufficient stock for credit sale")
                new_qty = product["quantity"] - qty
                conn.execute("UPDATE products SET quantity=?, updated_at=datetime('now') WHERE id=?",
                             (new_qty, product_id))
                conn.execute(
                    "INSERT INTO stock_movements (product_id, user_id, type, quantity, note) VALUES (?,?, 'out', ?,?)",
                    (product_id, user_id, qty, f"Credit sale #{cn_id}"),
                )
            conn.execute(
                """INSERT INTO credit_note_items (credit_note_id, product_id, product_name, quantity, unit_price, total_price)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (cn_id, item[0], item[1], item[2], item[3], item[4]),
            )
        conn.commit()
        return cn_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_credit_notes(user_id: int, status: str = None):
    conn = _get_connection()
    query = """SELECT cn.*, c.name as customer_name, c.phone as customer_phone
               FROM credit_notes cn
               JOIN customers c ON cn.customer_id = c.id
               WHERE cn.user_id = ?"""
    params = [user_id]
    if status:
        query += " AND cn.status = ?"
        params.append(status)
    query += " ORDER BY cn.created_at DESC"
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_credit_note(cn_id: int):
    conn = _get_connection()
    row = conn.execute(
        """SELECT cn.*, c.name as customer_name, c.phone as customer_phone
           FROM credit_notes cn
           JOIN customers c ON cn.customer_id = c.id
           WHERE cn.id = ?""",
        (cn_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_credit_note_items(cn_id: int):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM credit_note_items WHERE credit_note_id = ?", (cn_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_credit_payment(credit_note_id: int, amount: float, note: str = ""):
    if amount <= 0:
        raise ValueError("Payment amount must be positive")
    conn = _get_connection()
    try:
        cn = conn.execute("SELECT * FROM credit_notes WHERE id = ?", (credit_note_id,)).fetchone()
        if not cn:
            raise ValueError("Credit note not found")
        new_paid = cn["paid_amount"] + amount
        if new_paid > cn["total_amount"] + 0.001:
            raise ValueError("Payment exceeds remaining balance")
        new_status = "closed" if abs(new_paid - cn["total_amount"]) < 0.001 else "open"
        conn.execute(
            "INSERT INTO credit_payments (credit_note_id, amount, note) VALUES (?, ?, ?)",
            (credit_note_id, amount, note),
        )
        conn.execute(
            "UPDATE credit_notes SET paid_amount = ?, status = ?, updated_at = datetime('now') WHERE id = ?",
            (new_paid, new_status, credit_note_id),
        )
        conn.execute(
            "INSERT INTO transactions (user_id, type, amount, category, description) VALUES (?, 'income', ?, 'Credit', ?)",
            (cn["user_id"], amount, f"Credit payment for note #{credit_note_id}"),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_credit_payments(credit_note_id: int):
    conn = _get_connection()
    rows = conn.execute(
        "SELECT * FROM credit_payments WHERE credit_note_id = ? ORDER BY date DESC",
        (credit_note_id,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_credit_summary(user_id: int):
    conn = _get_connection()
    total = conn.execute(
        "SELECT COALESCE(SUM(total_amount - paid_amount), 0) as total FROM credit_notes WHERE user_id = ? AND status = 'open'",
        (user_id,),
    ).fetchone()["total"]
    count = conn.execute(
        "SELECT COUNT(*) as cnt FROM credit_notes WHERE user_id = ? AND status = 'open'",
        (user_id,),
    ).fetchone()["cnt"]
    conn.close()
    return {"total_outstanding": total, "open_count": count}


def get_dashboard_data(user_id: int):
    conn = _get_connection()
    stock_value = conn.execute(
        "SELECT COALESCE(SUM(quantity * price), 0) as val FROM products WHERE user_id = ?",
        (user_id,),
    ).fetchone()["val"]
    buying_cost = conn.execute(
        "SELECT COALESCE(SUM(quantity * buying_price), 0) as val FROM products WHERE user_id = ?",
        (user_id,),
    ).fetchone()["val"]
    cash_income = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as tot FROM transactions WHERE user_id = ? AND type='income'",
        (user_id,),
    ).fetchone()["tot"]
    cash_expense = conn.execute(
        "SELECT COALESCE(SUM(amount), 0) as tot FROM transactions WHERE user_id = ? AND type='expense'",
        (user_id,),
    ).fetchone()["tot"]
    cash_balance = cash_income - cash_expense
    low_stock = conn.execute(
        "SELECT COUNT(*) as cnt FROM products WHERE user_id = ? AND quantity <= low_stock_qty",
        (user_id,),
    ).fetchone()["cnt"]
    product_count = conn.execute(
        "SELECT COUNT(*) as cnt FROM products WHERE user_id = ?", (user_id,)
    ).fetchone()["cnt"]
    credit_outstanding = conn.execute(
        "SELECT COALESCE(SUM(total_amount - paid_amount), 0) as tot FROM credit_notes WHERE user_id = ? AND status = 'open'",
        (user_id,),
    ).fetchone()["tot"]
    conn.close()
    return {
        "stock_value": stock_value,
        "buying_cost": buying_cost,
        "potential_profit": stock_value - buying_cost,
        "cash_balance": cash_balance,
        "low_stock_count": low_stock,
        "product_count": product_count,
        "cash_income": cash_income,
        "cash_expense": cash_expense,
        "credit_outstanding": credit_outstanding,
    }
