from flask import Flask, render_template, request, redirect, url_for
import csv
import os

app = Flask(__name__)

@app.route('/')
def welcome():
    reservations = []
    filename = 'reservations.csv'
    if os.path.isfile(filename):
        with open(filename, 'r', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            next(reader)
            for row in reader:
                reservations.append(row)
    return render_template('welcome.html', reservations=reservations)

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        position = request.form['position']
        name = request.form['name']
        group_name = request.form['group_name']
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
                    if row[3] == date and row[4] == start_time:
                        if row[6] != '拒否':
                            conflict = True
                            break

        if conflict:
            return render_template('confirm.html', position=position, name=name, group_name=group_name,
                                   date=date, start_time=start_time, end_time=end_time)

        return save_reservation(position, name, group_name, date, start_time, end_time)

    return render_template('index.html')

@app.route('/confirm', methods=['POST'])
def confirm():
    position = request.form['position']
    name = request.form['name']
    group_name = request.form['group_name']
    date = request.form['date']
    start_time = request.form['start_time']
    end_time = request.form['end_time']

    return save_reservation(position, name, group_name, date, start_time, end_time)

def save_reservation(position, name, group_name, date, start_time, end_time):
    filename = 'reservations.csv'
    file_exists = os.path.isfile(filename)
    with open(filename, 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        if not file_exists:
            writer.writerow(['役職', '氏名', '団体名', '日付', '開始時間', '終了時間', '状態'])
        writer.writerow([position, name, group_name, date, start_time, end_time, '承認'])
    return f"{group_name}（{position}：{name}）が{date}の{start_time}〜{end_time}に予約しました！"

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
            if row[1] == name and row[3] == date and row[4] == start_time:
                continue
            writer.writerow(row)
    os.replace(temp_filename, filename)
    return redirect(url_for('welcome'))

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form['password']
        if password == 'adminpass':
            reservations = []
            filename = 'reservations.csv'
            if os.path.isfile(filename):
                with open(filename, 'r', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    next(reader)
                    for row in reader:
                        reservations.append(row)
            return render_template('admin.html', reservations=reservations)
        else:
            return 'パスワードが違います'
    return render_template('admin_login.html')

@app.route('/reject', methods=['POST'])
def reject():
    target_index = int(request.form['index'])
    filename = 'reservations.csv'
    temp_filename = 'temp_reservations.csv'

    with open(filename, 'r', encoding='utf-8') as infile, open(temp_filename, 'w', newline='', encoding='utf-8') as outfile:
        reader = list(csv.reader(infile))
        writer = csv.writer(outfile)

        writer.writerow(reader[0])

        for i, row in enumerate(reader[1:]):
            if i == target_index:
                row[6] = '拒否'
            writer.writerow(row)

    os.replace(temp_filename, filename)
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True)