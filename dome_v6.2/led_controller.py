import time

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
LED_COUNT_PER_STRIP = 60  # 每个灯带60个灯珠
LED_COUNT_TOTAL = 120     # 总共120个灯珠
LED_PIN_1 = 18            # 第一个灯带连接到GPIO18
LED_PIN_2 = 5            # 第二个灯带连接到GPIO5
LED_FREQ_HZ = 800000      # LED信号频率（赫兹）(通常为800khz)
LED_DMA = 10              # 用于生成信号的DMA通道 (尝试10)
LED_BRIGHTNESS = 50       # 亮度设置 (0最暗，255最亮)
LED_INVERT = False        # 是否反转信号 (使用NPN晶体管电平转换时设为True)
LED_CHANNEL_1 = 0         # 第一个灯带的通道
LED_CHANNEL_2 = 1         # 第二个灯带的通道

# Basic Color Definitions
RED_COLOR = Color(255, 0, 0)
YELLOW_COLOR = Color(255, 200, 0)
BLUE_COLOR = Color(0, 0, 255)
GREEN_COLOR = Color(0, 255, 0)
OFF_COLOR = Color(0, 0, 0)

# Zone Definitions (each zone 30 LEDs - 15 from each strip)
ZONE_SIZE = 30  # 每个颜色区域30盏灯
ZONES = {
    'red': (0, ZONE_SIZE),                    # 0-29 (前15个来自strip1，后15个来自strip2)
    'yellow': (ZONE_SIZE, ZONE_SIZE * 2),     # 30-59
    'blue': (ZONE_SIZE * 2, ZONE_SIZE * 3),   # 60-89
    'green': (ZONE_SIZE * 3, ZONE_SIZE * 4)   # 90-119
}

# Create LED strip objects
strip1 = None  # GPIO18
strip2 = None  # GPIO23
if IS_RPI_ENV:
    # 初始化第一个灯带 (GPIO18)
    strip1 = PixelStrip(LED_COUNT_PER_STRIP, LED_PIN_1, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL_1)
    strip1.begin()
    
    # 初始化第二个灯带 (GPIO23)
    strip2 = PixelStrip(LED_COUNT_PER_STRIP, LED_PIN_2, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL_2)
    strip2.begin()
    
    print("两个LED灯带已初始化在树莓派上。")
    print(f"灯带1: GPIO{LED_PIN_1}, 通道{LED_CHANNEL_1}, {LED_COUNT_PER_STRIP}盏灯")
    print(f"灯带2: GPIO{LED_PIN_2}, 通道{LED_CHANNEL_2}, {LED_COUNT_PER_STRIP}盏灯")
    print(f"总计: {LED_COUNT_TOTAL}盏灯")
else:
    print("LED灯带未初始化（不在树莓派环境）。")

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

def set_led_color(led_index, color):
    """
    设置指定LED的颜色。
    参数:
        led_index (int): LED索引 (0-119)
        color: 颜色对象
    """
    if not IS_RPI_ENV:
        return
    
    if led_index < LED_COUNT_PER_STRIP:
        # 第一个灯带 (0-59)
        strip1.setPixelColor(led_index, color)
    else:
        # 第二个灯带 (60-119)
        strip2.setPixelColor(led_index - LED_COUNT_PER_STRIP, color)

def show_all_strips():
    """显示所有灯带的变化。"""
    if not IS_RPI_ENV:
        return
    
    strip1.show()
    strip2.show()

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
    print(f"点亮区域 {zone_name}: LED {start} 到 {end-1}")
    
    # 设置该区域所有LED的颜色
    for i in range(start, end):
        set_led_color(i, color)
    
    # 显示变化
    show_all_strips()
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
    print(f"关闭区域 {zone_name}: LED {start} 到 {end-1}")
    
    # 设置该区域所有LED为关闭状态
    for i in range(start, end):
        set_led_color(i, OFF_COLOR)
    
    # 显示变化
    show_all_strips()

def turn_off_all_leds():
    """关闭所有灯带上的所有LED。"""
    if not IS_RPI_ENV:
        print("模拟LED: 关闭所有LED。")
        return
    
    # 关闭第一个灯带的所有LED
    for i in range(LED_COUNT_PER_STRIP):
        strip1.setPixelColor(i, OFF_COLOR)
    
    # 关闭第二个灯带的所有LED
    for i in range(LED_COUNT_PER_STRIP):
        strip2.setPixelColor(i, OFF_COLOR)
    
    # 显示变化
    show_all_strips()
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

# 测试函数 - 用于验证硬件连接
def test_all_zones():
    """
    测试所有颜色区域，依次点亮每个区域。
    用于验证硬件连接是否正确。
    """
    print("开始测试所有LED区域...")
    test_colors = ['red', 'yellow', 'blue', 'green']
    
    for color in test_colors:
        print(f"测试 {color} 区域...")
        light_zone(color, 1.0)  # 每个区域点亮1秒
        turn_off_zone(color)
        time.sleep(0.5)  # 区域之间暂停0.5秒
    
    print("LED区域测试完成。")

# Call turn_off_all_leds when the module is imported or script exits
# This ensures LEDs are off when the application stops

# import atexit
# if IS_RPI_ENV:
#     atexit.register(turn_off_all_leds)