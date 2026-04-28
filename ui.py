# ui.py

import customtkinter as ctk
from tkinter import messagebox
from logic import (
    init_db, try_login, reserve_seat, cancel_my_reservation,
    admin_cancel_reservation, get_hall_seats_for_user,
    get_hall_seats, get_halls_info, get_my_bookings,
    get_all_bookings, get_statistics, get_log_entries,
    get_users_list, register_user, change_password,
    get_balance, get_refund_preview, set_showtime, SEAT_PRICE
)

# ================== КОЛЬОРИ ==================

COLORS = {
    "bg":           "#0f0f0f",
    "bg_card":      "#1a1a1a",
    "bg_input":     "#222222",
    "red":          "#e03030",
    "red_hover":    "#c02020",
    "red_dark":     "#3a1010",
    "green":        "#2ecc71",
    "green_hover":  "#27ae60",
    "green_dark":   "#0d3320",
    "blue":         "#3498db",
    "blue_hover":   "#2980b9",
    "blue_dark":    "#0d2233",
    "gold":         "#f0c040",
    "gold_dark":    "#2a2000",
    "gray":         "#2a2a2a",
    "gray_light":   "#3a3a3a",
    "text":         "#f0f0f0",
    "text_muted":   "#888888",
    "seat_free":    "#2ecc71",
    "seat_mine":    "#3498db",
    "seat_taken":   "#e03030",
}

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# ================== БАЗОВИЙ КЛАС ==================

class Screen(ctk.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent, fg_color=COLORS["bg"], corner_radius=0)
        self.app = app

# ================== ЕКРАН ВХОДУ ==================

class LoginScreen(Screen):
    def __init__(self, parent, app):
        super().__init__(parent, app)
        self._build()

    def _build(self):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        card = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                            corner_radius=16, width=400, height=500)
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        ctk.CTkLabel(card, text="🎬", font=("Arial", 52),
                     text_color=COLORS["red"]).pack(pady=(40, 0))
        ctk.CTkLabel(card, text="КІНОТЕАТР",
                     font=("Arial", 26, "bold"),
                     text_color=COLORS["text"]).pack(pady=(4, 0))
        ctk.CTkLabel(card, text="Система бронювання квитків",
                     font=("Arial", 13),
                     text_color=COLORS["text_muted"]).pack(pady=(2, 24))

        ctk.CTkLabel(card, text="Логін", font=("Arial", 13),
                     text_color=COLORS["text_muted"],
                     anchor="w").pack(padx=40, fill="x")
        self.username_entry = ctk.CTkEntry(
            card, height=42, corner_radius=8,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["gray_light"],
            text_color=COLORS["text"], font=("Arial", 14),
            placeholder_text="Введіть логін"
        )
        self.username_entry.pack(padx=40, fill="x", pady=(4, 12))

        ctk.CTkLabel(card, text="Пароль", font=("Arial", 13),
                     text_color=COLORS["text_muted"],
                     anchor="w").pack(padx=40, fill="x")
        self.password_entry = ctk.CTkEntry(
            card, height=42, corner_radius=8,
            fg_color=COLORS["bg_input"],
            border_color=COLORS["gray_light"],
            text_color=COLORS["text"], font=("Arial", 14),
            placeholder_text="Введіть пароль", show="●"
        )
        self.password_entry.pack(padx=40, fill="x", pady=(4, 8))

        self.error_label = ctk.CTkLabel(
            card, text="", font=("Arial", 12),
            text_color=COLORS["red"]
        )
        self.error_label.pack()

        ctk.CTkButton(
            card, text="Увійти", height=44, corner_radius=8,
            font=("Arial", 15, "bold"),
            fg_color=COLORS["red"], hover_color=COLORS["red_hover"],
            text_color="white", command=self._login
        ).pack(padx=40, fill="x", pady=(8, 0))

        ctk.CTkLabel(
            card,
            text="admin / admin123   •   user1 / pass123",
            font=("Arial", 11), text_color=COLORS["text_muted"]
        ).pack(pady=(16, 0))

        self.password_entry.bind("<Return>", lambda e: self._login())
        self.username_entry.bind("<Return>",
                                 lambda e: self.password_entry.focus())

    def _login(self):
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        if not username or not password:
            self.error_label.configure(text="Заповніть всі поля")
            return
        session = try_login(username, password)
        if session:
            self.destroy()
            HallSelectScreen(self.master, self.app, session)
        else:
            self.error_label.configure(text="Невірний логін або пароль")
            self.password_entry.delete(0, "end")

# ================== ЕКРАН ВИБОРУ ЗАЛУ ==================

