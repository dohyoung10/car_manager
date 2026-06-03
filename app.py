# =========================================================
#  내 차 정비 관리 시스템 (My Car Maintenance Manager)
#  Flask + SQLite 웹 애플리케이션
# =========================================================
#  [이 프로그램이 동작하는 큰 흐름]
#   1) 브라우저가 주소(URL)로 요청을 보냄  (예: 127.0.0.1:5000/login/)
#   2) 아래 @app.route 가 그 주소에 맞는 '함수'를 실행함
#   3) 함수는 SQLite(car.db)에서 SQL로 데이터를 읽거나 저장함
#   4) render_template 로 templates 폴더의 HTML에 데이터를 끼워 넣어 응답함
#
#  [테이블 3개 / 1:N 관계 2개]
#   users(회원) ─< cars(차량) ─< records(정비기록)
#   - users 1 : N cars   (회원 한 명이 차 여러 대)
#   - cars  1 : N records (차 한 대에 정비기록 여러 개)
# =========================================================

from flask import Flask, request, redirect, render_template, session
# werkzeug: 비밀번호를 '해시(암호화)'로 저장/검증하는 보안 라이브러리
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, date

app = Flask(__name__)
# 세션(로그인 상태)을 암호화하기 위한 비밀 키 -- [보안 포인트]
app.secret_key = 'car-manager-secret-key-1234'

DB_NAME = 'car.db'


# ---------------------------------------------------------
#  DB 연결 도우미 함수
# ---------------------------------------------------------
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # 결과를 컬럼 이름으로 꺼낼 수 있게 해줌
    return conn


# ---------------------------------------------------------
#  DB 초기화: 테이블 3개 생성 + 관리자 계정 자동 생성
# ---------------------------------------------------------
def init_db():
    conn = get_db()
    cur = conn.cursor()

    # (1) 회원 테이블
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role     TEXT DEFAULT 'user'
        )
    ''')

    # (2) 차량 테이블  --  users 1 : N cars (회원 한 명이 차 여러 대)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS cars (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id  INTEGER NOT NULL,
            car_name TEXT NOT NULL,
            mileage  INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # (3) 정비기록 테이블  --  cars 1 : N records (차 한 대에 정비기록 여러 개)
    cur.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            car_id       INTEGER NOT NULL,
            part_name    TEXT NOT NULL,
            last_date    TEXT NOT NULL,
            cycle_months INTEGER NOT NULL,
            memo         TEXT,
            FOREIGN KEY (car_id) REFERENCES cars(id)
        )
    ''')

    # 관리자 계정이 없으면 자동 생성 (아이디: admin / 비번: admin)
    cur.execute("SELECT COUNT(*) FROM users WHERE role='admin'")
    if cur.fetchone()[0] == 0:
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (?, ?, 'admin')",
            ('admin', generate_password_hash('admin'))
        )

    conn.commit()
    conn.close()


# ---------------------------------------------------------
#  [핵심 추가 기능] 교체 예정일 & D-day 계산 함수
#  마지막 교체일 + 주기(개월) = 다음 교체 예정일
#  다음 교체 예정일 - 오늘 = 남은 날짜(D-day)
# ---------------------------------------------------------
def calc_dday(last_date, cycle_months):
    last = datetime.strptime(last_date, '%Y-%m-%d').date()

    # 마지막 교체일에 '주기(개월)'를 더해서 다음 교체일 구하기
    total_month = last.month - 1 + cycle_months
    next_year = last.year + total_month // 12
    next_month = total_month % 12 + 1
    next_day = min(last.day, 28)  # 30/31일 등 말일 오류 방지용 간단 처리
    next_date = date(next_year, next_month, next_day)

    d_day = (next_date - date.today()).days  # 남은 날 (음수면 이미 지남)

    # 상태 판정
    if d_day < 0:
        status = '교체 시기 지남'
        color = 'red'
    elif d_day <= 30:
        status = '곧 교체'
        color = 'orange'
    else:
        status = '여유'
        color = 'green'

    return next_date.strftime('%Y-%m-%d'), d_day, status, color


