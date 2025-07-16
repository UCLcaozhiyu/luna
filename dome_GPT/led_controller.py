
import time, threading, random, atexit

try:
    from rpi_ws281x import PixelStrip, Color
    IS_RPI_ENV=True
    print("rpi_ws281x imported successfully.")
except ImportError:
    IS_RPI_ENV=False
    print("rpi_ws281x not found. Using simulation mode.")
    class Color:
        def __init__(self,r,g,b): self.r,self.g,self.b=r,g,b
    class PixelStrip:
        def __init__(self,*a,**k): pass
        def begin(self): pass
        def setPixelColor(self,i,c): pass
        def show(self): pass

# ===== LED 配置 =====
LED_COUNT=120
LED_PIN=18
LED_FREQ_HZ=800000
LED_DMA=10
LED_BRIGHTNESS=50
LED_INVERT=False
LED_CHANNEL=0

ZONE_SIZE=30
ZONES={
    'red':(0,ZONE_SIZE),
    'yellow':(ZONE_SIZE,ZONE_SIZE*2),
    'blue':(ZONE_SIZE*2,ZONE_SIZE*3),
    'green':(ZONE_SIZE*3,ZONE_SIZE*4)
}

strip=None
if IS_RPI_ENV:
    strip=PixelStrip(LED_COUNT,LED_PIN,LED_FREQ_HZ,LED_DMA,LED_INVERT,LED_BRIGHTNESS,LED_CHANNEL)
    strip.begin()
else:
    print("LED strip simulation only.")

RED_COLOR=Color(255,0,0)
YELLOW_COLOR=Color(255,200,0)
BLUE_COLOR=Color(0,0,255)
GREEN_COLOR=Color(0,255,0)
OFF_COLOR=Color(0,0,0)

def safe_show():
    try:
        if IS_RPI_ENV: strip.show()
    except Exception as e:
        print(f"LED show error: {e}")

def get_color_object(name):
    return {'red':RED_COLOR,'yellow':YELLOW_COLOR,'blue':BLUE_COLOR,'green':GREEN_COLOR}.get(name,OFF_COLOR)

def light_zone(zone_name,duration=0.8):
    color=get_color_object(zone_name)
    if not IS_RPI_ENV:
        print(f"[SIM] Light zone {zone_name} for {duration}s")
        time.sleep(duration)
        return
    if zone_name not in ZONES: return
    start,end=ZONES[zone_name]
    for i in range(start,end): strip.setPixelColor(i,color)
    safe_show(); time.sleep(duration)

def turn_off_zone(zone_name):
    if not IS_RPI_ENV:
        print(f"[SIM] Turn off zone {zone_name}")
        return
    if zone_name not in ZONES: return
    start,end=ZONES[zone_name]
    for i in range(start,end): strip.setPixelColor(i,OFF_COLOR)
    safe_show()

def turn_off_all_leds():
    if not IS_RPI_ENV:
        print("[SIM] Turn off all LEDs")
        return
    for i in range(LED_COUNT): strip.setPixelColor(i,OFF_COLOR)
    safe_show()
    print("✅ All LEDs turned off.")

def play_sequence(sequence,light_duration_per_color=0.8,off_duration_between_colors=0.2):
    print(f"▶ Playing LED sequence: {sequence}")
    for color_name in sequence:
        light_zone(color_name,light_duration_per_color)
        turn_off_zone(color_name)
        time.sleep(off_duration_between_colors)
    turn_off_all_leds()
    print("✅ LED sequence finished.")

# ===== 呼吸灯模式 =====
soft_colors=[
    Color(255,128,128),Color(255,165,100),Color(255,255,128),
    Color(144,238,144),Color(128,224,224),Color(173,216,230),Color(216,160,240)
]

breathing_active=False
breathing_thread=None

def apply_brightness(base_color,brightness_scale):
    r=(base_color.r*brightness_scale)//255
    g=(base_color.g*brightness_scale)//255
    b=(base_color.b*brightness_scale)//255
    color=Color(r,g,b)
    if IS_RPI_ENV:
        for i in range(LED_COUNT): strip.setPixelColor(i,color)
        safe_show()

def soft_breathing_once(step_delay=0.01):
    global breathing_active
    color=random.choice(soft_colors)
    for b in range(0,256,8):
        if not breathing_active: return  # 立刻退出
        apply_brightness(color,b); time.sleep(step_delay)
    for b in range(255,-1,-8):
        if not breathing_active: return
        apply_brightness(color,b); time.sleep(step_delay)

def breathing_loop():
    print("✨ Breathing light started")
    while breathing_active:
        soft_breathing_once()
        time.sleep(0.2)
    print("❌ Breathing light stopped")

def start_breathing():
    global breathing_active,breathing_thread
    if breathing_active: return
    breathing_active=True
    breathing_thread=threading.Thread(target=breathing_loop,daemon=True)
    breathing_thread.start()

def stop_breathing():
    global breathing_active
    breathing_active=False
    turn_off_all_leds()

# 程序退出时关灯
atexit.register(turn_off_all_leds)
