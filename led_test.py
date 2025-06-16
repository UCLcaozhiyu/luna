import time
from rpi_ws281x import PixelStrip, Color

# LED 配置
LED_COUNT = 60         # 灯珠数量，根据你的实际灯带长度修改
LED_PIN = 18           # GPIO18 (物理引脚12)
LED_FREQ_HZ = 800000   # LED信号频率（一般800kHz）
LED_DMA = 10           # DMA通道
LED_BRIGHTNESS = 50    # 亮度（0-255）
LED_INVERT = False     # 是否反转信号
LED_CHANNEL = 0

# 创建灯带对象
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

print('按Ctrl-C退出程序')

try:
    while True:
        # 跑马灯效果
        for i in range(strip.numPixels()):
            strip.setPixelColor(i, Color(255, 0, 0))  # 当前灯珠亮红色
            if i > 0:
                strip.setPixelColor(i-1, Color(0, 0, 0))  # 上一个灯珠熄灭
            strip.show()
            time.sleep(0.05)
        # 熄灭最后一个
        strip.setPixelColor(strip.numPixels()-1, Color(0, 0, 0))
except KeyboardInterrupt:
    # 退出时熄灭所有灯
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show() 
