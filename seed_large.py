# 발표용 대량 가상 데이터 생성 스크립트 (회원 10명 + 차량 20대 + 정비기록 50개+)
from werkzeug.security import generate_password_hash
from datetime import date, timedelta
import random, app

app.init_db()
conn = app.get_db()
cur = conn.cursor()

# 기존 demo 데이터 외에 추가 (admin, 도형 계정은 유지)
users = [
    ("김민준", "1234"), ("이서연", "1234"), ("박지훈", "1234"),
    ("최수아", "1234"), ("정우진", "1234"), ("강하은", "1234"),
    ("윤도현", "1234"), ("장서영", "1234"), ("임현우", "1234"),
]

cars_data = {
    "김민준":  [("현대 아반떼 CN7", 42000), ("기아 K5", 18000)],
    "이서연":  [("쉐보레 트레일블레이저", 31000)],
    "박지훈":  [("현대 투싼", 67000), ("기아 쏘렌토", 5200)],
    "최수아":  [("르노 QM6", 24500)],
    "정우진":  [("현대 그랜저 GN7", 11000), ("제네시스 G80", 3000)],
    "강하은":  [("기아 니로 EV", 19800)],
    "윤도현":  [("현대 스타리아", 55000), ("기아 카니발", 88000)],
    "장서영":  [("볼보 XC40", 22000)],
    "임현우":  [("BMW 320i", 38000), ("미니 쿠퍼", 14000)],
}

parts_pool = [
    ("엔진오일",      6,  (-200, -10)),
    ("에어컨 필터",   6,  (-180, -20)),
    ("에어 필터",     12, (-370, -30)),
    ("브레이크패드",  18, (-540, -10)),
    ("타이어",        24, (-730, 200)),
    ("배터리",        24, (-700, 100)),
    ("와이퍼",        12, (-360, 300)),
    ("냉각수",        24, (-720, 180)),
    ("점화플러그",    24, (-700,  90)),
    ("자동변속기오일",40, (-1200, 60)),
]

today = date.today()
total_records = 0

for name, pw in users:
    # 이미 있으면 스킵
    cur.execute("SELECT id FROM users WHERE username=?", (name,))
    row = cur.fetchone()
    if row:
        user_id = row["id"]
    else:
        cur.execute("INSERT INTO users (username,password) VALUES (?,?)",
                    (name, generate_password_hash(pw)))
        user_id = cur.lastrowid

    for car_name, mileage in cars_data[name]:
        cur.execute("INSERT INTO cars (user_id,car_name,mileage) VALUES (?,?,?)",
                    (user_id, car_name, mileage))
        car_id = cur.lastrowid

        # 차량마다 랜덤 부품 4~6개 선택
        chosen = random.sample(parts_pool, random.randint(4, 6))
        for part, cycle, (d_min, d_max) in chosen:
            offset = random.randint(d_min, d_max)
            last_date = (today + timedelta(days=offset)).strftime("%Y-%m-%d")
            cur.execute(
                "INSERT INTO records (car_id,part_name,last_date,cycle_months,memo) VALUES (?,?,?,?,?)",
                (car_id, part, last_date, cycle, "")
            )
            total_records += 1

conn.commit()

# 전체 현황 출력
cur.execute("SELECT COUNT(*) FROM users")
print(f"전체 회원: {cur.fetchone()[0]}명")
cur.execute("SELECT COUNT(*) FROM cars")
print(f"전체 차량: {cur.fetchone()[0]}대")
cur.execute("SELECT COUNT(*) FROM records")
print(f"전체 정비기록: {cur.fetchone()[0]}개")
conn.close()
print("완료! 관리자(admin/admin)로 로그인해서 확인하세요.")
