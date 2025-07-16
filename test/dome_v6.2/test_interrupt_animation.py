#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试动画中断功能 - 在动画播放过程中停止
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

# ========== 距离检测函数 ==========
def get_distance():
    """获取HC-SR04传感器检测的距离"""
    if not IS_RPI_ENV:
        # 模拟距离检测 - 总是返回近距离以触发动画
        return random.uniform(50, 100)
    
    # 真实传感器代码...
    return random.uniform(50, 100)

# ========== LED 亮度调节 ==========
def apply_brightness(base_color, brightness_scale):
    """应用亮度调节到LED灯带"""
    if not IS_RPI_ENV:
        print(f"💡 模拟LED: 应用亮度 {brightness_scale} 到颜色 {base_color}")
        return
    
    # 真实LED控制代码...
    pass

# ========== 呼吸灯动画 ==========
def soft_breathing_once(step_delay=0.008):
    """播放一次呼吸灯动画"""
    if not IS_RPI_ENV:
        print("🌈 模拟LED: 播放呼吸灯动画")
        # 模拟动画播放时间 - 更长的动画以便测试中断
        for i in range(20):  # 模拟20步动画
            # 检查是否应该停止动画
            if not invite_detection_active or game_started:
                print("🛑 动画被中断")
                return
            print(f"   动画步骤 {i+1}/20")
            time.sleep(0.2)  # 每步0.2秒，总共4秒
        return
    
    # 真实动画代码...
    color = random.choice(soft_colors)
    for b in range(0, 256, 8):  # 渐亮
        # 检查是否应该停止动画
        if not invite_detection_active or game_started:
            print("🛑 动画被中断")
            return
        apply_brightness(color, b)
        time.sleep(step_delay)
    
    time.sleep(0.1)
    
    for b in range(255, -1, -8):  # 渐灭
        # 检查是否应该停止动画
        if not invite_detection_active or game_started:
            print("🛑 动画被中断")
            return
        apply_brightness(color, b)
        time.sleep(step_delay)

# ========== 清空邀请动画灯带 ==========
def clear_invite_strip():
    """清空邀请动画的LED灯带"""
    if not IS_RPI_ENV:
        print("💡 模拟LED: 清空邀请动画灯带")
        return
    
    # 真实清空代码...
    pass

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
                    soft_breathing_once()
                    last_play_time = time.time()
                    detected = True
                elif time.time() - last_play_time >= animation_interval:
                    print("🔁 持续检测到人员，循环播放邀请动画")
                    # 在播放动画前再次检查是否应该停止
                    if not invite_detection_active or game_started:
                        break
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
    
    # 立即清空LED灯带，停止动画
    clear_invite_strip()
    
    # 等待线程结束（最多等待1秒）
    if invite_thread and invite_thread.is_alive():
        invite_thread.join(timeout=1.0)
        if invite_thread.is_alive():
            print("⚠️ 邀请检测线程未能在1秒内停止，但已设置停止标志")
        else:
            print("✅ 邀请检测线程已成功停止")
    
    print("⏹️ 邀请检测已停止")

def test_animation_interrupt():
    """测试动画中断功能"""
    print("🧪 开始测试动画中断功能...")
    
    try:
        # 启动邀请检测
        print("\n1️⃣ 启动邀请检测...")
        start_invite_detection()
        
        # 等待1秒让动画开始
        print("\n2️⃣ 等待动画开始...")
        time.sleep(1)
        
        # 在动画播放过程中中断（动画需要4秒，我们在1.5秒后中断）
        print("\n3️⃣ 在动画播放过程中中断（1.5秒后）...")
        time.sleep(0.5)  # 再等0.5秒，总共1.5秒
        
        # 模拟游戏开始，停止邀请检测
        print("\n4️⃣ 模拟游戏开始，停止邀请检测...")
        stop_invite_detection()
        
        # 等待确认停止
        print("\n5️⃣ 等待确认停止...")
        time.sleep(1)
        
        print("\n✅ 动画中断功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_animation_interrupt() 