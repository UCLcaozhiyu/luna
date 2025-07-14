
import RPi.GPIO as GPIO
import time
import random
from rpi_ws281x import PixelStrip, Color

# ========== LED 设置 ==========
LED_COUNT = 120
LED_PIN = 18
strip = PixelStrip(LED_COUNT, LED_PIN, 800000, 10, False, 255, 0)
strip.begin()

# ========== HC-SR04 设置 ==========
TRIG = 23
ECHO = 24
GPIO.setmode(GPIO.BCM)
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# ========== 明亮柔和彩虹色列表 ==========
soft_colors = [
    Color(255, 128, 128),  # 柔红
    Color(255, 165, 100),  # 柔橙
    Color(255, 255, 128),  # 柔黄
    Color(144, 238, 144),  # 柔绿
    Color(128, 224, 224),  # 柔青
    Color(173, 216, 230),  # 柔蓝
    Color(216, 160, 240),  # 柔紫
]

# ========== 距离检测 ==========
def get_distance():
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
    r = ((base_color >> 16) & 0xFF) * brightness_scale // 255
    g = ((base_color >> 8) & 0xFF) * brightness_scale // 255
    b = (base_color & 0xFF) * brightness_scale // 255
    color = Color(r, g, b)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()

# ========== 呼吸灯动画 ==========
def soft_breathing_once(step_delay=0.008):
    color = random.choice(soft_colors)
    for b in range(0, 256, 8):  # 渐亮
        apply_brightness(color, b)
        time.sleep(step_delay)
    time.sleep(0.1)
    for b in range(255, -1, -8):  # 渐灭
        apply_brightness(color, b)
        time.sleep(step_delay)

# ========== 清空灯带 ==========
def clear_strip():
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# ========== 主逻辑 ==========
if __name__ == "__main__":
    try:
        print("✨ 呼吸灯邀请模式 v3 启动中... 靠近后每3秒播放一次")
        trigger_distance = 150  # 触发距离（单位 cm）
        stay_time = 2           # 停留秒数
        animation_interval = 3  # 每3秒重复播放动画

        last_play_time = 0
        detected = False

        while True:
            dist = get_distance()
            print("🔍 当前距离：", dist)

            if dist and dist <= trigger_distance:
                if not detected:
                    print("✅ 首次靠近，播放动画")
                    soft_breathing_once()
                    last_play_time = time.time()
                    detected = True
                elif time.time() - last_play_time >= animation_interval:
                    print("🔁 持续靠近，循环播放动画")
                    soft_breathing_once()
                    last_play_time = time.time()
            else:
                if detected:
                    print("👋 人离开，清除状态")
                    clear_strip()
                    detected = False

            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n🧹 程序终止，清理 GPIO 和灯光...")
        clear_strip()
        GPIO.cleanup()
