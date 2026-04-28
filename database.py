# database.py

import sqlite3
import hashlib
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "cinema.db"

SEAT_PRICE = 150.0        # ціна одного місця в гривнях
STARTING_BALANCE = 500.0  # початковий баланс нового користувача

# ================== ПІДКЛЮЧЕННЯ ==================

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ================== ІНІЦІАЛІЗАЦІЯ ==================

def init_db():
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT    NOT NULL UNIQUE,
                password_hash TEXT    NOT NULL,
                full_name     TEXT    NOT NULL,
                role          TEXT    NOT NULL DEFAULT 'user',
                balance       REAL    NOT NULL DEFAULT 0.0
            );

            CREATE TABLE IF NOT EXISTS halls (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                hall_id     TEXT    NOT NULL UNIQUE,
                name        TEXT    NOT NULL,
                seat_count  INTEGER NOT NULL,
                showtime    TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS bookings (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id),
                hall_id     INTEGER NOT NULL REFERENCES halls(id),
                seat        TEXT    NOT NULL,
                booked_at   TEXT    NOT NULL,
                price_paid  REAL    NOT NULL DEFAULT 0.0,
                status      TEXT    NOT NULL DEFAULT 'active'
            );

            CREATE UNIQUE INDEX IF NOT EXISTS idx_bookings_active
                ON bookings(hall_id, seat)
                WHERE status = 'active';

            CREATE TABLE IF NOT EXISTS booking_log (
                id        INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id   INTEGER NOT NULL REFERENCES users(id),
                hall_id   TEXT    NOT NULL,
                seat      TEXT    NOT NULL,
                action    TEXT    NOT NULL,
                timestamp TEXT    NOT NULL,
                amount    REAL    NOT NULL DEFAULT 0.0
            );
        """)
    _seed_initial_data()


def _seed_initial_data():
    with get_connection() as conn:
        if not conn.execute("SELECT 1 FROM users LIMIT 1").fetchone():
            users = [
                ("admin", _hash("admin123"), "Адміністратор", "admin", 9999.0),
                ("user1", _hash("pass123"),  "Іван Петренко",  "user",  STARTING_BALANCE),
            ]
            conn.executemany(
                """INSERT INTO users
                   (username, password_hash, full_name, role, balance)
                   VALUES (?,?,?,?,?)""",
                users
            )

        if not conn.execute("SELECT 1 FROM halls LIMIT 1").fetchone():
            # showtime — час сеансу, через 6 годин від зараз для демо
            from datetime import timedelta
            soon = (datetime.now() + timedelta(hours=6)).strftime("%Y-%m-%d %H:%M:%S")
            halls = [
                ("hall_1", "Зал 1 (Стандарт)", 25, soon),
                ("hall_2", "Зал 2 (VIP)",       35, soon),
            ]
            conn.executemany(
                "INSERT INTO halls (hall_id, name, seat_count, showtime) VALUES (?,?,?,?)",
                halls
            )

# ================== ДОПОМІЖНІ ==================

def _hash(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def _parse_dt(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d %H:%M:%S")

def _get_hall_row_id(conn, hall_id: str):
    row = conn.execute(
        "SELECT id FROM halls WHERE hall_id = ?", (hall_id,)
    ).fetchone()
    return row["id"] if row else None

def _get_user_row_id(conn, username: str):
    row = conn.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    ).fetchone()
    return row["id"] if row else None

# ================== РОЗРАХУНОК ПОВЕРНЕННЯ ==================

def calculate_refund(booked_at: str, showtime: str, price_paid: float) -> tuple[float, str]:
    """
    Повертає (сума_повернення, пояснення).

    Правила:
    - До сеансу < 30 хв          → 0% (повернення відсутнє)
    - Бронь існує <= 3 год        → 100%
    - Кожна година після 3-х      → -2%, мінімум 50%
    """
    now = datetime.now()
    show_dt   = _parse_dt(showtime)
    booked_dt = _parse_dt(booked_at)

    minutes_to_show = (show_dt - now).total_seconds() / 60

    # Менше 30 хвилин до сеансу — повернення неможливе
    if minutes_to_show < 30:
        return 0.0, "До сеансу менше 30 хвилин — повернення неможливе"

    hours_held = (now - booked_dt).total_seconds() / 3600

    if hours_held <= 3:
        percent = 100.0
    else:
        extra_hours = int(hours_held - 3)
        percent = max(50.0, 100.0 - extra_hours * 2)

    refund = round(price_paid * percent / 100, 2)
    explanation = f"Повертається {percent:.0f}% → {refund:.2f} грн"
    return refund, explanation

# ================== АВТОРИЗАЦІЯ ==================

def db_try_login(username: str, password: str) -> dict | None:
    username = username.strip().lower()
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
    if row and row["password_hash"] == _hash(password):
        return {
            "username":  row["username"],
            "role":      row["role"],
            "full_name": row["full_name"]
        }
    return None


def db_register_user(
    username: str, password: str, full_name: str, role: str = "user"
) -> tuple[bool, str]:
    username = username.strip().lower()
    if not username:
        return False, "Логін не може бути порожнім"
    if len(password) < 6:
        return False, "Пароль має бути не менше 6 символів"
    if not full_name.strip():
        return False, "Повне ім'я не може бути порожнім"
    if role not in ("admin", "user"):
        return False, "Невідома роль"
    try:
        with get_connection() as conn:
            conn.execute(
                """INSERT INTO users
                   (username, password_hash, full_name, role, balance)
                   VALUES (?,?,?,?,?)""",
                (username, _hash(password), full_name.strip(),
                 role, STARTING_BALANCE)
            )
        return True, f"Користувача '{username}' створено (баланс: {STARTING_BALANCE} грн)"
    except sqlite3.IntegrityError:
        return False, "Такий користувач вже існує"


def db_change_password(
    username: str, old_password: str, new_password: str
) -> tuple[bool, str]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT password_hash FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return False, "Користувача не знайдено"
        if row["password_hash"] != _hash(old_password):
            return False, "Невірний поточний пароль"
        if len(new_password) < 6:
            return False, "Новий пароль має бути не менше 6 символів"
        if old_password == new_password:
            return False, "Новий пароль збігається зі старим"
        conn.execute(
            "UPDATE users SET password_hash = ? WHERE username = ?",
            (_hash(new_password), username)
        )
    return True, "Пароль успішно змінено"


def db_get_users_list() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT username, full_name, role, balance
               FROM users ORDER BY role DESC, username"""
        ).fetchall()
    return [dict(r) for r in rows]


