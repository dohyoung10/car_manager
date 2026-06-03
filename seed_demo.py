# 발표 시연용 데모 데이터를 채워주는 스크립트
# (실행하면 car.db에 예시 회원/차량/정비기록이 들어갑니다)
# 사용법:  py seed_demo.py   또는   python seed_demo.py

from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import app  # app.py 재사용

app.init_db()
conn = app.get_db()
cur = conn.cursor()

# 데모 회원 (아이디: 도형 / 비번: 1234)
cur.execute("SELECT id FROM users WHERE username='도형'")
row = cur.fetchone()
if row:
    user_id = row['id']
else:
    cur.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                ('도형', generate_password_hash('1234')))
    user_id = cur.lastrowid

# 차량 한 대
cur.execute("INSERT INTO cars (user_id, car_name, mileage) VALUES (?, ?, ?)",
            (user_id, '아반떼 CN7', 42000))
car_id = cur.lastrowid

today = date.today()
# (부품, 마지막 교체일, 주기개월, 메모)  -- 색깔이 다양하게 나오도록 날짜를 섞음
records = [
    ('엔진오일', today - timedelta(days=210), 6, '합성유 사용'),       # 지남(빨강)
    ('에어컨 필터', today - timedelta(days=160), 6, ''),               # 곧(주황)
    ('타이어', today - timedelta(days=90), 24, '4짝 교체'),            # 여유(초록)
    ('브레이크 패드', today - timedelta(days=400), 18, '앞바퀴'),       # 곧/지남 근처
    ('와이퍼', today - timedelta(days=30), 12, ''),                    # 여유(초록)
]
for part, last, cycle, memo in records:
    cur.execute(
        "INSERT INTO records (car_id, part_name, last_date, cycle_months, memo) VALUES (?, ?, ?, ?, ?)",
        (car_id, part, last.strftime('%Y-%m-%d'), cycle, memo)
    )

conn.commit()
conn.close()
print('데모 데이터 입력 완료!  로그인 -> 아이디: 도형 / 비번: 1234  (관리자: admin / admin)')
