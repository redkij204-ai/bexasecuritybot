import sqlite3
from config import DB_PATH, SUPER_ADMIN_ID, DEFAULT_REQUIRED_CHANNEL


def _conn():
    conn = sqlite3.connect(DB_PATH, timeout=10, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        full_name TEXT,
        phone TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        service TEXT,
        quality TEXT,
        amount TEXT,
        link TEXT,
        target_user TEXT,
        details TEXT,
        price INTEGER DEFAULT 0,
        status TEXT DEFAULT 'pending',
        reject_reason TEXT,
        rating INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS required_channels (
        channel_username TEXT PRIMARY KEY,
        added_at TEXT DEFAULT CURRENT_TIMESTAMP
    )""")
    conn.commit()

    # Bosh admin va boshlang'ich majburiy kanalni bazaga urug'lash (bir martalik)
    cur.execute("INSERT OR IGNORE INTO admins (user_id, username) VALUES (?, ?)",
                (SUPER_ADMIN_ID, "bosh_admin"))
    cur.execute("INSERT OR IGNORE INTO required_channels (channel_username) VALUES (?)",
                (DEFAULT_REQUIRED_CHANNEL,))
    conn.commit()
    conn.close()


# ---------------- USERS ----------------
def save_user(user_id, username, full_name, phone=None):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT phone FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    if row and phone is None:
        phone = row["phone"]
    cur.execute("""INSERT INTO users (user_id, username, full_name, phone) VALUES (?,?,?,?)
                   ON CONFLICT(user_id) DO UPDATE SET
                     username=excluded.username,
                     full_name=excluded.full_name,
                     phone=COALESCE(excluded.phone, users.phone)""",
                (user_id, username, full_name, phone))
    conn.commit()
    conn.close()


def get_user(user_id):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_users():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""SELECT u.*,
                   (SELECT COUNT(*) FROM orders o WHERE o.user_id = u.user_id) AS orders_count
                   FROM users u ORDER BY u.created_at DESC""")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_all_user_ids():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id FROM users")
    rows = [r["user_id"] for r in cur.fetchall()]
    conn.close()
    return rows


# ---------------- ORDERS ----------------
def save_order(order: dict) -> int:
    conn = _conn()
    cur = conn.cursor()
    cur.execute("""INSERT INTO orders
        (user_id, service, quality, amount, link, target_user, details, price, status)
        VALUES (?,?,?,?,?,?,?,?, 'pending')""",
                (order.get('user_id'), order.get('service'), order.get('quality'),
                 order.get('amount'), order.get('link'), order.get('target_user'),
                 order.get('details'), order.get('price', 0)))
    order_id = cur.lastrowid
    conn.commit()
    conn.close()
    return order_id


def get_order(order_id):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE id=?", (order_id,))
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def get_user_orders(user_id):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders WHERE user_id=? ORDER BY created_at DESC", (user_id,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def get_recent_orders(limit=200):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM orders ORDER BY created_at DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def update_order_status(order_id, status, reason=None):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status=?, reject_reason=? WHERE id=?", (status, reason, order_id))
    conn.commit()
    conn.close()


def set_rating(order_id, rating):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET rating=? WHERE id=?", (rating, order_id))
    conn.commit()
    conn.close()


def get_stats():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) c FROM users")
    total_users = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM orders")
    total_orders = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM orders WHERE status='done'")
    done_orders = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM orders WHERE status='rejected'")
    rejected_orders = cur.fetchone()["c"]
    cur.execute("SELECT COUNT(*) c FROM orders WHERE status='pending'")
    pending_orders = cur.fetchone()["c"]
    cur.execute("SELECT SUM(price) s FROM orders WHERE status='done'")
    total_income = cur.fetchone()["s"] or 0
    conn.close()
    return {
        "total_users": total_users,
        "total_orders": total_orders,
        "done_orders": done_orders,
        "rejected_orders": rejected_orders,
        "pending_orders": pending_orders,
        "total_income": total_income,
    }


# ---------------- ADMINS ----------------
def is_admin(user_id):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM admins WHERE user_id=?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row is not None


def get_admins():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM admins ORDER BY added_at ASC")
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def add_admin(user_id, username=None):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO admins (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()
    conn.close()


def remove_admin(user_id):
    if user_id == SUPER_ADMIN_ID:
        return False
    conn = _conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM admins WHERE user_id=?", (user_id,))
    conn.commit()
    conn.close()
    return True


# ---------------- MAJBURIY OBUNA KANALLARI ----------------
def get_required_channels():
    conn = _conn()
    cur = conn.cursor()
    cur.execute("SELECT channel_username FROM required_channels ORDER BY added_at ASC")
    rows = [r["channel_username"] for r in cur.fetchall()]
    conn.close()
    return rows


def add_required_channel(channel_username):
    channel_username = channel_username.strip()
    if not channel_username.startswith("@"):
        channel_username = "@" + channel_username
    conn = _conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO required_channels (channel_username) VALUES (?)", (channel_username,))
    conn.commit()
    conn.close()


def remove_required_channel(channel_username):
    conn = _conn()
    cur = conn.cursor()
    cur.execute("DELETE FROM required_channels WHERE channel_username=?", (channel_username,))
    conn.commit()
    conn.close()