# ---------------------------------------------------------
#  프로그램이 켜질 때(import 될 때) DB를 준비한다.
#  ★ 여기를 함수 맨 바깥(모듈 레벨)에 두는 이유:
#    - 내 컴퓨터(python app.py)에서도 실행되고,
#    - 배포 서버(PythonAnywhere, WSGI)에서도 실행되게 하기 위함.
#    WSGI는 app.py를 'import'만 하고 맨 아래 __main__ 블록은 실행하지 않으므로,
#    init_db()를 __main__ 안에만 두면 배포 시 테이블이 안 만들어진다.
# ---------------------------------------------------------
init_db()


# =========================================================
#  회원 기능: 회원가입 / 로그인 / 로그아웃
# =========================================================

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (username,))
        if cur.fetchone():  # 이미 있는 아이디면
            conn.close()
            return render_template('register.html', error='이미 존재하는 아이디입니다.')

        # 비밀번호를 그대로 저장하지 않고 '해시'로 암호화해서 저장 -- [보안 포인트]
        cur.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            (username, generate_password_hash(password))
        )
        conn.commit()
        conn.close()
        return redirect('/login/')

    return render_template('register.html', error='')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM users WHERE username = ?', (username,))
        user = cur.fetchone()
        conn.close()

        # 저장된 해시와 입력한 비번이 일치하는지 검사 -- [보안 포인트]
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role'] = user['role']
            return redirect('/')
        else:
            return render_template('login.html', error='아이디 또는 비밀번호가 틀렸습니다.')

    return render_template('login.html', error='')


@app.route('/logout/')
def logout():
    session.clear()  # 세션 비우기 = 로그아웃
    return redirect('/login/')


# =========================================================
#  차량 기능: 목록(Read) / 등록(Create) / 삭제(Delete)
# =========================================================

@app.route('/')
def index():
    # 로그인 안 했으면 로그인 페이지로
    if 'user_id' not in session:
        return redirect('/login/')

    conn = get_db()
    cur = conn.cursor()
    # 내가 등록한 차량만 조회
    cur.execute('SELECT * FROM cars WHERE user_id = ?', (session['user_id'],))
    cars = cur.fetchall()

    # 각 차량마다 '곧 교체할 항목 개수'를 같이 계산해서 보여주기
    car_list = []
    for car in cars:
        cur.execute('SELECT * FROM records WHERE car_id = ?', (car['id'],))
        records = cur.fetchall()
        warning_count = 0
        for r in records:
            _, d_day, _, _ = calc_dday(r['last_date'], r['cycle_months'])
            if d_day <= 30:  # 30일 이하 남았으면 경고
                warning_count += 1
        car_list.append({'car': car, 'warning': warning_count})

    conn.close()
    return render_template('index.html', car_list=car_list)


@app.route('/car/add/', methods=['GET', 'POST'])
def add_car():
    if 'user_id' not in session:
        return redirect('/login/')

    if request.method == 'POST':
        car_name = request.form['car_name']
        mileage = request.form['mileage'] or 0

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO cars (user_id, car_name, mileage) VALUES (?, ?, ?)',
            (session['user_id'], car_name, mileage)
        )
        conn.commit()
        conn.close()
        return redirect('/')

    return render_template('add_car.html')


@app.route('/car/<int:car_id>/delete/')
def delete_car(car_id):
    if 'user_id' not in session:
        return redirect('/login/')

    conn = get_db()
    cur = conn.cursor()
    # 차량 삭제 시 그 차의 정비기록도 함께 삭제
    cur.execute('DELETE FROM records WHERE car_id = ?', (car_id,))
    cur.execute('DELETE FROM cars WHERE id = ? AND user_id = ?', (car_id, session['user_id']))
    conn.commit()
    conn.close()
    return redirect('/')


# =========================================================
#  정비기록 기능: 상세(Read) / 등록(Create) / 수정(Update) / 삭제(Delete)
# =========================================================

