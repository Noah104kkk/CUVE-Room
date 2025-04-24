import sqlite3

conn = sqlite3.connect('reservations.db')
c = conn.cursor()
c.execute('DROP TABLE IF EXISTS reservations')
c.execute('''
CREATE TABLE reservations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    position TEXT,
    name TEXT,
    date TEXT,
    start_time TEXT,
    end_time TEXT,
    status TEXT,
    mode TEXT
)
''')
conn.commit()
conn.close()
