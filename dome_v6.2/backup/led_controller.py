// ... existing code ...
# --- LED Configuration ---
LED_COUNT_TOTAL = 60     # 只用一根灯带，总共60个灯珠
LED_PIN_1 = 18           # 灯带连接到GPIO18
LED_FREQ_HZ = 800000     # LED信号频率（赫兹）(通常为800khz)
LED_DMA = 10             # 用于生成信号的DMA通道 (尝试10)
LED_BRIGHTNESS = 50      # 亮度设置 (0最暗，255最亮)
LED_INVERT = False       # 是否反转信号 (使用NPN晶体管电平转换时设为True)
LED_CHANNEL_1 = 0        # 灯带的通道

# Basic Color Definitions
RED_COLOR = Color(255, 0, 0)
YELLOW_COLOR = Color(255, 200, 0)
BLUE_COLOR = Color(0, 0, 255)
GREEN_COLOR = Color(0, 255, 0)
OFF_COLOR = Color(0, 0, 0)

# Zone Definitions (每个区域15盏灯)
ZONE_SIZE = 15
ZONES = {
    'red': (0, ZONE_SIZE),                    # 0-14
    'yellow': (ZONE_SIZE, ZONE_SIZE * 2),     # 15-29
    'blue': (ZONE_SIZE * 2, ZONE_SIZE * 3),   # 30-44
    'green': (ZONE_SIZE * 3, ZONE_SIZE * 4)   # 45-59
}

# 创建LED灯带对象
strip1 = None  # GPIO18
if IS_RPI_ENV:
    strip1 = PixelStrip(LED_COUNT_TOTAL, LED_PIN_1, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL_1)
    strip1.begin()
    print("LED灯带已初始化在树莓派上。")
    print(f"灯带: GPIO{LED_PIN_1}, 通道{LED_CHANNEL_1}, {LED_COUNT_TOTAL}盏灯")
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
        led_index (int): LED索引 (0-59)
        color: 颜色对象
    """
    if not IS_RPI_ENV:
        return
    if 0 <= led_index < LED_COUNT_TOTAL:
        strip1.setPixelColor(led_index, color)

def show_all_strips():
    """显示灯带的变化。"""
    if not IS_RPI_ENV:
        return
    strip1.show()

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
    for i in range(start, end):
        set_led_color(i, color)
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
    for i in range(start, end):
        set_led_color(i, OFF_COLOR)
    show_all_strips()

def turn_off_all_leds():
    """关闭灯带上的所有LED。"""
    if not IS_RPI_ENV:
        print("模拟LED: 关闭所有LED。")
        return
    for i in range(LED_COUNT_TOTAL):
        strip1.setPixelColor(i, OFF_COLOR)
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
        time.sleep(off_duration_between_colors)
    turn_off_all_leds()
    print("LED序列播放完成。")
// ... existing code ...