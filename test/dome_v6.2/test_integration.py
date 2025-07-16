#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试邀请检测功能集成
"""

import time
import threading
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_invite_detection():
    """测试邀请检测功能"""
    print("🧪 开始测试邀请检测功能...")
    
    try:
        # 导入app模块
        import app
        
        print("✅ 成功导入app模块")
        print("🔍 检测环境:", "Raspberry Pi" if app.IS_RPI_ENV else "模拟环境")
        
        # 测试距离检测
        print("📏 测试距离检测...")
        distance = app.get_distance()
        print(f"   当前距离: {distance} cm")
        
        # 测试LED控制
        print("💡 测试LED控制...")
        if app.IS_RPI_ENV:
            print("   真实LED环境，测试呼吸灯动画...")
            app.soft_breathing_once()
        else:
            print("   模拟环境，跳过LED测试")
        
        # 测试邀请检测线程
        print("🎯 测试邀请检测线程...")
        app.start_invite_detection()
        time.sleep(3)  # 运行3秒
        
        print("⏹️ 停止邀请检测...")
        app.stop_invite_detection()
        
        print("✅ 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_invite_detection() 