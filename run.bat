@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   내 차 정비 관리 시스템 서버를 시작합니다
echo ============================================

rem 파이썬 자동 감지 (py 우선, 없으면 python)
where py >nul 2>nul
if %errorlevel%==0 (set PY=py) else (set PY=python)

echo [1/2] Flask 설치 확인 중... (인터넷 필요, 처음 한 번만)
%PY% -m pip install flask >nul 2>nul

echo [2/2] 서버 시작! 크롬에서 아래 주소로 접속하세요:
echo.
echo        http://127.0.0.1:5000
echo.
echo   (종료하려면 이 창에서 Ctrl + C)
echo ============================================
%PY% app.py
pause
