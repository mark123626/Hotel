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
                ("101", "Standard", 150.0),
                ("201", "Deluxe",   300.0),
                ("301", "Suite",    500.0),
            ]
        )
    conn.commit()
    return conn