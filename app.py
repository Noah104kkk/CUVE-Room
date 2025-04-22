from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os
import datetime
import traceback

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

# セッション設定（Render対応）
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

DB_NAME = 'reservations.db'

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def welcome():
    conn = get_db_connection()
    today = datetime.date.today()
    reservations = conn.execute(
        "SELECT * FROM reservations WHERE date >= ?",
        (today.strftime('%Y-%m-%d'),)
    ).fetchall()
    conn.close()
    return render_template('welcome.html', reservations=reservations)

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        position = request.form['position']
        name = request.form['name']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        conn = get_db_connection()
        existing = conn.execute(
            "SELECT * FROM reservations WHERE date = ? AND status != '拒否'",
            (date,)
        ).fetchall()

        new_start = datetime.datetime.strptime(start_time, "%H:%M")
        new_end = datetime.datetime.strptime(end_time, "%H:%M")
        conflict = False

        for row in existing:
            existing_start = datetime.datetime.strptime(row['start_time'], "%H:%M")
            existing_end = datetime.datetime.strptime(row['end_time'], "%H:%M")
            if max(existing_start, new_start) < min(existing_end, new_end):
                conflict = True
                break

        conn.close()

        if conflict:
            return render_template('confirm.html', position=position, name=name,
                                   date=date, start_time=start_time, end_time=end_time)

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
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO reservations (position, name, date, start_time, end_time, status) VALUES (?, ?, ?, ?, ?, '承認')",
        (position, name, date, start_time, end_time)
    )
    conn.commit()
    conn.close()
    message = f"{position}：{name} が {date} の {start_time}〜{end_time} に予約しました！"
    return render_template('complete.html', message=message)

@app.route('/cancel', methods=['POST'])
def cancel():
    name = request.form['name']
    date = request.form['date']
    start_time = request.form['start_time']

    conn = get_db_connection()
    conn.execute(
        "DELETE FROM reservations WHERE name = ? AND date = ? AND start_time = ?",
        (name, date, start_time)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('welcome'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'adminpass':
            session['admin'] = True
            conn = get_db_connection()
            reservations = conn.execute("SELECT * FROM reservations").fetchall()
            conn.close()
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
        conn = get_db_connection()
        reservations = conn.execute("SELECT rowid, * FROM reservations").fetchall()
        if 0 <= target_index < len(reservations):
            rowid = reservations[target_index]['rowid']
            conn.execute("UPDATE reservations SET status = '拒否' WHERE rowid = ?", (rowid,))
            conn.commit()
        conn.close()
        return redirect(url_for('admin'))

    except Exception as e:
        print(f"拒否処理中のエラー: ")
	traceback.print_exc()
        return "拒否処理中にエラーが発生しました", 500

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
