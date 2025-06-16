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
RED = Color(255, 0, 0)
YELLOW = Color(255, 255, 0)
BLUE = Color(0, 0, 255)
GREEN = Color(0, 255, 0)
OFF = Color(0, 0, 0)

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

class SimonGame:
    def __init__(self):
        self.sequence = []
        self.player_sequence = []
        self.level = 1
        self.colors = ['RED', 'YELLOW', 'BLUE', 'GREEN']
        
    def light_zone(self, zone, color, duration=0.5):
        """点亮指定区域"""
        start, end = ZONES[zone]
        for i in range(start, end):
            strip.setPixelColor(i, color)
        strip.show()
        time.sleep(duration)
        
    def turn_off_zone(self, zone):
        """关闭指定区域"""
        start, end = ZONES[zone]
        for i in range(start, end):
            strip.setPixelColor(i, OFF)
        strip.show()
        
    def show_sequence(self):
        """显示当前序列"""
        for color in self.sequence:
            self.light_zone(color, globals()[color])
            self.turn_off_zone(color)
            time.sleep(0.3)
            
    def add_to_sequence(self):
        """添加新的颜色到序列"""
        self.sequence.append(random.choice(self.colors))
        
    def reset_game(self):
        """重置游戏"""
        self.sequence = []
        self.player_sequence = []
        self.level = 1
        self.add_to_sequence()
        
    def play(self):
        """开始游戏"""
        print("Simon LED Game - 按Ctrl+C退出")
        self.reset_game()
        
        try:
            while True:
                print(f"\nLevel {self.level}")
                print("观察序列...")
                self.show_sequence()
                
                # 这里应该添加玩家输入逻辑
                # 由于树莓派没有按钮，我们可以用键盘输入模拟
                # 实际使用时可以添加按钮或触摸传感器
                print("\n请输入颜色序列 (R/Y/B/G):")
                player_input = input().upper()
                
                # 将输入转换为颜色名称
                input_map = {'R': 'RED', 'Y': 'YELLOW', 'B': 'BLUE', 'G': 'GREEN'}
                self.player_sequence = [input_map[c] for c in player_input if c in input_map]
                
                # 检查玩家输入
                if self.player_sequence == self.sequence:
                    print("正确！进入下一关")
                    self.level += 1
                    self.add_to_sequence()
                else:
                    print("错误！游戏结束")
                    # 显示错误动画
                    for _ in range(3):
                        for color in self.colors:
                            self.light_zone(color, RED)
                        time.sleep(0.2)
                        for color in self.colors:
                            self.turn_off_zone(color)
                        time.sleep(0.2)
                    self.reset_game()
                    
        except KeyboardInterrupt:
            print("\n游戏结束")
            # 关闭所有灯
            for i in range(LED_COUNT):
                strip.setPixelColor(i, OFF)
            strip.show()

if __name__ == "__main__":
    game = SimonGame()
    game.play()
