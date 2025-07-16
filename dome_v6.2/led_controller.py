import time
import RPi.GPIO as GPIO
import random
import threading

# Attempt to import rpi_ws281x for LED control.
# If not on a Raspberry Pi, a dummy class will be used.
try:
    from rpi_ws281x import PixelStrip, Color
    print("rpi_ws281x imported successfully.")
    IS_RPI_ENV = True
except ImportError:
    print("rpi_ws281x not found. Running in non-Raspberry Pi environment. LED control will be simulated.")
    IS_RPI_ENV = False

    # Dummy classes for non-Raspberry Pi environment
    class Color:
        def __init__(self, r, g, b):
            pass

    class PixelStrip:
        def __init__(self, *args, **kwargs):
            pass
        def begin(self):
            pass
        def setPixelColor(self, index, color):
            pass
        def show(self):
            pass

# --- LED Configuration ---
LED_COUNT = 120      # 总共60个灯珠
LED_PIN = 18        # 连接到像素的GPIO引脚 (18使用PWM!)
LED_FREQ_HZ = 800000 # LED信号频率（赫兹）(通常为800khz)
LED_DMA = 10        # 用于生成信号的DMA通道 (尝试10)
LED_BRIGHTNESS = 50 # 亮度设置 (0最暗，255最亮)
LED_INVERT = False  # 是否反转信号 (使用NPN晶体管电平转换时设为True)
LED_CHANNEL = 0

# Basic Color Definitions
RED_COLOR = Color(255, 0, 0)
YELLOW_COLOR = Color(255, 200, 0)
BLUE_COLOR = Color(0, 0, 255)
GREEN_COLOR = Color(0, 255, 0)
OFF_COLOR = Color(0, 0, 0)

# Zone Definitions (each zone 15 LEDs)
ZONE_SIZE = 30
ZONES = {
    'red': (0, ZONE_SIZE),            # 0-14
    'yellow': (ZONE_SIZE, ZONE_SIZE * 2),    # 15-29
    'blue': (ZONE_SIZE * 2, ZONE_SIZE * 3),  # 30-44
    'green': (ZONE_SIZE * 3, ZONE_SIZE * 4) # 45-59
}

# Create LED strip object
strip = None
if IS_RPI_ENV:
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    print("LED strip initialized on Raspberry Pi.")
else:
    print("LED strip not initialized (not on Raspberry Pi).")

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
    Color(173, 216, 230),   # 浅蓝色
    Color(144, 238, 144),   # 浅绿色
    Color(255, 255, 153),   # 浅黄色
]

def get_color_object(color_name):
    """根据颜色名称返回颜色对象。"""
    colors = {
        'red': RED_COLOR,
        'yellow': YELLOW_COLOR,
        'blue': BLUE_COLOR,
        'green': GREEN_COLOR
    }
    return colors.get(color_name, OFF_COLOR)

def light_zone(zone_name, duration=0.8):
    """
    点亮指定LED区域并持续一段时间。
    参数:
        zone_name (str): 区域名称 ('red', 'yellow', 'blue', 'green')。
        duration (float): 区域保持点亮的时间，单位为秒。
    """
    color = get_color_object(zone_name)
    if not IS_RPI_ENV:
        print(f"模拟LED: 点亮区域 {zone_name}，颜色 {color}，持续 {duration} 秒")
        time.sleep(duration)
        return

    if zone_name not in ZONES:
        print(f"错误: 区域 '{zone_name}' 未定义。")
        return

    start, end = ZONES[zone_name]
    for i in range(start, end):
        strip.setPixelColor(i, color)
    strip.show()
    time.sleep(duration)

def turn_off_zone(zone_name):
    """
    关闭指定LED区域。
    参数:
        zone_name (str): 要关闭的区域名称。
    """
    if not IS_RPI_ENV:
        print(f"模拟LED: 关闭区域 {zone_name}")
        return

    if zone_name not in ZONES:
        print(f"错误: 区域 '{zone_name}' 未定义。")
        return

    start, end = ZONES[zone_name]
    for i in range(start, end):
        strip.setPixelColor(i, OFF_COLOR)
    strip.show()