def db_get_balance(username: str) -> float:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT balance FROM users WHERE username = ?", (username,)
        ).fetchone()
    return round(row["balance"], 2) if row else 0.0

# ================== ЗАЛИ ==================

def db_get_halls_info() -> list[dict]:
    with get_connection() as conn:
        halls = conn.execute(
            "SELECT * FROM halls ORDER BY hall_id"
        ).fetchall()
        result = []
        for h in halls:
            busy = conn.execute(
                "SELECT COUNT(*) FROM bookings WHERE hall_id = ? AND status = 'active'",
                (h["id"],)
            ).fetchone()[0]
            total = h["seat_count"]
            result.append({
                "hall_id":  h["hall_id"],
                "name":     h["name"],
                "total":    total,
                "busy":     busy,
                "free":     total - busy,
                "percent":  round((busy / total) * 100, 1) if total else 0.0,
                "showtime": h["showtime"],
                "price":    SEAT_PRICE
            })
    return result


def db_set_showtime(hall_id: str, showtime: str) -> tuple[bool, str]:
    """Адмін змінює час сеансу."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE halls SET showtime = ? WHERE hall_id = ?",
            (showtime, hall_id)
        )
    return True, "Час сеансу оновлено"

# ================== МІСЦЯ ==================

def db_get_hall_seats(hall_id: str) -> list[dict]:
    with get_connection() as conn:
        hall_row = conn.execute(
            "SELECT * FROM halls WHERE hall_id = ?", (hall_id,)
        ).fetchone()
        if not hall_row:
            return []

        booked = {}
        rows = conn.execute("""
            SELECT b.seat, b.booked_at, b.price_paid, b.status,
                   u.username, u.full_name
            FROM bookings b
            JOIN users u ON b.user_id = u.id
            WHERE b.hall_id = ? AND b.status = 'active'
        """, (hall_row["id"],)).fetchall()

        for r in rows:
            booked[r["seat"]] = {
                "username":  r["username"],
                "full_name": r["full_name"],
                "booked_at": r["booked_at"],
                "price_paid": r["price_paid"]
            }

        result = []
        for i in range(1, hall_row["seat_count"] + 1):
            seat = str(i)
            if seat in booked:
                result.append({
                    "seat":       seat,
                    "status":     "taken",
                    "occupant":   booked[seat]["username"],
                    "full_name":  booked[seat]["full_name"],
                    "booked_at":  booked[seat]["booked_at"],
                    "price_paid": booked[seat]["price_paid"]
                })
            else:
                result.append({
                    "seat":       seat,
                    "status":     "free",
                    "occupant":   None,
                    "full_name":  None,
                    "booked_at":  None,
                    "price_paid": None
                })
    return result


def db_get_hall_seats_for_user(hall_id: str, session: dict) -> list[dict]:
    seats = db_get_hall_seats(hall_id)
    for item in seats:
        if item["occupant"] == session["username"]:
            item["status"] = "mine"
    return seats

# ================== БРОНЮВАННЯ ==================

def db_reserve_seat(
    session: dict, hall_id: str, seat: str
) -> tuple[bool, str]:
    seat = str(seat).strip()
    with get_connection() as conn:
        hall_row = conn.execute(
            "SELECT * FROM halls WHERE hall_id = ?", (hall_id,)
        ).fetchone()
        if not hall_row:
            return False, "Зал не знайдено"

        if not seat.isdigit() or not (1 <= int(seat) <= hall_row["seat_count"]):
            return False, f"Місця №{seat} не існує в цьому залі"

        # Перевірка: сеанс ще не почався
        minutes_to_show = (
            _parse_dt(hall_row["showtime"]) - datetime.now()
        ).total_seconds() / 60
        if minutes_to_show < 0:
            return False, "Сеанс вже розпочався — бронювання неможливе"
        if minutes_to_show < 30:
            return False, "До сеансу менше 30 хвилин — бронювання закрито"

        user_id  = _get_user_row_id(conn, session["username"])
        hall_rid = hall_row["id"]

        # Місце вже зайняте?
        taken = conn.execute(
            """SELECT 1 FROM bookings
               WHERE hall_id = ? AND seat = ? AND status = 'active'""",
            (hall_rid, seat)
        ).fetchone()
        if taken:
            return False, "Місце вже зайняте іншим користувачем"

        # Перевірка балансу
        user_row = conn.execute(
            "SELECT balance FROM users WHERE id = ?", (user_id,)
        ).fetchone()
        if user_row["balance"] < SEAT_PRICE:
            return False, (
                f"Недостатньо коштів. "
                f"Потрібно: {SEAT_PRICE} грн, "
                f"на балансі: {user_row['balance']:.2f} грн"
            )

        # Списуємо кошти і бронюємо
        conn.execute(
            "UPDATE users SET balance = balance - ? WHERE id = ?",
            (SEAT_PRICE, user_id)
        )
        conn.execute(
            """INSERT INTO bookings
               (user_id, hall_id, seat, booked_at, price_paid, status)
               VALUES (?,?,?,?,?,?)""",
            (user_id, hall_rid, seat, _now(), SEAT_PRICE, "active")
        )
        _db_log(conn, session["username"], hall_id, seat,
                "reserve", -SEAT_PRICE)

    return True, f"Місце №{seat} заброньовано! Списано {SEAT_PRICE} грн"


def db_cancel_my_reservation(
    session: dict, hall_id: str, seat: str = None
) -> tuple[bool, str]:
    with get_connection() as conn:
        hall_row = conn.execute(
            "SELECT * FROM halls WHERE hall_id = ?", (hall_id,)
        ).fetchone()
        if not hall_row:
            return False, "Зал не знайдено"

        user_id  = _get_user_row_id(conn, session["username"])
        hall_rid = hall_row["id"]

        if seat:
            # Скасування конкретного місця
            row = conn.execute(
                """SELECT id, seat, booked_at, price_paid
                   FROM bookings
                   WHERE user_id = ? AND hall_id = ?
                   AND seat = ? AND status = 'active'""",
                (user_id, hall_rid, str(seat))
            ).fetchone()
        else:
            # Скасування першого знайденого (для сумісності)
            row = conn.execute(
                """SELECT id, seat, booked_at, price_paid
                   FROM bookings
                   WHERE user_id = ? AND hall_id = ? AND status = 'active'
                   LIMIT 1""",
                (user_id, hall_rid)
            ).fetchone()

        if not row:
            return False, "Активне бронювання не знайдено"

        refund, explanation = calculate_refund(
            row["booked_at"], hall_row["showtime"], row["price_paid"]
        )

        conn.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
            (row["id"],)
        )
        if refund > 0:
            conn.execute(
                "UPDATE users SET balance = balance + ? WHERE id = ?",
                (refund, user_id)
            )
        _db_log(conn, session["username"], hall_id,
                row["seat"], "cancel_self", refund)

    return True, f"Бронювання місця №{row['seat']} скасовано. {explanation}"


def db_admin_cancel_reservation(
    session: dict, hall_id: str, target_username: str, seat: str = None
) -> tuple[bool, str]:
    if session["role"] != "admin":
        return False, "Недостатньо прав"

    target_username = target_username.strip().lower()
    with get_connection() as conn:
        target_id = _get_user_row_id(conn, target_username)
        if not target_id:
            return False, f"Користувача '{target_username}' не існує"

        hall_row = conn.execute(
            "SELECT * FROM halls WHERE hall_id = ?", (hall_id,)
        ).fetchone()
        hall_rid = hall_row["id"]

        if seat:
            row = conn.execute(
                """SELECT id, seat, booked_at, price_paid
                   FROM bookings
                   WHERE user_id = ? AND hall_id = ?
                   AND seat = ? AND status = 'active'""",
                (target_id, hall_rid, str(seat))
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT id, seat, booked_at, price_paid
                   FROM bookings
                   WHERE user_id = ? AND hall_id = ? AND status = 'active'
                   LIMIT 1""",
                (target_id, hall_rid)
            ).fetchone()

        if not row:
            return False, f"Бронювання не знайдено"

        refund, explanation = calculate_refund(
            row["booked_at"], hall_row["showtime"], row["price_paid"]
        )

        conn.execute(
            "UPDATE bookings SET status = 'cancelled' WHERE id = ?",
            (row["id"],)
        )
        if refund > 0:
            conn.execute(
                "UPDATE users SET balance = balance + ? WHERE id = ?",
                (refund, target_id)
            )
        _db_log(conn, session["username"], hall_id, row["seat"],
                f"admin_cancel:{target_username}", refund)

    return True, (
        f"Бронювання '{target_username}' (місце №{row['seat']}) скасовано. "
        f"{explanation}"
    )