class HallSelectScreen(Screen):
    def __init__(self, parent, app, session):
        super().__init__(parent, app)
        self.session = session
        self._build()

    def _build(self):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self._build_header()

        ctk.CTkLabel(self, text="Оберіть зал",
                     font=("Arial", 22, "bold"),
                     text_color=COLORS["text"]).pack(pady=(40, 4))
        ctk.CTkLabel(
            self,
            text=f"Ціна квитка: {SEAT_PRICE:.0f} грн",
            font=("Arial", 14), text_color=COLORS["gold"]
        ).pack(pady=(0, 24))

        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack()
        for hall in get_halls_info():
            self._hall_card(cards_frame, hall)

    def _build_header(self):
        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                              corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🎬  КІНОТЕАТР",
                     font=("Arial", 20, "bold"),
                     text_color=COLORS["red"]).pack(side="left", padx=24)

        balance = get_balance(self.session["username"])
        role_icon = "🔧" if self.session["role"] == "admin" else "👤"

        ctk.CTkLabel(
            header,
            text=f"💰 {balance:.2f} грн",
            font=("Arial", 13, "bold"),
            text_color=COLORS["gold"]
        ).pack(side="right", padx=16)

        ctk.CTkLabel(
            header,
            text=f"{role_icon}  {self.session['full_name']}",
            font=("Arial", 13), text_color=COLORS["text_muted"]
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            header, text="Вийти", width=80, height=32,
            corner_radius=6, font=("Arial", 12),
            fg_color=COLORS["gray"], hover_color=COLORS["gray_light"],
            text_color=COLORS["text"], command=self._logout
        ).pack(side="right", padx=8, pady=16)

    def _hall_card(self, parent, hall: dict):
        from datetime import datetime
        pct = hall["percent"]
        color      = COLORS["green"] if pct < 50 else COLORS["blue"] if pct < 85 else COLORS["red"]
        color_dark = COLORS["green_dark"] if pct < 50 else COLORS["blue_dark"] if pct < 85 else COLORS["red_dark"]

        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_card"],
                            corner_radius=14, width=340, height=200,
                            border_width=1, border_color=COLORS["gray_light"])
        card.pack(side="left", padx=16, pady=8)
        card.pack_propagate(False)

        ctk.CTkLabel(card, text=hall["name"],
                     font=("Arial", 17, "bold"),
                     text_color=COLORS["text"]).pack(pady=(20, 2))

        try:
            show_dt = datetime.strptime(hall["showtime"], "%Y-%m-%d %H:%M:%S")
            show_str = show_dt.strftime("%d.%m.%Y  %H:%M")
        except Exception:
            show_str = hall["showtime"]

        ctk.CTkLabel(card, text=f"🕐 Сеанс: {show_str}",
                     font=("Arial", 12),
                     text_color=COLORS["text_muted"]).pack()

        bar_frame = ctk.CTkFrame(card, fg_color=COLORS["gray"],
                                 corner_radius=6, height=10, width=260)
        bar_frame.pack(pady=6)
        bar_frame.pack_propagate(False)
        fill_w = max(4, int(260 * pct / 100))
        ctk.CTkFrame(bar_frame, fg_color=color, corner_radius=6,
                     height=10, width=fill_w).place(x=0, y=0)

        ctk.CTkLabel(
            card,
            text=f"Зайнято: {hall['busy']}  •  Вільно: {hall['free']}  •  {pct}%",
            font=("Arial", 12), text_color=COLORS["text_muted"]
        ).pack()

        ctk.CTkButton(
            card, text="Відкрити зал →", height=36, corner_radius=8,
            font=("Arial", 13, "bold"),
            fg_color=color_dark, hover_color=color,
            text_color=color, border_width=1, border_color=color,
            command=lambda hid=hall["hall_id"]: self._open_hall(hid)
        ).pack(pady=(8, 0), padx=24, fill="x")

    def _open_hall(self, hall_id):
        self.destroy()
        MainScreen(self.master, self.app, self.session, hall_id)

    def _logout(self):
        self.destroy()
        LoginScreen(self.master, self.app)
        
# ================== ГОЛОВНИЙ ЕКРАН ==================

