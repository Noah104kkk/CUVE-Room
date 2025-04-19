from flask import Flask, render_template, request, redirect, url_for, session
from flask_session import Session
import csv
import os
import datetime

app = Flask(__name__)
app.secret_key = 'your-very-secret-key'

# Flask-Session設定
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_FILE_DIR'] = './.flask_session/'
app.config['SESSION_PERMANENT'] = False
Session(app)

@app.route('/')
def welcome():
    reservations = []
    today = datetime.date.today()
    filename = 'reservations.csv'
    if os.path.isfile(filename):
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                if len(row) >= 6:
                    date_obj = datetime.datetime.strptime(row[2], "%Y-%m-%d").date()
                    if date_obj >= today:
                        reservations.append(row)
    return render_template('welcome.html', reservations=reservations)

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        position = request.form['position']
        name = request.form['name']
        date = request.form['date']
        start_time = request.form['start_time']
        end_time = request.form['end_time']

        filename = 'reservations.csv'
        conflict = False
        if os.path.isfile(filename):
            with open(filename, 'r', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                next(reader)
                for row in reader:
                    if len(row) >= 6 and row[2] == date:
                        existing_start = datetime.datetime.strptime(row[3], "%H:%M")
                        existing_end = datetime.datetime.strptime(row[4], "%H:%M")
                        new_start = datetime.datetime.strptime(start_time, "%H:%M")
                        new_end = datetime.datetime.strptime(end_time, "%H:%M")
                        overlap = max(existing_start, new_start) < min(existing_end, new_end)
                        if overlap and row[5] != '拒否':
                            conflict = True
                            break

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
    filename = 'reservations.csv'
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['役職', '氏名', '日付', '開始時間', '終了時間', '状態'])
        writer.writerow([position, name, date, start_time, end_time, '承認'])
    message = f"{position}：{name} が {date} の {start_time}〜{end_time} に予約しました！"
    return render_template('complete.html', message=message)

@app.route('/cancel', methods=['POST'])
def cancel():
    name = request.form['name']
    date = request.form['date']
    start_time = request.form['start_time']

    filename = 'reservations.csv'
    temp_filename = 'temp_reservations.csv'
    with open(filename, 'r', encoding='utf-8') as infile, open(temp_filename, 'w', newline='', encoding='utf-8') as outfile:
        reader = csv.reader(infile)
        writer = csv.writer(outfile)
        for row in reader:
            if row[1] == name and row[2] == date and row[3] == start_time:
                continue
            writer.writerow(row)
    os.replace(temp_filename, filename)
    return redirect(url_for('welcome'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'adminpass':
            session['admin'] = True
            reservations = []
            filename = 'reservations.csv'
            if os.path.isfile(filename):
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)
                    for row in reader:
                        if len(row) >= 6:
                            reservations.append(row)
            return render_template('admin.html', reservations=reservations)
        else:
            return render_template('admin_login.html', error='パスワードが違います')
    return render_template('admin_login.html')

@app.route('/reject', methods=['POST'])
def reject():
    print('セッションadmin状態:', session.get('admin'))
    if not session.get('admin'):
        return redirect(url_for('admin'))

    try:
        target_index = int(request.form['index'])
        filename = 'reservations.csv'
        temp_filename = 'temp_reservations.csv'

        with open(filename, 'r', encoding='utf-8') as infile, open(temp_filename, 'w', newline='', encoding='utf-8') as outfile:
            reader = list(csv.reader(infile))
            writer = csv.writer(outfile)

            writer.writerow(reader[0])

            for i, row in enumerate(reader[1:]):
                if len(row) >= 6:
                    if i == target_index:
                        row[5] = '拒否'
                writer.writerow(row)

        os.replace(temp_filename, filename)
        return redirect(url_for('admin'))

    except Exception as e:
        print(f"拒否処理中のエラー: {e}")
        return "拒否処理中にエラーが発生しました", 500

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)