#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试邀请检测功能（简化版，不依赖Flask）
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

# ========== HC-SR04 传感器设置 ==========
if IS_RPI_ENV:
    TRIG = 23
    ECHO = 24
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)

# ========== 邀请动画LED设置 ==========
if IS_RPI_ENV:
    INVITE_LED_COUNT = 120
    INVITE_LED_PIN = 18
    invite_strip = PixelStrip(INVITE_LED_COUNT, INVITE_LED_PIN, 800000, 10, False, 255, 0)
    invite_strip.begin()

# ========== 明亮柔和彩虹色列表 ==========
soft_colors = [
    Color(255, 128, 128),  # 柔红
    Color(255, 165, 100),  # 柔橙
    Color(255, 255, 128),  # 柔黄
    Color(144, 238, 144),  # 柔绿
    Color(128, 224, 224),  # 柔青
    Color(173, 216, 230),  # 柔蓝
    Color(216, 160, 240),  # 柔紫
] if IS_RPI_ENV else []

# ========== 邀请检测状态 ==========
invite_detection_active = True
game_started = False

# ========== 距离检测函数 ==========
def get_distance():
    """获取HC-SR04传感器检测的距离"""
    if not IS_RPI_ENV:
        # 模拟距离检测
        return random.uniform(50, 200)
    
    GPIO.output(TRIG, False)
    time.sleep(0.0002)
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)

    timeout = time.time() + 0.05
    while GPIO.input(ECHO) == 0:
        pulse_start = time.time()
        if pulse_start > timeout:
            return None

    while GPIO.input(ECHO) == 1:
        pulse_end = time.time()
        if pulse_end > timeout:
            return None

    duration = pulse_end - pulse_start
    distance = duration * 34300 / 2
    return round(distance, 2)

# ========== LED 亮度调节 ==========
def apply_brightness(base_color, brightness_scale):
    """应用亮度调节到LED灯带"""
    if not IS_RPI_ENV:
        print(f"💡 模拟LED: 应用亮度 {brightness_scale} 到颜色 {base_color}")
        return
    
    r = ((base_color >> 16) & 0xFF) * brightness_scale // 255
    g = ((base_color >> 8) & 0xFF) * brightness_scale // 255
    b = (base_color & 0xFF) * brightness_scale // 255
    color = Color(r, g, b)
    for i in range(invite_strip.numPixels()):
        invite_strip.setPixelColor(i, color)
    invite_strip.show()

# ========== 呼吸灯动画 ==========
def soft_breathing_once(step_delay=0.008):
    """播放一次呼吸灯动画"""
    if not IS_RPI_ENV:
        print("🌈 模拟LED: 播放呼吸灯动画")
        time.sleep(0.5)
        return
    
    color = random.choice(soft_colors)
    for b in range(0, 256, 8):  # 渐亮
        apply_brightness(color, b)
        time.sleep(step_delay)
    time.sleep(0.1)
    for b in range(255, -1, -8):  # 渐灭
        apply_brightness(color, b)
        time.sleep(step_delay)

# ========== 清空邀请动画灯带 ==========
def clear_invite_strip():
    """清空邀请动画的LED灯带"""
    if not IS_RPI_ENV:
        print("💡 模拟LED: 清空邀请动画灯带")
        return
    
    for i in range(invite_strip.numPixels()):
        invite_strip.setPixelColor(i, Color(0, 0, 0))
    invite_strip.show()

# ========== 邀请检测线程 ==========
def invite_detection_thread():
    """后台线程：检测人员靠近并播放邀请动画"""
    global invite_detection_active, game_started
    
    print("🎯 邀请检测线程启动...")
    trigger_distance = 150  # 触发距离（单位 cm）
    stay_time = 2           # 停留秒数
    animation_interval = 3  # 每3秒重复播放动画

    last_play_time = 0
    detected = False

    while invite_detection_active and not game_started:
        try:
            dist = get_distance()
            if IS_RPI_ENV:
                print(f"🔍 当前距离：{dist} cm")

            if dist and dist <= trigger_distance:
                if not detected:
                    print("✅ 检测到人员靠近，开始播放邀请动画")
                    soft_breathing_once()
                    last_play_time = time.time()
                    detected = True
                elif time.time() - last_play_time >= animation_interval:
                    print("🔁 持续检测到人员，循环播放邀请动画")
                    soft_breathing_once()
                    last_play_time = time.time()
            else:
                if detected:
                    print("👋 人员离开，停止邀请动画")
                    clear_invite_strip()
                    detected = False

            time.sleep(0.1)
        except Exception as e:
            print(f"邀请检测线程错误: {e}")
            time.sleep(1)
    
    print("🎮 邀请检测线程结束")
    clear_invite_strip()

# ========== 启动邀请检测 ==========
def start_invite_detection():
    """启动邀请检测后台线程"""
    global invite_detection_active, game_started
    invite_detection_active = True
    game_started = False
    invite_thread = threading.Thread(target=invite_detection_thread, daemon=True)
    invite_thread.start()
    print("🚀 邀请检测已启动")

# ========== 停止邀请检测 ==========
def stop_invite_detection():
    """停止邀请检测"""
    global invite_detection_active, game_started
    invite_detection_active = False
    game_started = True
    clear_invite_strip()
    print("⏹️ 邀请检测已停止")

def test_invite_detection():
    """测试邀请检测功能"""
    print("🧪 开始测试邀请检测功能...")
    
    try:
        print("✅ 成功初始化邀请检测模块")
        print("🔍 检测环境:", "Raspberry Pi" if IS_RPI_ENV else "模拟环境")
        
        # 测试距离检测
        print("📏 测试距离检测...")
        distance = get_distance()
        print(f"   当前距离: {distance} cm")
        
        # 测试LED控制
        print("💡 测试LED控制...")
        if IS_RPI_ENV:
            print("   真实LED环境，测试呼吸灯动画...")
            soft_breathing_once()
        else:
            print("   模拟环境，测试模拟动画...")
            soft_breathing_once()
        
        # 测试邀请检测线程
        print("🎯 测试邀请检测线程...")
        start_invite_detection()
        time.sleep(5)  # 运行5秒
        
        print("⏹️ 停止邀请检测...")
        stop_invite_detection()
        
        print("✅ 所有测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_invite_detection() 