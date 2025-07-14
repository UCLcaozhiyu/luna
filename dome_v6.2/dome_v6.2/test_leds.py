#!/usr/bin/env python3
"""
LED硬件测试脚本
用于验证120盏LED灯带的连接是否正确
"""

import time
import led_controller

def main():
    print("=== LED硬件测试程序 ===")
    print("此程序将测试所有120盏LED灯带")
    print("按 Ctrl+C 停止测试")
    print()
    
    try:
        # 首先关闭所有LED
        print("1. 关闭所有LED...")
        led_controller.turn_off_all_leds()
        time.sleep(1)
        
        # 测试每个颜色区域
        print("2. 测试各个颜色区域...")
        led_controller.test_all_zones()
        
        # 测试序列播放
        print("3. 测试序列播放...")
        test_sequence = ['red', 'yellow', 'blue', 'green', 'red', 'blue']
        led_controller.play_sequence(test_sequence, 0.5, 0.3)
        
        # 测试单个区域
        print("4. 测试单个区域点亮...")
        colors = ['red', 'yellow', 'blue', 'green']
        for color in colors:
            print(f"点亮 {color} 区域...")
            led_controller.light_zone(color, 2.0)
            led_controller.turn_off_zone(color)
            time.sleep(1)
        
        # 最终关闭所有LED
        print("5. 最终关闭所有LED...")
        led_controller.turn_off_all_leds()
        
        print("测试完成！")
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        led_controller.turn_off_all_leds()
        print("所有LED已关闭")
    except Exception as e:
        print(f"测试过程中出现错误: {e}")
        led_controller.turn_off_all_leds()

if __name__ == "__main__":
    main() 