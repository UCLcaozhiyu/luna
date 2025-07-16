#!/bin/bash

# 西蒙游戏服务器启动脚本
# 适用于树莓派环境

echo "🎮 西蒙游戏服务器启动脚本"
echo "================================"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到Python3，请先安装Python3"
    exit 1
fi

# 检查必要的Python包
echo "📦 检查Python依赖..."
python3 -c "import flask, flask_socketio" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  警告: 缺少Flask依赖，尝试安装..."
    pip3 install flask flask-socketio
fi

# 检查树莓派特定依赖
python3 -c "import RPi.GPIO, rpi_ws281x" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  警告: 缺少树莓派依赖，尝试安装..."
    pip3 install RPi.GPIO rpi_ws281x
fi

# 检查当前目录
if [ ! -f "app.py" ]; then
    echo "❌ 错误: 未找到app.py文件，请确保在正确的目录中运行此脚本"
    exit 1
fi

echo "✅ 环境检查完成"
echo "🚀 启动游戏服务器..."

# 设置环境变量
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

# 启动服务器
echo "📡 服务器将在 http://0.0.0.0:5000 启动"
echo "🎯 邀请检测已激活，等待玩家靠近..."
echo "⏹️  按 Ctrl+C 停止服务器"
echo "================================"

# 使用sudo运行（如果需要GPIO权限）
if [ "$EUID" -ne 0 ]; then
    echo "🔐 尝试使用sudo权限启动（用于GPIO访问）..."
    sudo python3 app.py
else
    python3 app.py
fi 