class MainScreen(Screen):
    def __init__(self, parent, app, session, hall_id):
        super().__init__(parent, app)
        self.session = session
        self.hall_id = hall_id
        self._build()

    def _build(self):
        self.place(relx=0, rely=0, relwidth=1, relheight=1)

        header = ctk.CTkFrame(self, fg_color=COLORS["bg_card"],
                              corner_radius=0, height=64)
        header.pack(fill="x")
        header.pack_propagate(False)

        ctk.CTkLabel(header, text="🎬  КІНОТЕАТР",
                     font=("Arial", 20, "bold"),
                     text_color=COLORS["red"]).pack(side="left", padx=24)

        # Баланс в хедері
        self.balance_label = ctk.CTkLabel(
            header, text="",
            font=("Arial", 13, "bold"),
            text_color=COLORS["gold"]
        )
        self.balance_label.pack(side="right", padx=16)
        self._refresh_balance()

        role_icon = "🔧" if self.session["role"] == "admin" else "👤"
        ctk.CTkLabel(
            header,
            text=f"{role_icon}  {self.session['full_name']}",
            font=("Arial", 13), text_color=COLORS["text_muted"]
        ).pack(side="right", padx=4)

        ctk.CTkButton(
            header, text="← Зали", width=90, height=32,
            corner_radius=6, font=("Arial", 12),
            fg_color=COLORS["gray"], hover_color=COLORS["gray_light"],
            text_color=COLORS["text"], command=self._back_to_halls
        ).pack(side="right", padx=8, pady=16)

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)

        self.sidebar = ctk.CTkFrame(content, fg_color=COLORS["bg_card"],
                                    corner_radius=12, width=220)
        self.sidebar.pack(side="left", fill="y", padx=(0, 12))
        self.sidebar.pack_propagate(False)

        self.right_panel = ctk.CTkFrame(content, fg_color="transparent")
        self.right_panel.pack(side="left", fill="both", expand=True)

        self._build_sidebar()
        self._show_hall_panel()

    def _refresh_balance(self):
        balance = get_balance(self.session["username"])
        self.balance_label.configure(text=f"💰 {balance:.2f} грн")

    def _build_sidebar(self):
        halls_info = get_halls_info()
        hall_name = next(
            (h["name"] for h in halls_info if h["hall_id"] == self.hall_id), ""
        )

        ctk.CTkLabel(
            self.sidebar, text=hall_name,
            font=("Arial", 14, "bold"),
            text_color=COLORS["text"], wraplength=190
        ).pack(pady=(20, 4), padx=12)

        ctk.CTkLabel(
            self.sidebar,
            text=f"Квиток: {SEAT_PRICE:.0f} грн",
            font=("Arial", 12), text_color=COLORS["gold"]
        ).pack(pady=(0, 12), padx=12)

        ctk.CTkFrame(self.sidebar, fg_color=COLORS["gray"],
                     height=1).pack(fill="x", padx=12)

        buttons = [
            ("🪑  Схема залу",       self._show_hall_panel,      COLORS["blue"]),
            ("✅  Забронювати",      self._show_reserve_panel,   COLORS["green"]),
            ("❌  Скасувати бронь",  self._show_cancel_panel,    COLORS["red"]),
            ("📋  Мої бронювання",  self._show_my_bookings,     COLORS["blue"]),
            ("📊  Статистика",       self._show_statistics,      COLORS["blue"]),
            ("🔑  Змінити пароль",  self._show_change_password, COLORS["gray_light"]),
        ]

        if self.session["role"] == "admin":
            buttons += [
                ("─── Адмін ─────────", None, None),
                ("👥  Всі бронювання", self._show_all_bookings,   COLORS["blue"]),
                ("🚫  Скас. будь-яку", self._show_admin_cancel,   COLORS["red"]),
                ("🕐  Час сеансу",     self._show_set_showtime,   COLORS["gold"]),
                ("📜  Журнал дій",     self._show_log,            COLORS["blue"]),
                ("👤  Користувачі",    self._show_users,          COLORS["blue"]),
                ("➕  Новий юзер",     self._show_register,       COLORS["green"]),
            ]

        for text, cmd, color in buttons:
            if cmd is None:
                ctk.CTkLabel(
                    self.sidebar, text=text, font=("Arial", 10),
                    text_color=COLORS["text_muted"]
                ).pack(pady=(12, 2), padx=12, anchor="w")
                continue
            ctk.CTkButton(
                self.sidebar, text=text, height=38,
                corner_radius=8, anchor="w", font=("Arial", 13),
                fg_color="transparent", hover_color=COLORS["gray"],
                text_color=color, command=cmd
            ).pack(fill="x", padx=8, pady=2)

    def _clear_right(self):
        for w in self.right_panel.winfo_children():
            w.destroy()

    def _panel_title(self, title: str):
        ctk.CTkLabel(
            self.right_panel, text=title,
            font=("Arial", 20, "bold"),
            text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 16))

    # ================== СХЕМА ЗАЛУ ==================

    def _show_hall_panel(self):
        self._clear_right()
        self._panel_title("🪑  Схема залу")

        legend = ctk.CTkFrame(self.right_panel, fg_color="transparent")
        legend.pack(anchor="w", pady=(0, 12))
        for color, label in [
            (COLORS["seat_free"],  "Вільно"),
            (COLORS["seat_mine"],  "Ваше"),
            (COLORS["seat_taken"], "Зайнято"),
        ]:
            ctk.CTkFrame(legend, fg_color=color, width=14,
                         height=14, corner_radius=3).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(legend, text=label, font=("Arial", 12),
                         text_color=COLORS["text_muted"]).pack(side="left", padx=(0, 16))

        grid_frame = ctk.CTkScrollableFrame(
            self.right_panel, fg_color=COLORS["bg_card"],
            corner_radius=12,
            scrollbar_button_color=COLORS["gray"]
        )
        grid_frame.pack(fill="both", expand=True)

        seats = get_hall_seats_for_user(self.hall_id, self.session)
        cols = 5

        for i, sd in enumerate(seats):
            status = sd["status"]
            seat_num = sd["seat"]

            if status == "free":
                bg, fg, hover = COLORS["green_dark"], COLORS["seat_free"], COLORS["green"]
                cmd = lambda s=seat_num: self._quick_reserve(s)
            elif status == "mine":
                bg, fg, hover = COLORS["blue_dark"], COLORS["seat_mine"], COLORS["blue"]
                cmd = lambda: self._show_cancel_panel()
            else:
                bg, fg, hover = COLORS["red_dark"], COLORS["seat_taken"], COLORS["red_dark"]
                cmd = None

            label_text = seat_num
            font_size = 14
            if status == "taken" and self.session["role"] == "admin":
                label_text = f"{seat_num}\n{sd['occupant'][:6]}"
                font_size = 11

            ctk.CTkButton(
                grid_frame, text=label_text, width=70, height=58,
                corner_radius=8, font=("Arial", font_size, "bold"),
                fg_color=bg, hover_color=hover,
                text_color=fg, border_width=1, border_color=fg,
                command=cmd if cmd else lambda: None,
                state="normal" if cmd else "disabled"
            ).grid(row=i // cols, column=i % cols, padx=6, pady=6)

    def _quick_reserve(self, seat: str):
        balance = get_balance(self.session["username"])
        if balance < SEAT_PRICE:
            messagebox.showerror(
                "❌ Недостатньо коштів",
                f"Потрібно: {SEAT_PRICE:.0f} грн\nНа балансі: {balance:.2f} грн"
            )
            return
        if not messagebox.askyesno(
            "Підтвердження",
            f"Забронювати місце №{seat}?\nСпишеться: {SEAT_PRICE:.0f} грн"
        ):
            return
        success, msg = reserve_seat(self.session, self.hall_id, seat)
        if success:
            messagebox.showinfo("✅ Успішно", msg)
            self._refresh_balance()
        else:
            messagebox.showerror("❌ Помилка", msg)
        self._show_hall_panel()

    # ================== БРОНЮВАННЯ ==================

    def _show_reserve_panel(self):
        self._clear_right()
        self._panel_title("✅  Забронювати місце")

        # Картка балансу
        balance_card = ctk.CTkFrame(self.right_panel,
                                    fg_color=COLORS["gold_dark"],
                                    corner_radius=10)
        balance_card.pack(fill="x", pady=(0, 12))
        balance = get_balance(self.session["username"])
        ctk.CTkLabel(
            balance_card,
            text=f"💰 Баланс: {balance:.2f} грн    |    Ціна квитка: {SEAT_PRICE:.0f} грн",
            font=("Arial", 14, "bold"), text_color=COLORS["gold"]
        ).pack(pady=12)

        card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                            corner_radius=12)
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="Номер місця:", font=("Arial", 14),
                     text_color=COLORS["text_muted"]).pack(anchor="w", padx=24, pady=(20, 4))

        entry = ctk.CTkEntry(
            card, height=44, corner_radius=8,
            fg_color=COLORS["bg_input"], border_color=COLORS["gray_light"],
            text_color=COLORS["text"], font=("Arial", 15),
            placeholder_text="Введіть номер місця"
        )
        entry.pack(padx=24, fill="x", pady=(0, 8))

        result_label = ctk.CTkLabel(card, text="", font=("Arial", 13))
        result_label.pack(pady=(0, 4))

        def do_reserve():
            seat = entry.get().strip()
            if not messagebox.askyesno(
                "Підтвердження",
                f"Забронювати місце №{seat}?\nСпишеться: {SEAT_PRICE:.0f} грн"
            ):
                return
            success, msg = reserve_seat(self.session, self.hall_id, seat)
            color = COLORS["green"] if success else COLORS["red"]
            result_label.configure(
                text=f"{'✅' if success else '❌'}  {msg}", text_color=color
            )
            if success:
                entry.delete(0, "end")
                self._refresh_balance()
                # Оновлюємо відображення балансу
                new_balance = get_balance(self.session["username"])
                balance_card_label = balance_card.winfo_children()[0]
                balance_card_label.configure(
                    text=f"💰 Баланс: {new_balance:.2f} грн    |    Ціна квитка: {SEAT_PRICE:.0f} грн"
                )

        ctk.CTkButton(
            card, text="Забронювати", height=44, corner_radius=8,
            font=("Arial", 14, "bold"),
            fg_color=COLORS["green"], hover_color=COLORS["green_hover"],
            text_color="white", command=do_reserve
        ).pack(padx=24, fill="x", pady=(0, 20))

        entry.bind("<Return>", lambda e: do_reserve())

        ctk.CTkLabel(self.right_panel, text="Доступні місця:",
                     font=("Arial", 14),
                     text_color=COLORS["text_muted"]).pack(anchor="w", pady=(8, 4))
        self._mini_hall_grid(self.right_panel)

    # ================== СКАСУВАННЯ ==================

    def _show_cancel_panel(self):
        self._clear_right()
        self._panel_title("❌  Скасувати бронювання")

        bookings = get_my_bookings(self.session)
        hall_bookings = [b for b in bookings
                        if b["hall_id"] == self.hall_id
                        and b["status"] == "active"]

        if not hall_bookings:
            card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                                corner_radius=12)
            card.pack(fill="x")
            ctk.CTkLabel(
                card,
                text="У вас немає активних бронювань у цьому залі",
                font=("Arial", 14), text_color=COLORS["text_muted"]
            ).pack(pady=40)
            return

        ctk.CTkLabel(
            self.right_panel,
            text=f"Ваші місця в цьому залі ({len(hall_bookings)}):",
            font=("Arial", 14), text_color=COLORS["text_muted"]
        ).pack(anchor="w", pady=(0, 8))

        self.result_label = ctk.CTkLabel(
            self.right_panel, text="", font=("Arial", 13)
        )

        for b in hall_bookings:
            refund_amount, refund_explanation = get_refund_preview(
                self.session, self.hall_id, b["seat"]
            )
            refund_color = COLORS["green"] if refund_amount > 0 else COLORS["red"]

            card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                                corner_radius=12)
            card.pack(fill="x", pady=4)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=16, pady=(14, 4))

            ctk.CTkLabel(
                info, text=f"Місце №{b['seat']}",
                font=("Arial", 16, "bold"),
                text_color=COLORS["blue"]
            ).pack(side="left")

            ctk.CTkLabel(
                info, text=f"Сплачено: {b['price_paid']:.0f} грн",
                font=("Arial", 13), text_color=COLORS["gold"]
            ).pack(side="left", padx=16)

            ctk.CTkLabel(
                info, text=f"Заброньовано: {b['booked_at']}",
                font=("Arial", 11), text_color=COLORS["text_muted"]
            ).pack(side="left")

            refund_frame = ctk.CTkFrame(card, fg_color=COLORS["gray"],
                                        corner_radius=6)
            refund_frame.pack(fill="x", padx=16, pady=(4, 8))

            ctk.CTkLabel(
                refund_frame,
                text=f"💡 {refund_explanation}",
                font=("Arial", 13), text_color=refund_color
            ).pack(side="left", padx=12, pady=8)

            ctk.CTkButton(
                card,
                text=f"Скасувати місце №{b['seat']}",
                height=38, corner_radius=8,
                font=("Arial", 13, "bold"),
                fg_color=COLORS["red"], hover_color=COLORS["red_hover"],
                text_color="white",
                command=lambda seat=b["seat"], refund=refund_amount: self._do_cancel(seat, refund)
            ).pack(padx=16, fill="x", pady=(0, 14))

        self.result_label.pack(pady=4)


    def _do_cancel(self, seat: str, refund_amount: float):
        if refund_amount == 0:
            confirm_text = (
                f"Скасувати місце №{seat}?\n"
                f"⚠️ Повернення коштів неможливе!"
            )
        else:
            confirm_text = (
                f"Скасувати місце №{seat}?\n"
                f"На баланс повернеться: {refund_amount:.2f} грн"
            )
        if not messagebox.askyesno("Підтвердження", confirm_text):
            return

        success, msg = cancel_my_reservation(self.session, self.hall_id, seat)
        color = COLORS["green"] if success else COLORS["red"]
        self.result_label.configure(
            text=f"{'✅' if success else '❌'}  {msg}",
            text_color=color
        )
        if success:
            self._refresh_balance()
            self.after(1200, self._show_cancel_panel)

    # ================== МОЇ БРОНЮВАННЯ ==================

    def _show_my_bookings(self):
        self._clear_right()
        self._panel_title("📋  Мої бронювання")

        balance = get_balance(self.session["username"])
        ctk.CTkLabel(
            self.right_panel,
            text=f"💰 Поточний баланс: {balance:.2f} грн",
            font=("Arial", 14, "bold"), text_color=COLORS["gold"]
        ).pack(anchor="w", pady=(0, 12))

        bookings = get_my_bookings(self.session)

        if not bookings:
            card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                                corner_radius=12)
            card.pack(fill="x")
            ctk.CTkLabel(card, text="У вас немає бронювань",
                         font=("Arial", 14),
                         text_color=COLORS["text_muted"]).pack(pady=40)
            return

        for b in bookings:
            is_active = b["status"] == "active"
            bg = COLORS["bg_card"] if is_active else COLORS["gray"]

            row = ctk.CTkFrame(self.right_panel, fg_color=bg,
                               corner_radius=8, height=60)
            row.pack(fill="x", pady=4)
            row.pack_propagate(False)

            status_color = COLORS["green"] if is_active else COLORS["text_muted"]
            status_text  = "● Активна" if is_active else "✕ Скасована"

            ctk.CTkLabel(row, text=f"🎬  {b['hall_name']}",
                         font=("Arial", 13),
                         text_color=COLORS["text"]).pack(side="left", padx=16)
            ctk.CTkLabel(row, text=f"Місце №{b['seat']}",
                         font=("Arial", 14, "bold"),
                         text_color=COLORS["blue"]).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=f"{b['price_paid']:.0f} грн",
                         font=("Arial", 12),
                         text_color=COLORS["gold"]).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=status_text,
                         font=("Arial", 12),
                         text_color=status_color).pack(side="right", padx=16)

    # ================== СТАТИСТИКА ==================

    def _show_statistics(self):
        self._clear_right()
        self._panel_title("📊  Статистика")

        from datetime import datetime
        for hall in get_statistics():
            card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                                corner_radius=12)
            card.pack(fill="x", pady=6)

            try:
                show_dt  = datetime.strptime(hall["showtime"], "%Y-%m-%d %H:%M:%S")
                show_str = show_dt.strftime("%d.%m.%Y  %H:%M")
            except Exception:
                show_str = hall.get("showtime", "—")

            ctk.CTkLabel(card, text=hall["name"],
                         font=("Arial", 15, "bold"),
                         text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(16, 2))
            ctk.CTkLabel(card, text=f"🕐 Сеанс: {show_str}",
                         font=("Arial", 12),
                         text_color=COLORS["text_muted"]).pack(anchor="w", padx=20)

            bar_bg = ctk.CTkFrame(card, fg_color=COLORS["gray"],
                                  corner_radius=6, height=14)
            bar_bg.pack(fill="x", padx=20, pady=6)
            bar_bg.pack_propagate(False)

            pct   = hall["percent"]
            color = COLORS["green"] if pct < 50 else COLORS["blue"] if pct < 85 else COLORS["red"]

            def draw_bar(bg=bar_bg, p=pct, c=color):
                w    = bg.winfo_width()
                fill = max(6, int(w * p / 100))
                ctk.CTkFrame(bg, fg_color=c, corner_radius=6,
                             height=14, width=fill).place(x=0, y=0)
            card.after(50, draw_bar)

            info = ctk.CTkFrame(card, fg_color="transparent")
            info.pack(fill="x", padx=20, pady=(4, 16))

            revenue = hall["busy"] * SEAT_PRICE
            for label, value, col in [
                ("Всього місць", hall["total"],       COLORS["text"]),
                ("Зайнято",      hall["busy"],        COLORS["red"]),
                ("Вільно",       hall["free"],        COLORS["green"]),
                ("Заповненість", f"{pct}%",           color),
                ("Виручка",      f"{revenue:.0f} ₴",  COLORS["gold"]),
            ]:
                f = ctk.CTkFrame(info, fg_color=COLORS["gray"],
                                 corner_radius=8, width=110, height=60)
                f.pack(side="left", padx=4)
                f.pack_propagate(False)
                ctk.CTkLabel(f, text=str(value), font=("Arial", 18, "bold"),
                             text_color=col).pack(expand=True)
                ctk.CTkLabel(f, text=label, font=("Arial", 10),
                             text_color=COLORS["text_muted"]).pack(pady=(0, 6))

    # ================== ЗМІНА ПАРОЛЯ ==================

    def _show_change_password(self):
        self._clear_right()
        self._panel_title("🔑  Змінити пароль")

        card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                            corner_radius=12)
        card.pack(fill="x")
        entries = {}

        for key, label in [("old", "Поточний пароль"),
                            ("new", "Новий пароль"),
                            ("confirm", "Підтвердіть пароль")]:
            ctk.CTkLabel(card, text=label, font=("Arial", 13),
                         text_color=COLORS["text_muted"],
                         anchor="w").pack(padx=24, fill="x", pady=(16, 2))
            e = ctk.CTkEntry(
                card, height=42, corner_radius=8, show="●",
                fg_color=COLORS["bg_input"],
                border_color=COLORS["gray_light"],
                text_color=COLORS["text"], font=("Arial", 14)
            )
            e.pack(padx=24, fill="x")
            entries[key] = e

        result_label = ctk.CTkLabel(card, text="", font=("Arial", 13))
        result_label.pack(pady=8)

        def do_change():
            if entries["new"].get() != entries["confirm"].get():
                result_label.configure(text="❌  Паролі не збігаються",
                                       text_color=COLORS["red"])
                return
            success, msg = change_password(
                self.session["username"],
                entries["old"].get(),
                entries["new"].get()
            )
            result_label.configure(
                text=f"{'✅' if success else '❌'}  {msg}",
                text_color=COLORS["green"] if success else COLORS["red"]
            )
            if success:
                for e in entries.values():
                    e.delete(0, "end")

        ctk.CTkButton(
            card, text="Змінити пароль", height=44, corner_radius=8,
            font=("Arial", 14, "bold"),
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            text_color="white", command=do_change
        ).pack(padx=24, fill="x", pady=(0, 24))

    # ================== АДМІН: ВСІ БРОНЮВАННЯ ==================

    def _show_all_bookings(self):
        self._clear_right()
        self._panel_title("👥  Всі бронювання")

        table = ctk.CTkScrollableFrame(
            self.right_panel, fg_color=COLORS["bg_card"],
            corner_radius=12, scrollbar_button_color=COLORS["gray"]
        )
        table.pack(fill="both", expand=True)

        headers = ["Зал", "Місце", "Логін", "Ім'я", "Сплачено", "Час броні"]
        widths   = [180,    70,     110,     160,    90,          140]

        for col, (h, w) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(table, text=h, width=w,
                         font=("Arial", 12, "bold"),
                         text_color=COLORS["text_muted"],
                         anchor="w").grid(row=0, column=col,
                                          padx=8, pady=(12, 4), sticky="w")

        ctk.CTkFrame(table, fg_color=COLORS["gray"], height=1).grid(
            row=1, column=0, columnspan=6, sticky="ew", padx=8, pady=2
        )

        bookings = get_all_bookings()
        if not bookings:
            ctk.CTkLabel(table, text="Немає активних бронювань",
                         font=("Arial", 14),
                         text_color=COLORS["text_muted"]).grid(
                row=2, column=0, columnspan=6, pady=40)
            return

        for i, b in enumerate(bookings):
            bg = COLORS["gray"] if i % 2 == 0 else "transparent"
            row_data   = [b["hall_name"], f"№{b['seat']}", b["username"],
                          b["full_name"], f"{b['price_paid']:.0f} грн",
                          b["booked_at"]]
            row_colors = [COLORS["text"], COLORS["blue"], COLORS["text"],
                          COLORS["text_muted"], COLORS["gold"], COLORS["text_muted"]]
            for col, (val, w, c) in enumerate(zip(row_data, widths, row_colors)):
                ctk.CTkLabel(table, text=val, width=w,
                             font=("Arial", 12), text_color=c,
                             fg_color=bg, corner_radius=4,
                             anchor="w").grid(row=i + 2, column=col,
                                              padx=8, pady=3, sticky="w")

    # ================== АДМІН: СКАСУВАННЯ ==================

    def _show_admin_cancel(self):
        self._clear_right()
        self._panel_title("🚫  Скасувати бронювання користувача")

        card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                            corner_radius=12)
        card.pack(fill="x", pady=(0, 12))

        ctk.CTkLabel(card, text="Логін користувача:", font=("Arial", 13),
                    text_color=COLORS["text_muted"],
                    anchor="w").pack(padx=24, fill="x", pady=(20, 4))

        entry = ctk.CTkEntry(
            card, height=44, corner_radius=8,
            fg_color=COLORS["bg_input"], border_color=COLORS["gray_light"],
            text_color=COLORS["text"], font=("Arial", 15),
            placeholder_text="Введіть логін"
        )
        entry.pack(padx=24, fill="x")

        # Фрейм для вибору місця (з'являється після пошуку)
        seat_frame = ctk.CTkFrame(card, fg_color="transparent")
        seat_frame.pack(fill="x", padx=24, pady=(8, 0))

        result_label = ctk.CTkLabel(card, text="", font=("Arial", 13))
        result_label.pack(pady=8)

        def search_bookings():
            # Очищаємо попередній вибір місця
            for w in seat_frame.winfo_children():
                w.destroy()

            target = entry.get().strip().lower()
            if not target:
                result_label.configure(text="❌  Введіть логін",
                                    text_color=COLORS["red"])
                return

            # Шукаємо всі бронювання користувача в цьому залі
            all_bookings = get_all_bookings()
            user_bookings = [
                b for b in all_bookings
                if b["username"] == target and b["hall_id"] == self.hall_id
            ]

            if not user_bookings:
                result_label.configure(
                    text=f"❌  Користувач '{target}' не має бронювань у цьому залі",
                    text_color=COLORS["red"]
                )
                return

            result_label.configure(
                text=f"✅  Знайдено бронювань: {len(user_bookings)}",
                text_color=COLORS["green"]
            )

            ctk.CTkLabel(seat_frame, text="Оберіть місце для скасування:",
                        font=("Arial", 13),
                        text_color=COLORS["text_muted"]).pack(anchor="w", pady=(4, 6))

            for b in user_bookings:
                row = ctk.CTkFrame(seat_frame, fg_color=COLORS["gray"],
                               corner_radius=8, height=44)
                row.pack(fill="x", pady=3)
                row.pack_propagate(False)

                ctk.CTkLabel(row, text=f"Місце №{b['seat']}",
                            font=("Arial", 13, "bold"),
                            text_color=COLORS["blue"]).pack(side="left", padx=12)
                ctk.CTkLabel(row, text=f"Сплачено: {b['price_paid']:.0f} грн",
                            font=("Arial", 12),
                            text_color=COLORS["gold"]).pack(side="left", padx=8)
                ctk.CTkLabel(row, text=b["booked_at"],
                            font=("Arial", 11),
                            text_color=COLORS["text_muted"]).pack(side="left", padx=4)

                ctk.CTkButton(
                    row, text="Скасувати", width=90, height=28,
                    corner_radius=6, font=("Arial", 12, "bold"),
                    fg_color=COLORS["red"], hover_color=COLORS["red_hover"],
                    text_color="white",
                    command=lambda t=target, s=b["seat"]: do_admin_cancel(t, s)
                ).pack(side="right", padx=8)

        def do_admin_cancel(target: str, seat: str):
            if not messagebox.askyesno(
                "Підтвердження",
                f"Скасувати місце №{seat} користувача '{target}'?\n"
                f"Кошти будуть повернені згідно правил."
            ):
                return
            success, msg = admin_cancel_reservation(
                self.session, self.hall_id, target, seat)
            result_label.configure(
                text=f"{'✅' if success else '❌'}  {msg}",
                text_color=COLORS["green"] if success else COLORS["red"]
            )
            if success:
                search_bookings()

        ctk.CTkButton(
            card, text="🔍 Знайти бронювання", height=40,
            corner_radius=8, font=("Arial", 13, "bold"),
            fg_color=COLORS["blue"], hover_color=COLORS["blue_hover"],
            text_color="white", command=search_bookings
        ).pack(padx=24, fill="x", pady=(0, 20))

        entry.bind("<Return>", lambda e: search_bookings())

        ctk.CTkLabel(self.right_panel, text="Всі активні бронювання в цьому залі:",
                    font=("Arial", 13),
                    text_color=COLORS["text_muted"]).pack(anchor="w", pady=(4, 4))
        self._bookings_mini_table()

    def _bookings_mini_table(self):
        bookings = [b for b in get_all_bookings()
                    if b["hall_id"] == self.hall_id]
        frame = ctk.CTkScrollableFrame(
            self.right_panel, fg_color=COLORS["bg_card"],
            corner_radius=10, height=200,
            scrollbar_button_color=COLORS["gray"]
        )
        frame.pack(fill="x")
        if not bookings:
            ctk.CTkLabel(frame, text="Немає бронювань",
                         font=("Arial", 13),
                         text_color=COLORS["text_muted"]).pack(pady=20)
            return
        for i, b in enumerate(bookings):
            row = ctk.CTkFrame(
                frame,
                fg_color=COLORS["gray"] if i % 2 == 0 else "transparent",
                corner_radius=6, height=36
            )
            row.pack(fill="x", padx=8, pady=2)
            row.pack_propagate(False)
            ctk.CTkLabel(row, text=f"№{b['seat']}",
                         font=("Arial", 13, "bold"),
                         text_color=COLORS["blue"], width=50).pack(side="left", padx=8)
            ctk.CTkLabel(row, text=b["username"],
                         font=("Arial", 13),
                         text_color=COLORS["text"], width=100).pack(side="left", padx=4)
            ctk.CTkLabel(row, text=f"{b['price_paid']:.0f} грн",
                         font=("Arial", 12),
                         text_color=COLORS["gold"]).pack(side="right", padx=12)

    # ================== АДМІН: ЧАС СЕАНСУ ==================

    def _show_set_showtime(self):
        self._clear_right()
        self._panel_title("🕐  Змінити час сеансу")

        card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                            corner_radius=12)
        card.pack(fill="x")

        halls = get_halls_info()
        self.showtime_hall_var = ctk.StringVar(
            value=halls[0]["hall_id"] if halls else ""
        )

        ctk.CTkLabel(card, text="Зал:", font=("Arial", 13),
                    text_color=COLORS["text_muted"],
                    anchor="w").pack(padx=24, fill="x", pady=(20, 4))
        ctk.CTkOptionMenu(
            card,
            values=[h["hall_id"] for h in halls],
            variable=self.showtime_hall_var,
            fg_color=COLORS["bg_input"],
            button_color=COLORS["gray"],
            font=("Arial", 13)
        ).pack(padx=24, fill="x", pady=(0, 12))

        # Вибір дати і часу через окремі поля
        from datetime import datetime, timedelta
        default_dt = datetime.now() + timedelta(hours=6)

        date_row = ctk.CTkFrame(card, fg_color="transparent")
        date_row.pack(fill="x", padx=24, pady=(0, 8))

        # Дата
        ctk.CTkLabel(date_row, text="Дата:", font=("Arial", 13),
                    text_color=COLORS["text_muted"],
                    width=50).pack(side="left")

        day_var   = ctk.StringVar(value=str(default_dt.day))
        month_var = ctk.StringVar(value=str(default_dt.month))
        year_var  = ctk.StringVar(value=str(default_dt.year))

        ctk.CTkOptionMenu(
            date_row, width=70,
            values=[str(i) for i in range(1, 32)],
            variable=day_var,
            fg_color=COLORS["bg_input"], button_color=COLORS["gray"],
            font=("Arial", 13)
        ).pack(side="left", padx=4)

        ctk.CTkLabel(date_row, text=".", font=("Arial", 14),
                    text_color=COLORS["text_muted"]).pack(side="left")

        ctk.CTkOptionMenu(
            date_row, width=70,
            values=[str(i) for i in range(1, 13)],
            variable=month_var,
            fg_color=COLORS["bg_input"], button_color=COLORS["gray"],
            font=("Arial", 13)
        ).pack(side="left", padx=4)

        ctk.CTkLabel(date_row, text=".", font=("Arial", 14),
                    text_color=COLORS["text_muted"]).pack(side="left")

        ctk.CTkOptionMenu(
            date_row, width=90,
            values=[str(datetime.now().year + i) for i in range(3)],
            variable=year_var,
            fg_color=COLORS["bg_input"], button_color=COLORS["gray"],
            font=("Arial", 13)
        ).pack(side="left", padx=4)

        # Час
        time_row = ctk.CTkFrame(card, fg_color="transparent")
        time_row.pack(fill="x", padx=24, pady=(0, 12))

        ctk.CTkLabel(time_row, text="Час:", font=("Arial", 13),
                    text_color=COLORS["text_muted"],
                    width=50).pack(side="left")

        hour_var   = ctk.StringVar(value=str(default_dt.hour))
        minute_var = ctk.StringVar(value="00")

        ctk.CTkOptionMenu(
            time_row, width=70,
            values=[f"{i:02d}" for i in range(24)],
            variable=hour_var,
            fg_color=COLORS["bg_input"], button_color=COLORS["gray"],
            font=("Arial", 13)
        ).pack(side="left", padx=4)

        ctk.CTkLabel(time_row, text=":", font=("Arial", 16, "bold"),
                    text_color=COLORS["text_muted"]).pack(side="left")

        ctk.CTkOptionMenu(
            time_row, width=70,
            values=["00", "15", "30", "45"],
            variable=minute_var,
            fg_color=COLORS["bg_input"], button_color=COLORS["gray"],
            font=("Arial", 13)
        ).pack(side="left", padx=4)

        # Прев'ю результату
        preview_label = ctk.CTkLabel(card, text="", font=("Arial", 13),
                                    text_color=COLORS["text_muted"])
        preview_label.pack(padx=24, anchor="w")

        def update_preview(*args):
            try:
                dt = datetime(
                    int(year_var.get()), int(month_var.get()), int(day_var.get()),
                    int(hour_var.get()), int(minute_var.get())
                )
                preview_label.configure(
                    text=f"📅 Буде збережено: {dt.strftime('%d.%m.%Y  %H:%M')}"
                )
            except ValueError:
                preview_label.configure(text="⚠️  Невірна дата")

        for var in [day_var, month_var, year_var, hour_var, minute_var]:
            var.trace_add("write", update_preview)
        update_preview()

        result_label = ctk.CTkLabel(card, text="", font=("Arial", 13))
        result_label.pack(pady=4)

        def do_set():
            try:
                dt = datetime(
                    int(year_var.get()), int(month_var.get()), int(day_var.get()),
                    int(hour_var.get()), int(minute_var.get())
                )
            except ValueError:
                result_label.configure(text="❌  Невірна дата",
                                   text_color=COLORS["red"])
                return

            val = dt.strftime("%Y-%m-%d %H:%M:%S")
            success, msg = set_showtime(self.showtime_hall_var.get(), val)
            result_label.configure(
                text=f"{'✅' if success else '❌'}  {msg}",
                text_color=COLORS["green"] if success else COLORS["red"]
            )

        ctk.CTkButton(
            card, text="💾 Зберегти час сеансу", height=44,
            corner_radius=8, font=("Arial", 14, "bold"),
            fg_color=COLORS["gold_dark"], hover_color=COLORS["gray"],
            text_color=COLORS["gold"], border_width=1,
            border_color=COLORS["gold"], command=do_set
        ).pack(padx=24, fill="x", pady=(8, 24))

    # ================== АДМІН: ЖУРНАЛ ==================

    def _show_log(self):
        self._clear_right()
        self._panel_title("📜  Журнал дій")

        table = ctk.CTkScrollableFrame(
            self.right_panel, fg_color=COLORS["bg_card"],
            corner_radius=12, scrollbar_button_color=COLORS["gray"]
        )
        table.pack(fill="both", expand=True)

        headers = ["Час", "Користувач", "Дія", "Зал", "Місце", "Сума"]
        widths   = [140,   110,           180,   160,   60,      90]

        for col, (h, w) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(table, text=h, width=w,
                         font=("Arial", 12, "bold"),
                         text_color=COLORS["text_muted"],
                         anchor="w").grid(row=0, column=col,
                                          padx=8, pady=(12, 4), sticky="w")
        ctk.CTkFrame(table, fg_color=COLORS["gray"], height=1).grid(
            row=1, column=0, columnspan=6, sticky="ew", padx=8, pady=2
        )

        entries = get_log_entries(100)
        if not entries:
            ctk.CTkLabel(table, text="Журнал порожній",
                         font=("Arial", 14),
                         text_color=COLORS["text_muted"]).grid(
                row=2, column=0, columnspan=6, pady=40)
            return

        for i, e in enumerate(entries):
            bg = COLORS["gray"] if i % 2 == 0 else "transparent"
            is_reserve = "Бронювання" in e["action"]
            amount     = e.get("amount", 0)
            amount_str = f"-{abs(amount):.0f}" if amount < 0 else f"+{amount:.0f}"
            amount_col = COLORS["red"] if amount < 0 else COLORS["green"]

            row_data   = [e["timestamp"], e["username"], e["action"],
                          e["hall_name"], f"№{e['seat']}", f"{amount_str} грн"]
            row_colors = [
                COLORS["text_muted"], COLORS["text"],
                COLORS["green"] if is_reserve else COLORS["red"],
                COLORS["text_muted"], COLORS["blue"], amount_col
            ]
            for col, (val, w, c) in enumerate(zip(row_data, widths, row_colors)):
                ctk.CTkLabel(table, text=val, width=w,
                             font=("Arial", 12), text_color=c,
                             fg_color=bg, corner_radius=4,
                             anchor="w").grid(row=i + 2, column=col,
                                              padx=8, pady=3, sticky="w")

    # ================== АДМІН: КОРИСТУВАЧІ ==================

    def _show_users(self):
        self._clear_right()
        self._panel_title("👤  Користувачі")

        table = ctk.CTkScrollableFrame(
            self.right_panel, fg_color=COLORS["bg_card"],
            corner_radius=12, scrollbar_button_color=COLORS["gray"]
        )
        table.pack(fill="both", expand=True)

        headers = ["Логін", "Повне ім'я", "Роль", "Баланс"]
        widths   = [140,     220,           90,     120]

        for col, (h, w) in enumerate(zip(headers, widths)):
            ctk.CTkLabel(table, text=h, width=w,
                         font=("Arial", 12, "bold"),
                         text_color=COLORS["text_muted"],
                         anchor="w").grid(row=0, column=col,
                                          padx=8, pady=(12, 4), sticky="w")
        ctk.CTkFrame(table, fg_color=COLORS["gray"], height=1).grid(
            row=1, column=0, columnspan=4, sticky="ew", padx=8, pady=2
        )

        for i, user in enumerate(get_users_list()):
            bg         = COLORS["gray"] if i % 2 == 0 else "transparent"
            role_color = COLORS["red"] if user["role"] == "admin" else COLORS["blue"]
            balance    = user.get("balance", 0)
            bal_color  = COLORS["gold"] if balance > 0 else COLORS["text_muted"]

            row_data   = [user["username"], user["full_name"],
                          user["role"], f"{balance:.2f} грн"]
            row_colors = [COLORS["text"], COLORS["text_muted"],
                          role_color, bal_color]

            for col, (val, w, c) in enumerate(zip(row_data, widths, row_colors)):
                ctk.CTkLabel(table, text=val, width=w,
                             font=("Arial", 13), text_color=c,
                             fg_color=bg, corner_radius=4,
                             anchor="w").grid(row=i + 2, column=col,
                                              padx=8, pady=4, sticky="w")

    # ================== АДМІН: НОВИЙ КОРИСТУВАЧ ==================

    def _show_register(self):
        self._clear_right()
        self._panel_title("➕  Новий користувач")

        card = ctk.CTkFrame(self.right_panel, fg_color=COLORS["bg_card"],
                            corner_radius=12)
        card.pack(fill="x")
        entries = {}

        for key, label, hidden in [
            ("username",  "Логін",        False),
            ("full_name", "Повне ім'я",    False),
            ("password",  "Пароль",        True),
            ("confirm",   "Підтвердження", True),
        ]:
            ctk.CTkLabel(card, text=label, font=("Arial", 13),
                         text_color=COLORS["text_muted"],
                         anchor="w").pack(padx=24, fill="x", pady=(14, 2))
            e = ctk.CTkEntry(
                card, height=42, corner_radius=8,
                fg_color=COLORS["bg_input"],
                border_color=COLORS["gray_light"],
                text_color=COLORS["text"], font=("Arial", 14),
                show="●" if hidden else ""
            )
            e.pack(padx=24, fill="x")
            entries[key] = e

        ctk.CTkLabel(card, text="Роль:", font=("Arial", 13),
                     text_color=COLORS["text_muted"],
                     anchor="w").pack(padx=24, fill="x", pady=(14, 4))
        role_var = ctk.StringVar(value="user")
        role_frame = ctk.CTkFrame(card, fg_color="transparent")
        role_frame.pack(anchor="w", padx=24)
        for val, label in [("user", "Користувач"), ("admin", "Адміністратор")]:
            ctk.CTkRadioButton(
                role_frame, text=label, variable=role_var, value=val,
                font=("Arial", 13), text_color=COLORS["text"],
                fg_color=COLORS["red"]
            ).pack(side="left", padx=(0, 20))

        result_label = ctk.CTkLabel(card, text="", font=("Arial", 13))
        result_label.pack(pady=8)

        def do_register():
            if entries["password"].get() != entries["confirm"].get():
                result_label.configure(text="❌  Паролі не збігаються",
                                       text_color=COLORS["red"])
                return
            success, msg = register_user(
                entries["username"].get(), entries["password"].get(),
                entries["full_name"].get(), role_var.get()
            )
            result_label.configure(
                text=f"{'✅' if success else '❌'}  {msg}",
                text_color=COLORS["green"] if success else COLORS["red"]
            )
            if success:
                for e in entries.values():
                    e.delete(0, "end")

        ctk.CTkButton(
            card, text="Створити користувача", height=44,
            corner_radius=8, font=("Arial", 14, "bold"),
            fg_color=COLORS["green"], hover_color=COLORS["green_hover"],
            text_color="white", command=do_register
        ).pack(padx=24, fill="x", pady=(0, 24))

    # ================== ДОПОМІЖНІ ==================

    def _mini_hall_grid(self, parent):
        seats = get_hall_seats_for_user(self.hall_id, self.session)
        frame = ctk.CTkScrollableFrame(
            parent, fg_color=COLORS["bg_card"],
            corner_radius=10, height=180,
            scrollbar_button_color=COLORS["gray"]
        )
        frame.pack(fill="x")
        cols = 5
        color_map = {
            "free":  (COLORS["green_dark"], COLORS["seat_free"]),
            "mine":  (COLORS["blue_dark"],  COLORS["seat_mine"]),
            "taken": (COLORS["red_dark"],   COLORS["seat_taken"]),
        }
        for i, sd in enumerate(seats):
            bg, fg = color_map[sd["status"]]
            ctk.CTkLabel(
                frame, text=sd["seat"], width=54, height=46,
                font=("Arial", 13, "bold"),
                text_color=fg, fg_color=bg, corner_radius=6
            ).grid(row=i // cols, column=i % cols, padx=4, pady=4)

    def _back_to_halls(self):
        self.destroy()
        HallSelectScreen(self.master, self.app, self.session)


# ================== ЗАПУСК ==================

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        init_db()
        self.title("🎬 Кінотеатр — Система бронювання")
        self.geometry("1100x720")
        self.minsize(900, 600)
        self.configure(fg_color=COLORS["bg"])
        LoginScreen(self, self)


if __name__ == "__main__":
    init_db()
    app = App()
    app.mainloop()