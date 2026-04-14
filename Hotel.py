import flet as ft
import sqlite3
 
def init_db():
    conn = sqlite3.connect("hotel.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type   TEXT NOT NULL,
            price       REAL NOT NULL,
            status      TEXT DEFAULT 'available'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone     TEXT
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            guest_id   INTEGER NOT NULL,
            room_id    INTEGER NOT NULL,
            check_in   TEXT,
            check_out  TEXT,
            FOREIGN KEY(guest_id) REFERENCES guests(id),
            FOREIGN KEY(room_id)  REFERENCES rooms(id)
        )
    """)
    cur.execute("DROP VIEW IF EXISTS room_summary")
    cur.execute("""
        CREATE VIEW room_summary AS
        SELECT status, COUNT(*) AS count
        FROM rooms
        GROUP BY status
    """)
    cur.execute("SELECT COUNT(*) FROM rooms")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO rooms (room_number, room_type, price) VALUES (?, ?, ?)",
            [
            ("101", "Standard", 150.0, "Available"),
            ("102", "Standard", 150.0, "Available"),
            ("201", "Deluxe", 300.0, "Available"),
            ("202", "Deluxe", 300.0, "Available"),
            ("301", "Suite", 500.0, "Available")
        ]
        )
    conn.commit()
    return conn

def main(page: ft.Page):
    page.title = "Simple Hotel Manager"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width = 900
    page.window_height = 700
    
    db_conn = init_db()
    content_area = ft.Column(expand=True, scroll="auto")

    def show_page(page_name):
        content_area.controls.clear()
        
        if page_name == "Dashboard":
            cur = db_conn.cursor()
            cur.execute("SELECT status, COUNT(*) FROM rooms GROUP BY status")
            stats = dict(cur.fetchall())
            
            content_area.controls.append(ft.Text("Hotel Overview", size=30, weight="bold"))
            content_area.controls.append(
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"Available: {stats.get('Available', 0)}", color="white"),
                        bgcolor="green", padding=20, border_radius=10
                    ),
                    ft.Container(
                        content=ft.Text(f"Occupied: {stats.get('Occupied', 0)}", color="white"),
                        bgcolor="red", padding=20, border_radius=10
                    ),
                ])
            )
        # (Remaining page logic will be in Part 3)