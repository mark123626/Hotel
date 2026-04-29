import flet as ft
import sqlite3
from datetime import datetime


def init_db():
    conn = sqlite3.connect("hotel.db", check_same_thread=False)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'Available',
            current_guest TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_type TEXT NOT NULL,
            room_number TEXT NOT NULL,
            guest_name TEXT,
            timestamp TEXT NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) FROM rooms")
    if cur.fetchone()[0] == 0:
        rooms_data = [
            ("101", "Standard", 150.0, "Available", None),
            ("102", "Standard", 150.0, "Available", None),
            ("201", "Deluxe", 300.0, "Available", None),
            ("202", "Deluxe", 300.0, "Available", None),
            ("301", "Suite", 500.0, "Available", None),
        ]
        cur.executemany(
            "INSERT INTO rooms (room_number, room_type, price, status, current_guest) VALUES (?, ?, ?, ?, ?)",
            rooms_data,
        )

    try:
        cur.execute("ALTER TABLE rooms ADD COLUMN current_guest TEXT")
    except:
        pass

    conn.commit()
    return conn


def log_event(conn, event_type, room_number, guest_name=None):
    conn.execute(
        "INSERT INTO events (event_type, room_number, guest_name, timestamp) VALUES (?, ?, ?, datetime('now'))",
        (event_type, room_number, guest_name),
    )
    conn.commit()


