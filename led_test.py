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

# 基础颜色定义
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

def generate_random_color():
    """生成随机颜色"""
    r = random.randint(0, 255)
    g = random.randint(0, 255)
    b = random.randint(0, 255)
    return Color(r, g, b)

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

def show_sequence(sequence, duration):
    """显示颜色序列"""
    for color in sequence:
        light_zone(color['zone'], color['color'], duration)
        turn_off_zone(color['zone'])
        time.sleep(0.8)

def get_level_config(level):
    """根据关卡返回游戏配置"""
    base_colors = [
        {'zone': 'RED', 'color': RED},
        {'zone': 'YELLOW', 'color': YELLOW},
        {'zone': 'BLUE', 'color': BLUE},
        {'zone': 'GREEN', 'color': GREEN}
    ]
    
    # 基础配置
    config = {
        'colors': base_colors.copy(),
        'duration': 1.2,  # 默认显示时间
        'sequence_length': 3  # 默认序列长度
    }
    
    # 根据关卡调整配置
    if level >= 2:
        # 第二关：添加一个随机颜色
        random_zone = random.choice(['RED', 'YELLOW', 'BLUE', 'GREEN'])
        config['colors'].append({
            'zone': random_zone,
            'color': generate_random_color()
        })
        config['sequence_length'] = 4
    
    if level >= 3:
        # 第三关：再添加一个随机颜色
        random_zone = random.choice(['RED', 'YELLOW', 'BLUE', 'GREEN'])
        config['colors'].append({
            'zone': random_zone,
            'color': generate_random_color()
        })
        config['sequence_length'] = 5
    
    if level >= 4:
        # 第四关：再添加一个随机颜色
        random_zone = random.choice(['RED', 'YELLOW', 'BLUE', 'GREEN'])
        config['colors'].append({
            'zone': random_zone,
            'color': generate_random_color()
        })
        config['sequence_length'] = 6
    
    if level >= 5:
        # 第五关：加快显示速度
        config['duration'] = 0.8
    
    return config

def play_game():
    """开始游戏"""
    print("进阶版 Simon LED Game - 按Ctrl+C退出")
    level = 1
    
    try:
        while True:
            print(f"\n=== 第 {level} 关 ===")
            config = get_level_config(level)
            
            # 生成随机序列
            sequence = random.choices(config['colors'], k=config['sequence_length'])
            
            # 显示序列
            print("观察序列...")
            show_sequence(sequence, config['duration'])
            
            # 等待一段时间后进入下一关
            print("进入下一关...")
            time.sleep(2)
            level += 1
            
    except KeyboardInterrupt:
        print("\n游戏结束")
        # 关闭所有灯
        for i in range(LED_COUNT):
            strip.setPixelColor(i, OFF)
        strip.show()

if __name__ == "__main__":
    play_game()
