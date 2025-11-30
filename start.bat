@echo off

cd backend
start "后端服务" python server.py


timeout /t 5 /nobreak >nul


cd ..\web
start "前端服务" python serve.py


timeout /t 3 /nobreak >nul


start "" "http://localhost:3000"

pause >nul