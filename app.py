from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import datetime
import traceback

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

DB_FILE = 'reservations.db'

def get_reservations(include_past=False):
    reservations = []
    today = datetime.date.today()
    if os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT position, name, date, start_time, end_time, status FROM reservations")
        for row in cursor.fetchall():
            date_obj = datetime.datetime.strptime(row[2], "%Y-%m-%d").date()
            if include_past or date_obj >= today:
                reservations.append(row)
        conn.close()
    return reservations

@app.route('/')
def welcome():
    reservations = get_reservations()
    return render_template('welcome.html', reservations=reservations)

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        position = request.form['position']
        name = request.form['name']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT start_time, end_time, status FROM reservations WHERE date = ?
        ''', (date,))
        conflict = False
        new_start = datetime.datetime.strptime(start_time, "%H:%M")
        new_end = datetime.datetime.strptime(end_time, "%H:%M")

        for row in cursor.fetchall():
            existing_start = datetime.datetime.strptime(row[0], "%H:%M")
            existing_end = datetime.datetime.strptime(row[1], "%H:%M")
            overlap = max(existing_start, new_start) < min(existing_end, new_end)
            if overlap and row[2] != '拒否':
                conflict = True
                break
        conn.close()

        if conflict:
            return render_template('confirm.html', position=position, name=name, date=date,
                                   start_time=start_time, end_time=end_time)

        return save_reservation(position, name, date, start_time, end_time)
    return render_template('index.html')

@app.route('/confirm', methods=['POST'])
def confirm():
    position = request.form['position']
    name = request.form['name']
    date = request.form['date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    return save_reservation(position, name, date, start_time, end_time)

def save_reservation(position, name, date, start_time, end_time):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position TEXT,
            name TEXT,
            date TEXT,
            start_time TEXT,
            end_time TEXT,
            status TEXT DEFAULT '承認'
        )
    ''')
    cursor.execute('''
        INSERT INTO reservations (position, name, date, start_time, end_time)
        VALUES (?, ?, ?, ?, ?)
    ''', (position, name, date, start_time, end_time))
    conn.commit()
    conn.close()
    message = f"{position}：{name} が {date} の {start_time}〜{end_time} に予約しました！"
    return render_template('complete.html', message=message)

@app.route('/cancel', methods=['POST'])
def cancel():
    name = request.form['name']
    date = request.form['date']
    start_time = request.form['start_time']
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        DELETE FROM reservations
        WHERE name = ? AND date = ? AND start_time = ?
    ''', (name, date, start_time))
    conn.commit()
    conn.close()
    return redirect(url_for('welcome'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'adminpass':
            session.permanent = True  # ← セッション維持！
            session['admin'] = True
            reservations = get_reservations(include_past=True)
            return render_template('admin.html', reservations=reservations)
        else:
            return render_template('admin_login.html', error='パスワードが違います')
    return render_template('admin_login.html')

@app.route('/reject', methods=['POST'])
def reject():
    if not session.get('admin'):
        return redirect(url_for('admin'))
    try:
        target_index = int(request.form['index'])

        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM reservations ORDER BY id")
        all_ids = cursor.fetchall()

        if target_index < len(all_ids):
            target_id = all_ids[target_index][0]
            cursor.execute("UPDATE reservations SET status = '拒否' WHERE id = ?", (target_id,))
            conn.commit()
        conn.close()
        return redirect(url_for('admin'))

    except Exception as e:
        print("拒否処理中のエラー:")
        traceback.print_exc()
        return "拒否処理中にエラーが発生しました", 500

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
