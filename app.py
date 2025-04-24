from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

@app.route('/')
def welcome():
    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reservations WHERE date >= date('now') ORDER BY date ASC, start_time ASC")
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
        mode = request.form['mode']  # 専属 or 開放

        conn = sqlite3.connect('reservations.db')
        c = conn.cursor()

        if mode == '専属':
            c.execute("""
                SELECT * FROM reservations
                WHERE date = ? AND (
                    (? < end_time AND ? > start_time)
                ) AND (status IS NULL OR status != '拒否')
            """, (date, start_time, end_time))
            conflict = c.fetchone()
            conn.close()

            if conflict:
                return render_template('confirm.html', position=position, name=name,
                                       date=date, start_time=start_time, end_time=end_time, mode=mode)
        else:
            conn.close()

        return save_reservation(position, name, date, start_time, end_time, mode)

    return render_template('index.html')

@app.route('/confirm', methods=['POST'])
def confirm():
    position = request.form['position']
    name = request.form['name']
    date = request.form['date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']
    mode = request.form['mode']

    return save_reservation(position, name, date, start_time, end_time, mode)

def save_reservation(position, name, date, start_time, end_time, mode):
    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("""
        INSERT INTO reservations (position, name, date, start_time, end_time, status, mode)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (position, name, date, start_time, end_time, '', mode))
    conn.commit()
    conn.close()

    message = f"{position}：{name} が {date} の {start_time}〜{end_time} に予約しました！（{mode}）"
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
        else:
            return render_template('admin_login.html', error='パスワードが違います')

    if not session.get('admin'):
        return render_template('admin_login.html', error=None)

    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reservations ORDER BY date ASC, start_time ASC")
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

@app.route('/undo_reject', methods=['POST'])
def undo_reject():
    if not session.get('admin'):
        return redirect(url_for('admin'))

    try:
        target_id = request.form['id']
        conn = sqlite3.connect('reservations.db')
        c = conn.cursor()
        c.execute("UPDATE reservations SET status = '' WHERE id = ?", (target_id,))
        conn.commit()
        conn.close()
        return redirect(url_for('admin'))
    except Exception as e:
        print("拒否取消エラー:", e)
        return "拒否取消中にエラーが発生しました", 500

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
