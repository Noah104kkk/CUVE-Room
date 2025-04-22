from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

@app.route('/')
def welcome():
    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reservations WHERE date >= date('now')")
    reservations = c.fetchall()
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

        conn = sqlite3.connect('reservations.db')
        c = conn.cursor()

        # 重複チェック（1分以上かぶる予約があるか）
        c.execute("""
            SELECT * FROM reservations
            WHERE date = ? AND
            ((start_time < ? AND end_time > ?) OR
             (start_time < ? AND end_time > ?) OR
             (start_time >= ? AND end_time <= ?))
            AND (status IS NULL OR status != '拒否')
        """, (date, end_time, end_time, start_time, start_time, start_time, end_time))

        conflict = c.fetchone()
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
    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO reservations (position, name, date, start_time, end_time, status)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (position, name, date, start_time, end_time, ''))  # 状態は空白
    conn.commit()
    conn.close()

    message = f"{position}：{name} が {date} の {start_time}〜{end_time} に予約しました！"
    return render_template('complete.html', message=message)

@app.route('/cancel', methods=['POST'])
def cancel():
    name = request.form['name']
    date = request.form['date']
    start_time = request.form['start_time']

    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("DELETE FROM reservations WHERE name=? AND date=? AND start_time=?", (name, date, start_time))
    conn.commit()
    conn.close()
    return redirect(url_for('welcome'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'adminpass':
            session['admin'] = True
            return redirect(url_for('admin'))

    if not session.get('admin'):
        return render_template('admin_login.html', error=None)

    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reservations")
    reservations = c.fetchall()
    conn.close()
    return render_template('admin.html', reservations=reservations)

@app.route('/reject', methods=['POST'])
def reject():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    try:
        target_id = request.form['id']
        conn = sqlite3.connect('reservations.db')
        c = conn.cursor()
        c.execute("UPDATE reservations SET status = '拒否' WHERE id = ?", (target_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    except Exception as e:
        print("拒否処理エラー:", e)
        return "拒否処理中にエラーが発生しました", 500

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