# ================== ЗАПИТИ ДЛЯ UI ==================

def db_get_my_bookings(session: dict) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT h.hall_id, h.name AS hall_name, h.showtime,
                   b.seat, b.booked_at, b.price_paid, b.status
            FROM bookings b
            JOIN halls h ON b.hall_id = h.id
            JOIN users u ON b.user_id = u.id
            WHERE u.username = ?
            ORDER BY b.status, h.hall_id, CAST(b.seat AS INTEGER)
        """, (session["username"],)).fetchall()
    return [dict(r) for r in rows]


def db_get_all_bookings() -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT h.hall_id, h.name AS hall_name,
                   b.seat, b.booked_at, b.price_paid, b.status,
                   u.username, u.full_name
            FROM bookings b
            JOIN halls h ON b.hall_id = h.id
            JOIN users u ON b.user_id = u.id
            WHERE b.status = 'active'
            ORDER BY h.hall_id, CAST(b.seat AS INTEGER)
        """).fetchall()
    return [dict(r) for r in rows]


def db_get_statistics() -> list[dict]:
    return db_get_halls_info()


def db_get_log_entries(last_n: int = 100) -> list[dict]:
    action_map = {
        "reserve":     "Бронювання",
        "cancel_self": "Скасування"
    }
    with get_connection() as conn:
        rows = conn.execute("""
            SELECT l.timestamp, u.username, l.action,
                   l.hall_id, l.seat, l.amount
            FROM booking_log l
            JOIN users u ON l.user_id = u.id
            ORDER BY l.id DESC
            LIMIT ?
        """, (last_n,)).fetchall()

        result = []
        for r in rows:
            action = r["action"]
            if action.startswith("admin_cancel:"):
                label = f"Адмін скасував ({action.split(':')[1]})"
            else:
                label = action_map.get(action, action)

            hall = conn.execute(
                "SELECT name FROM halls WHERE hall_id = ?", (r["hall_id"],)
            ).fetchone()
            hall_name = hall["name"] if hall else r["hall_id"]

            result.append({
                "timestamp": r["timestamp"],
                "username":  r["username"],
                "action":    label,
                "hall_name": hall_name,
                "seat":      r["seat"],
                "amount":    r["amount"]
            })
    return result


