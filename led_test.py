import time
import random
from rpi_ws281x import PixelStrip, Color

# LED 配置
LED_COUNT = 60         # 总共60个灯珠
LED_PIN = 18           # GPIO18 (物理引脚12)
LED_FREQ_HZ = 800000   # LED信号频率
LED_DMA = 10           # DMA通道
LED_BRIGHTNESS = 50    # 亮度（0-255）
LED_INVERT = False     # 是否反转信号
LED_CHANNEL = 0

# 颜色定义
RED = Color(255, 0, 0)        # 纯红色
YELLOW = Color(255, 200, 0)   # 金黄色
BLUE = Color(0, 0, 255)       # 纯蓝色
GREEN = Color(0, 255, 0)      # 纯绿色
OFF = Color(0, 0, 0)          # 关闭

# 区域定义（每个区域15个灯）
ZONE_SIZE = 15
ZONES = {
    'RED': (0, ZONE_SIZE),           # 0-14
    'YELLOW': (ZONE_SIZE, ZONE_SIZE*2),    # 15-29
    'BLUE': (ZONE_SIZE*2, ZONE_SIZE*3),    # 30-44
    'GREEN': (ZONE_SIZE*3, ZONE_SIZE*4)    # 45-59
}

# 创建灯带对象
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

def light_zone(zone, color, duration=1.2):
    """点亮指定区域"""
    start, end = ZONES[zone]
    for i in range(start, end):
        strip.setPixelColor(i, color)
    strip.show()
    time.sleep(duration)

def turn_off_zone(zone):
    """关闭指定区域"""
    start, end = ZONES[zone]
    for i in range(start, end):
        strip.setPixelColor(i, OFF)
    strip.show()

def random_light_sequence():
    """随机点亮不同颜色区域"""
    colors = ['RED', 'YELLOW', 'BLUE', 'GREEN']
    try:
        while True:
            # 随机选择一个颜色
            color = random.choice(colors)
            # 点亮对应区域
            light_zone(color, globals()[color])
            # 关闭该区域
            turn_off_zone(color)
            # 短暂延迟
            time.sleep(0.8)
    except KeyboardInterrupt:
        print("\n程序结束")
        # 关闭所有灯
        for i in range(LED_COUNT):
            strip.setPixelColor(i, OFF)
        strip.show()

if __name__ == "__main__":
    print("随机点亮LED区域 - 按Ctrl+C退出")
    random_light_sequence() 
