import flet as ft
import sqlite3

def init_db():
    conn = sqlite3.connect("hotel.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_number TEXT UNIQUE NOT NULL,
            room_type TEXT NOT NULL,
            price REAL NOT NULL,
            status TEXT DEFAULT 'Available'
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS guests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT
        )
    """)
    
    cur.execute("SELECT COUNT(*) FROM rooms")
    if cur.fetchone()[0] == 0:
        rooms_data = [
            ("101", "Standard", 150.0, "Available"),
            ("102", "Standard", 150.0, "Available"),
            ("201", "Deluxe", 300.0, "Available"),
            ("202", "Deluxe", 300.0, "Available"),
            ("301", "Suite", 500.0, "Available")
        ]
        cur.executemany("INSERT INTO rooms (room_number, room_type, price, status) VALUES (?, ?, ?, ?)", rooms_data)
    
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
        cur = db_conn.cursor() 
        
        if page_name == "Dashboard":
            cur.execute("SELECT status, COUNT(*) FROM rooms GROUP BY status")
            stats = dict(cur.fetchall())
            
            available_total = stats.get('Available', 0)
            occupied_total = stats.get('Occupied', 0)

            content_area.controls.append(ft.Text("Hotel Overview", size=30, weight="bold"))
            content_area.controls.append(
                ft.Row([
                    ft.Container(
                        content=ft.Text(f"Available: {available_total}", color="white"),
                        bgcolor="green", padding=20, border_radius=10
                    ),
                    ft.Container(
                        content=ft.Text(f"Occupied: {occupied_total}", color="white"),
                        bgcolor="red", padding=20, border_radius=10
                    ),
                ])
            )

        elif page_name == "Rooms":
            content_area.controls.append(ft.Text("Room Management", size=30, weight="bold"))
            cur.execute("SELECT * FROM rooms")
            for r in cur.fetchall():
                def toggle(e, r_id=r[0], current=r[4]):
                    new_status = "Occupied" if current == "Available" else "Available"
                    db_conn.execute("UPDATE rooms SET status=? WHERE id=?", (new_status, r_id))
                    db_conn.commit()
                    show_page("Rooms") 

                content_area.controls.append(ft.Card(content=ft.ListTile(
                    leading=ft.Icon(ft.Icons.BED), 
                    title=ft.Text(f"Room {r[1]} - {r[2]}"),
                    subtitle=ft.Text(f"Status: {r[4]}"),
                    trailing=ft.ElevatedButton("Switch", on_click=toggle)
                )))

        elif page_name == "Register":
            name_box = ft.TextField(label="Full Name")
            def save(e):
                if name_box.value:
                    db_conn.execute("INSERT INTO guests (full_name) VALUES (?)", (name_box.value,))
                    db_conn.commit()
                    name_box.value = ""
                    page.snack_bar = ft.SnackBar(ft.Text("Guest Saved!"))
                    page.snack_bar.open = True
                    page.update()
                else:
                    page.snack_bar = ft.SnackBar(ft.Text("Please enter a name!"))
                    page.snack_bar.open = True
                    page.update()
            
            content_area.controls.extend([
                ft.Text("Register Guest", size=30, weight="bold"), 
                name_box, 
                ft.ElevatedButton("Save", icon=ft.Icons.SAVE, on_click=save)
            ])

        page.update()

    nav = ft.NavigationRail(
        selected_index=0,
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationRailDestination(icon=ft.Icons.BED, label="Rooms"),
            ft.NavigationRailDestination(icon=ft.Icons.PERSON_ADD, label="Register"),
        ],
        on_change=lambda e: show_page(["Dashboard", "Rooms", "Register"][e.control.selected_index])
    )

    page.add(ft.Row([nav, ft.VerticalDivider(width=1), content_area], expand=True))
    show_page("Dashboard")

ft.app(target=main)