def db_get_refund_preview(
    session: dict, hall_id: str, seat: str = None
) -> tuple[float, str]:
    with get_connection() as conn:
        hall_row = conn.execute(
            "SELECT showtime FROM halls WHERE hall_id = ?", (hall_id,)
        ).fetchone()
        if not hall_row:
            return 0.0, "Зал не знайдено"

        user_id = _get_user_row_id(conn, session["username"])

        if seat:
            row = conn.execute(
                """SELECT booked_at, price_paid FROM bookings
                   WHERE user_id = ? AND hall_id = (
                       SELECT id FROM halls WHERE hall_id = ?
                   ) AND seat = ? AND status = 'active'""",
                (user_id, hall_id, str(seat))
            ).fetchone()
        else:
            row = conn.execute(
                """SELECT booked_at, price_paid FROM bookings
                   WHERE user_id = ? AND hall_id = (
                       SELECT id FROM halls WHERE hall_id = ?
                   ) AND status = 'active' LIMIT 1""",
                (user_id, hall_id)
            ).fetchone()

    if not row:
        return 0.0, "Активне бронювання не знайдено"

    return calculate_refund(row["booked_at"], hall_row["showtime"], row["price_paid"])

# ================== ВНУТРІШНІЙ ЛОГ ==================

def _db_log(conn, username: str, hall_id: str,
            seat: str, action: str, amount: float = 0.0):
    user_id = _get_user_row_id(conn, username)
    conn.execute(
        """INSERT INTO booking_log
           (user_id, hall_id, seat, action, timestamp, amount)
           VALUES (?,?,?,?,?,?)""",
        (user_id, hall_id, seat, action, _now(), amount)
    )