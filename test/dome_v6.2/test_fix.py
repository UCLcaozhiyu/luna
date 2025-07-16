#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的邀请检测功能
"""

import time
import threading
import random

# 模拟环境检测
try:
    import RPi.GPIO as GPIO
    from rpi_ws281x import PixelStrip, Color
    IS_RPI_ENV = True
    print("✅ 检测到Raspberry Pi环境")
except ImportError:
    IS_RPI_ENV = False
    print("✅ 检测到开发环境，使用模拟功能")

# ========== 邀请检测状态 ==========
invite_detection_active = True
game_started = False
invite_thread = None

# ========== 距离检测函数 ==========
def get_distance():
    """获取HC-SR04传感器检测的距离"""
    if not IS_RPI_ENV:
        # 模拟距离检测
        return random.uniform(50, 200)
    
    try:
        GPIO.output(TRIG, False)
        time.sleep(0.0002)
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        timeout = time.time() + 0.05
        pulse_start = None
        pulse_end = None
        
        # 等待ECHO引脚变为高电平
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            if pulse_start > timeout:
                return None

        # 等待ECHO引脚变为低电平
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if pulse_end > timeout:
                return None

        # 确保两个时间戳都已获取
        if pulse_start is None or pulse_end is None:
            return None

        duration = pulse_end - pulse_start
        distance = duration * 34300 / 2
        return round(distance, 2)
        
    except Exception as e:
        print(f"距离检测错误: {e}")
        return None

# ========== 邀请检测线程 ==========
def invite_detection_thread():
    """后台线程：检测人员靠近并播放邀请动画"""
    global invite_detection_active, game_started
    
    print("🎯 邀请检测线程启动...")
    trigger_distance = 150  # 触发距离（单位 cm）
    animation_interval = 3  # 每3秒重复播放动画

    last_play_time = 0
    detected = False

    while invite_detection_active and not game_started:
        try:
            # 检查是否应该停止
            if not invite_detection_active or game_started:
                break
                
            dist = get_distance()
            print(f"🔍 当前距离：{dist} cm")

            if dist and dist <= trigger_distance:
                if not detected:
                    print("✅ 检测到人员靠近，开始播放邀请动画")
                    # 在播放动画前再次检查是否应该停止
                    if not invite_detection_active or game_started:
                        break
                    print("🌈 播放邀请动画...")
                    time.sleep(0.5)  # 模拟动画播放
                    last_play_time = time.time()
                    detected = True
                elif time.time() - last_play_time >= animation_interval:
                    print("🔁 持续检测到人员，循环播放邀请动画")
                    # 在播放动画前再次检查是否应该停止
                    if not invite_detection_active or game_started:
                        break
                    print("🌈 播放邀请动画...")
                    time.sleep(0.5)  # 模拟动画播放
                    last_play_time = time.time()
            else:
                if detected:
                    print("👋 人员离开，停止邀请动画")
                    detected = False

            time.sleep(0.1)
        except Exception as e:
            print(f"邀请检测线程错误: {e}")
            time.sleep(1)
    
    print("🎮 邀请检测线程结束")

# ========== 启动邀请检测 ==========
def start_invite_detection():
    """启动邀请检测后台线程"""
    global invite_detection_active, game_started, invite_thread
    invite_detection_active = True
    game_started = False
    invite_thread = threading.Thread(target=invite_detection_thread, daemon=True)
    invite_thread.start()
    print("🚀 邀请检测已启动")

# ========== 停止邀请检测 ==========
def stop_invite_detection():
    """停止邀请检测"""
    global invite_detection_active, game_started, invite_thread
    
    print("🛑 正在停止邀请检测...")
    invite_detection_active = False
    game_started = True
    
    # 等待线程结束（最多等待1秒）
    if invite_thread and invite_thread.is_alive():
        invite_thread.join(timeout=1.0)
        if invite_thread.is_alive():
            print("⚠️ 邀请检测线程未能在1秒内停止，但已设置停止标志")
        else:
            print("✅ 邀请检测线程已成功停止")
    
    print("⏹️ 邀请检测已停止")

def test_fix():
    """测试修复后的功能"""
    print("🧪 开始测试修复后的邀请检测功能...")
    
    try:
        # 启动邀请检测
        print("\n1️⃣ 启动邀请检测...")
        start_invite_detection()
        
        # 等待3秒让检测运行
        print("\n2️⃣ 等待3秒让检测运行...")
        time.sleep(3)
        
        # 模拟游戏开始，停止邀请检测
        print("\n3️⃣ 模拟游戏开始，停止邀请检测...")
        stop_invite_detection()
        
        # 等待确认停止
        print("\n4️⃣ 等待确认停止...")
        time.sleep(2)
        
        print("\n✅ 修复测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_fix() 