def turn_off_all_leds():
    """关闭灯带上的所有LED。"""
    if not IS_RPI_ENV:
        print("模拟LED: 关闭所有LED。")
        return
    for i in range(LED_COUNT):
        strip.setPixelColor(i, OFF_COLOR)
    strip.show()
    print("所有LED已关闭。")

def play_sequence(sequence, light_duration_per_color=0.8, off_duration_between_colors=0.2):
    """
    在LED灯带上播放颜色序列。
    对于序列中的每个颜色，它会点亮相应的区域，
    然后关闭该区域，并在两者之间有短暂的暂停。
    最后，它确保所有LED都已关闭。

    参数:
        sequence (list): 颜色名称列表 (例如, ['red', 'blue', 'yellow'])。
        light_duration_per_color (float): 每个LED区域保持点亮的时间 (秒)。
        off_duration_between_colors (float): 关闭一个区域与点亮序列中下一个区域之间的时间 (秒)。
    """
    print(f"播放LED序列: {sequence}")
    for color_name in sequence:
        light_zone(color_name, light_duration_per_color)
        turn_off_zone(color_name)
        time.sleep(off_duration_between_colors) # 颜色之间的小暂停

    turn_off_all_leds() # 确保在序列播放结束时所有LED都已关闭
    print("LED序列播放完成。")

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

def apply_brightness(base_color, brightness):
    r = ((base_color >> 16) & 0xFF) * brightness // 255
    g = ((base_color >> 8) & 0xFF) * brightness // 255
    b = (base_color & 0xFF) * brightness // 255
    color = Color(r, g, b)
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()

def soft_breathing_once(step_delay=0.015, stop_event=None):
    color = random.choice(soft_colors)
    for b in range(0, 256, 5):
        if stop_event and stop_event.is_set():
            break
        apply_brightness(color, b)
        time.sleep(step_delay)
    for b in range(255, -1, -5):
        if stop_event and stop_event.is_set():
            break
        apply_brightness(color, b)
        time.sleep(step_delay)

def clear_strip():
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def run_invite_animation():
    """
    游戏启动前的邀请动画：检测到有人靠近时，播放柔和呼吸灯动画。
    """
    print("✨ 呼吸灯邀请模式启动中... 持续靠近 1.5m 可触发动画")
    check_interval = 3      # 每 3 秒检测一次
    trigger_distance = 150  # 距离阈值（单位 cm）
    stay_time = 2           # 靠近持续秒数
    try:
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
                    time.sleep(2)  # 停留2秒
                    clear_strip()  # 动画后关闭所有LED
                    break  # 播放一次后退出，进入主程序
                else:
                    print("❌ 用户离开，忽略")
            else:
                print("🕳️ 无人靠近")
            time.sleep(check_interval)
    except KeyboardInterrupt:
        print("\n🧹 程序终止，清理 GPIO 和灯光...")
        clear_strip()
        GPIO.cleanup()

def wait_for_start_with_animation(timeout=120, stop_event=None):
    """
    动画循环播放，直到stop_event被设置或超时（单位秒）。
    返回True表示用户点击start，False表示超时。
    """
    print(f"进入等待start动画模式，最长等待{timeout}秒...")
    start_time = time.time()
    while True:
        if stop_event and stop_event.is_set():
            print("检测到start按钮被点击，停止动画。")
            clear_strip()
            return True
        if time.time() - start_time > timeout:
            print("等待start超时，停止动画，回到靠近检测状态。")
            clear_strip()
            return False
        soft_breathing_once(stop_event=stop_event)
        time.sleep(0.2)  # 动画间隔


# Call turn_off_all_leds when the module is imported or script exits
# This ensures LEDs are off when the application stops

# import atexit
# if IS_RPI_ENV:
#     atexit.register(turn_off_all_leds)