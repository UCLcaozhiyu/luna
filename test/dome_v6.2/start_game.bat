@echo off
chcp 65001 >nul
echo 🎮 西蒙游戏服务器启动脚本
echo ================================

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

REM 检查必要的Python包
echo 📦 检查Python依赖...
python -c "import flask, flask_socketio" 2>nul
if errorlevel 1 (
    echo ⚠️  警告: 缺少Flask依赖，尝试安装...
    pip install flask flask-socketio
)

REM 检查当前目录
if not exist "app.py" (
    echo ❌ 错误: 未找到app.py文件，请确保在正确的目录中运行此脚本
    pause
    exit /b 1
)

echo ✅ 环境检查完成
echo 🚀 启动游戏服务器...
echo 📡 服务器将在 http://localhost:5000 启动
echo 🎯 邀请检测已激活（模拟模式）
echo ⏹️  按 Ctrl+C 停止服务器
echo ================================

REM 启动服务器
python app.py

pause 