def main(page: ft.Page):
    page.title = "Simple Hotel Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 700

    db_conn = init_db()
    content_area = ft.Column(expand=True, scroll="auto")

    def show_page(page_name):
        content_area.controls.clear()
        cur = db_conn.cursor()

        if page_name == "Dashboard":
            cur.execute("SELECT status, COUNT(*) FROM rooms GROUP BY status")
            stats = dict(cur.fetchall())

            available_total = stats.get("Available", 0)
            occupied_total = stats.get("Occupied", 0)

            cur.execute(
                "SELECT COUNT(DISTINCT guest_name) FROM events WHERE event_type='Check-in'"
            )
            total_guests = cur.fetchone()[0]

            content_area.controls.append(ft.Text("Hotel Overview", size=30, weight="bold"))

            content_area.controls.append(
                ft.Row([
                    ft.Container(
                        ft.Text(f"Available Rooms: {available_total}", color="white"),
                        bgcolor="green", padding=20, border_radius=10
                    ),
                    ft.Container(
                        ft.Text(f"Occupied Rooms: {occupied_total}", color="white"),
                        bgcolor="red", padding=20, border_radius=10
                    ),
                    ft.Container(
                        ft.Text(f"Total Guests: {total_guests}", color="white"),
                        bgcolor="blue", padding=20, border_radius=10
                    ),
                ])
            )

            content_area.controls.append(
                ft.Text("Recent Activity Log", size=22, weight="bold")
            )

            cur.execute(
                "SELECT event_type, room_number, guest_name, timestamp FROM events ORDER BY id DESC LIMIT 50"
            )
            rows = cur.fetchall()

            if not rows:
                content_area.controls.append(ft.Text("No records yet", color="grey"))
            else:
                colors = {
                    "Check-in": "green",
                    "Check-out": "red",
                    "Room Change": "orange"
                }

                for ev, room, guest, ts in rows:
                    content_area.controls.append(
                        ft.Card(
                            content=ft.ListTile(
                                leading=ft.Container(
                                    ft.Text(ev, color="white", size=12),
                                    bgcolor=colors.get(ev, "grey"),
                                    padding=5,
                                    border_radius=5
                                ),
                                title=ft.Text(f"Room {room} — {guest or '-'}"),
                                subtitle=ft.Text(ts)
                            )
                        )
                    )

        elif page_name == "Rooms":
            content_area.controls.append(ft.Text("Room Management", size=30, weight="bold"))

            cur.execute("SELECT id, room_number, room_type, price, status, current_guest FROM rooms")
            rooms = cur.fetchall()

            for r in rooms:
                r_id, r_num, r_type, r_price, r_status, r_guest = r

                subtitle = f"Status: {r_status} | ${r_price}/night"
                if r_guest:
                    subtitle += f" | Guest: {r_guest}"

                def checkin_handler(e, rid=r_id, rnum=r_num):
                    db_conn.execute(
                        "UPDATE rooms SET status='Occupied', current_guest='Guest' WHERE id=?",
                        (rid,),
                    )
                    db_conn.commit()
                    log_event(db_conn, "Check-in", rnum)
                    show_page("Rooms")

                def checkout_handler(e, rid=r_id, rnum=r_num, g=r_guest):
                    db_conn.execute(
                        "UPDATE rooms SET status='Available', current_guest=NULL WHERE id=?",
                        (rid,),
                    )
                    db_conn.commit()
                    log_event(db_conn, "Check-out", rnum, g)
                    show_page("Rooms")

                if r_status == "Available":
                    btn = ft.ElevatedButton("Check-in", on_click=checkin_handler)
                else:
                    btn = ft.ElevatedButton("Check-out", on_click=checkout_handler)

                content_area.controls.append(
                    ft.Card(
                        content=ft.ListTile(
                            title=ft.Text(f"Room {r_num} - {r_type}"),
                            subtitle=ft.Text(subtitle),
                            trailing=btn
                        )
                    )
                )

        elif page_name == "Register":
            TYPE_PRICES = {"Standard": 150, "Deluxe": 300, "Suite": 500}

            name_box = ft.TextField(label="Guest Full Name")
            btn1 = ft.ElevatedButton("Continue")

            type_dd = ft.Dropdown(
                label="Room Type",
                options=[
                    ft.dropdown.Option("Standard"),
                    ft.dropdown.Option("Deluxe"),
                    ft.dropdown.Option("Suite"),
                ],
                visible=False
            )
            btn2 = ft.ElevatedButton("Continue", visible=False)

            nights = ft.TextField(label="Number of Nights", visible=False)
            calc_btn = ft.ElevatedButton("Calculate Total", visible=False)

            result = ft.Text("", visible=False)
            confirm = ft.ElevatedButton("Confirm Check-in", visible=False)

            def step1(e):
                if not name_box.value.strip():
                    return
                type_dd.visible = True
                btn2.visible = True
                page.update()

            def step2(e):
                if not type_dd.value:
                    return
                nights.visible = True
                calc_btn.visible = True
                page.update()

            def calc(e):
                try:
                    n = int(nights.value)
                    assert n > 0
                except:
                    return

                total = TYPE_PRICES[type_dd.value] * n
                result.value = f"Total Price: ${total}"
                result.visible = True
                confirm.visible = True
                page.update()

            def finish(e):
                name = name_box.value
                rtype = type_dd.value

                cur.execute(
                    "SELECT id, room_number FROM rooms WHERE room_type=? AND status='Available' LIMIT 1",
                    (rtype,)
                )
                row = cur.fetchone()

                if not row:
                    result.value = "No available room!"
                    result.visible = True
                    page.update()
                    return

                rid, rnum = row

                db_conn.execute("INSERT INTO guests (full_name) VALUES (?)", (name,))
                db_conn.execute(
                    "UPDATE rooms SET status='Occupied', current_guest=? WHERE id=?",
                    (name, rid),
                )
                db_conn.commit()

                log_event(db_conn, "Check-in", rnum, name)

                show_page("Register")

            btn1.on_click = step1
            btn2.on_click = step2
            calc_btn.on_click = calc
            confirm.on_click = finish

            content_area.controls.extend([
                ft.Text("Register Guest", size=30, weight="bold"),
                name_box, btn1,
                type_dd, btn2,
                nights, calc_btn,
                result,
                confirm
            ])

        page.update()

    nav = ft.NavigationRail(
        selected_index=0,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationRailDestination(icon=ft.Icons.BED, label="Rooms"),
            ft.NavigationRailDestination(icon=ft.Icons.PERSON_ADD, label="Register"),
        ],
        on_change=lambda e: show_page(
            ["Dashboard", "Rooms", "Register"][e.control.selected_index]
        ),
    )

    page.add(ft.Row([nav, ft.VerticalDivider(width=1), content_area], expand=True))
    show_page("Dashboard")


ft.app(target=main)