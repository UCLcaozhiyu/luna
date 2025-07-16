
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

# ========== 柔和颜色列表 ==========
soft_colors = [
    Color(255, 182, 193),   # 浅粉红
    Color(221, 160, 221),   # 浅紫色
    Color(173, 216, 230),   # 浅蓝色（保留）
    Color(144, 238, 144),   # 浅绿色
    Color(255, 255, 153),   # 浅黄色
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
def apply_brightness(base_color, brightness):
    r = ((base_color >> 16) & 0xFF) * brightness // 255
    g = ((base_color >> 8) & 0xFF) * brightness // 255
    b = (base_color & 0xFF) * brightness // 255
    color = Color(r, g, b)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()

# ========== 柔和呼吸灯动画 ==========
def soft_breathing_once(step_delay=0.015):
    color = random.choice(soft_colors)
    for b in range(0, 256, 5):
        apply_brightness(color, b)
        time.sleep(step_delay)
    for b in range(255, -1, -5):
        apply_brightness(color, b)
        time.sleep(step_delay)

# ========== 清空灯带 ==========
def clear_strip():
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# ========== 主逻辑循环 ==========
if __name__ == "__main__":
    try:
        print("✨ 呼吸灯邀请模式启动中... 持续靠近 1.5m 可触发动画")
        check_interval = 3      # 每 3 秒检测一次
        trigger_distance = 150  # 距离阈值（单位 cm）
        stay_time = 2           # 靠近持续秒数

        while True:
            print("🔍 检测中...")
            dist1 = get_distance()
            if dist1 and dist1 <= trigger_distance:
                print(f"👣 首次检测到靠近（{dist1} cm），等待确认...")
                time.sleep(stay_time)
                dist2 = get_distance()
                if dist2 and dist2 <= trigger_distance:
                    print(f"✅ 用户持续靠近 {stay_time} 秒，播放柔和动画")
                    soft_breathing_once()
                else:
                    print("❌ 用户离开，忽略")
            else:
                print("🕳️ 无人靠近")

            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n🧹 程序终止，清理 GPIO 和灯光...")
        clear_strip()
        GPIO.cleanup()
