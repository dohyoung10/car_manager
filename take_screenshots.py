"""발표용 PPT 스크린샷 자동 캡처 스크립트"""
import os
from playwright.sync_api import sync_playwright

SAVE_DIR = r"C:\Users\김도형\Desktop\car_manager\screenshots"
os.makedirs(SAVE_DIR, exist_ok=True)

def shot(page, name):
    path = os.path.join(SAVE_DIR, f"{name}.png")
    page.screenshot(path=path, full_page=False)
    print(f"  저장: {name}.png")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    ctx = browser.new_context(viewport={"width": 1280, "height": 800})
    page = ctx.new_page()

    # 1) 로그인 페이지
    page.goto("http://127.0.0.1:5000/login/")
    page.wait_for_load_state("networkidle")
    shot(page, "01_login")

    # 2) 도형으로 로그인 → 메인(차량 목록)
    page.fill("input[name=username]", "도형")
    page.fill("input[name=password]", "1234")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    shot(page, "02_main_vehicles")

    # 3) 차량 상세(정비기록 + D-day)
    page.goto("http://127.0.0.1:5000/car/1/")
    page.wait_for_load_state("networkidle")
    shot(page, "03_car_detail_dday")

    # 4) 정비기록 추가(부품 카드 UI) - 카드 하나 클릭해서 선택 상태 보여주기
    page.goto("http://127.0.0.1:5000/car/1/record/add/")
    page.wait_for_load_state("networkidle")
    # 엔진오일 카드 클릭
    page.evaluate("""
        const cards = document.querySelectorAll('.part-card');
        cards[0].click();
    """)
    page.wait_for_timeout(300)
    shot(page, "04_add_record_parts")

    # 5) 로그아웃 → admin 로그인 → 관리자 페이지
    page.goto("http://127.0.0.1:5000/logout/")
    page.goto("http://127.0.0.1:5000/login/")
    page.fill("input[name=username]", "admin")
    page.fill("input[name=password]", "admin")
    page.click("button[type=submit]")
    page.wait_for_load_state("networkidle")
    page.goto("http://127.0.0.1:5000/admin/")
    page.wait_for_load_state("networkidle")
    shot(page, "05_admin_page")

    browser.close()
    print("\n모든 스크린샷 완료!")
    print(f"저장 위치: {SAVE_DIR}")
