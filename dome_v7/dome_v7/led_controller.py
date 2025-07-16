import time
import threading

# Attempt to import rpi_ws281x for LED control.
try:
    from rpi_ws281x import PixelStrip, Color
    print("rpi_ws281x imported successfully.")
    IS_RPI_ENV = True
except ImportError:
    print("rpi_ws281x not found. Running in simulation mode.")
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
LED_COUNT = 60      # 每段灯带60个灯珠
LED_PIN = 18        # 第一段灯带 GPIO
LED_PIN2 = 23       # 第二段灯带 GPIO（新增）
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
ZONE_SIZE = 15
ZONES = {
    'red': (0, ZONE_SIZE),            # 0-14
    'yellow': (ZONE_SIZE, ZONE_SIZE * 2),    # 15-29
    'blue': (ZONE_SIZE * 2, ZONE_SIZE * 3),  # 30-44
    'green': (ZONE_SIZE * 3, ZONE_SIZE * 4) # 45-59
}

# Create LED strip object
strip = None
strip2 = None  # 新增
if IS_RPI_ENV:
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip2 = PixelStrip(LED_COUNT, LED_PIN2, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)  # 新增
    strip.begin()
    strip2.begin()  # 新增
    print("LED strip initialized on Raspberry Pi.")
else:
    print("LED strip not initialized (not on Raspberry Pi).")

# --- LED Control Functions ---
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
        if i < 60:
            strip.setPixelColor(i, color)
        else:
            strip2.setPixelColor(i - 60, color)
    strip.show()
    strip2.show()
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
        if i < 60:
            strip.setPixelColor(i, OFF_COLOR)
        else:
            strip2.setPixelColor(i - 60, OFF_COLOR)
    strip.show()
    strip2.show()

def turn_off_all_leds():
    """关闭灯带上的所有LED。"""
    if not IS_RPI_ENV:
        print("模拟LED: 关闭所有LED。")
        return
    for i in range(120):
        if i < 60:
            strip.setPixelColor(i, OFF_COLOR)
        else:
            strip2.setPixelColor(i - 60, OFF_COLOR)
    strip.show()
    strip2.show()
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

# --- Idle Water Ripple Animation ---

idle_animation_active = True

def idle_water_ripple_animation():
    center = 60  # 假设总共120个灯
    max_radius = 30
    color = BLUE_COLOR
    while idle_animation_active:
        for radius in range(0, max_radius):
            if not idle_animation_active:
                break
            turn_off_all_leds()
            for offset in [-radius, radius]:
                for base in [center - 1, center]:
                    led_index = base + offset
                    if 0 <= led_index < 120:
                        if led_index < 60:
                            strip.setPixelColor(led_index, color)
                        else:
                            strip2.setPixelColor(led_index - 60, color)
            strip.show()
            strip2.show()
            time.sleep(0.05)

if IS_RPI_ENV:
    threading.Thread(target=idle_water_ripple_animation, daemon=True).start()

