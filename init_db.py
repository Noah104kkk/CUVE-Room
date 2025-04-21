import sqlite3

conn = sqlite3.connect('reservations.db')
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position TEXT NOT NULL,
    name TEXT NOT NULL,
    date TEXT NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    status TEXT DEFAULT '承認'
)
''')

conn.commit()
conn.close()

print("reservations.db を初期化しました！")