@app.route('/car/<int:car_id>/')
def car_detail(car_id):
    if 'user_id' not in session:
        return redirect('/login/')

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM cars WHERE id = ?', (car_id,))
    car = cur.fetchone()

    cur.execute('SELECT * FROM records WHERE car_id = ? ORDER BY last_date DESC', (car_id,))
    records = cur.fetchall()
    conn.close()

    # 각 기록마다 D-day 계산해서 화면에 넘겨주기
    record_list = []
    for r in records:
        next_date, d_day, status, color = calc_dday(r['last_date'], r['cycle_months'])
        record_list.append({
            'record': r,
            'next_date': next_date,
            'd_day': d_day,
            'status': status,
            'color': color
        })

    return render_template('car_detail.html', car=car, record_list=record_list)


@app.route('/car/<int:car_id>/record/add/', methods=['GET', 'POST'])
def add_record(car_id):
    if 'user_id' not in session:
        return redirect('/login/')

    if request.method == 'POST':
        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO records (car_id, part_name, last_date, cycle_months, memo) VALUES (?, ?, ?, ?, ?)',
            (car_id, request.form['part_name'], request.form['last_date'],
             request.form['cycle_months'], request.form['memo'])
        )
        conn.commit()
        conn.close()
        return redirect(f'/car/{car_id}/')

    return render_template('add_record.html', car_id=car_id)


@app.route('/record/<int:record_id>/edit/', methods=['GET', 'POST'])
def edit_record(record_id):
    if 'user_id' not in session:
        return redirect('/login/')

    conn = get_db()
    cur = conn.cursor()

    if request.method == 'POST':
        cur.execute(
            'UPDATE records SET part_name=?, last_date=?, cycle_months=?, memo=? WHERE id=?',
            (request.form['part_name'], request.form['last_date'],
             request.form['cycle_months'], request.form['memo'], record_id)
        )
        conn.commit()
        cur.execute('SELECT car_id FROM records WHERE id = ?', (record_id,))
        car_id = cur.fetchone()['car_id']
        conn.close()
        return redirect(f'/car/{car_id}/')

    cur.execute('SELECT * FROM records WHERE id = ?', (record_id,))
    record = cur.fetchone()
    conn.close()
    return render_template('edit_record.html', record=record)


@app.route('/record/<int:record_id>/delete/')
def delete_record(record_id):
    if 'user_id' not in session:
        return redirect('/login/')

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT car_id FROM records WHERE id = ?', (record_id,))
    car_id = cur.fetchone()['car_id']
    cur.execute('DELETE FROM records WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    return redirect(f'/car/{car_id}/')


# =========================================================
#  관리자 페이지: 모든 회원 / 모든 차량 조회 (admin만 접근 가능)
# =========================================================

@app.route('/admin/')
def admin():
    # 로그인 안 했거나, 관리자가 아니면 차단
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM users')
    users = cur.fetchall()
    # 차량 + 주인 아이디를 JOIN으로 한 번에 조회
    cur.execute('''
        SELECT cars.*, users.username
        FROM cars JOIN users ON cars.user_id = users.id
    ''')
    cars = cur.fetchall()
    conn.close()
    return render_template('admin.html', users=users, cars=cars)


@app.route('/admin/user/<int:user_id>/delete/')
def admin_delete_user(user_id):
    if session.get('role') != 'admin':
        return redirect('/')

    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE id = ? AND role != 'admin'", (user_id,))
    conn.commit()
    conn.close()
    return redirect('/admin/')


# =========================================================
#  서버 실행
#  - 이 블록은 '내 컴퓨터에서 python app.py로 직접 실행할 때'만 동작한다.
#  - 배포 서버(PythonAnywhere)에서는 이 블록이 실행되지 않으므로(위 init_db 참고)
#    debug=True 가 켜질 걱정이 없다.
# =========================================================
if __name__ == '__main__':
    app.run(debug=True)  # 개발 모드로 서버 실행 (http://127.0.0.1:5000)
