# 邀请检测功能集成说明

## 功能概述

本集成将 `soft_invite_detector_v2.py` 的HC-SR04传感器检测和呼吸灯动画功能无缝集成到 `app.py` 中，实现了以下功能：

1. **自动邀请检测**：Flask服务器启动后自动开始检测人员靠近
2. **智能动画播放**：检测到人员靠近时播放柔和的呼吸灯动画
3. **游戏状态管理**：游戏开始时自动停止邀请检测，游戏结束后自动恢复
4. **环境兼容性**：支持真实树莓派环境和开发环境模拟

## 硬件要求

### 必需硬件
- **HC-SR04超声波传感器**
  - TRIG引脚连接到GPIO 23
  - ECHO引脚连接到GPIO 24
  - VCC连接到5V
  - GND连接到地

- **WS2812B LED灯带**
  - 数据引脚连接到GPIO 18
  - 120个LED灯珠
  - 5V供电

### 连接示意图
```
HC-SR04:
TRIG -> GPIO 23
ECHO -> GPIO 24
VCC  -> 5V
GND  -> GND

WS2812B:
DIN  -> GPIO 18
VCC  -> 5V
GND  -> GND
```

## 软件依赖

### 必需Python包
```bash
pip install flask flask-socketio rpi_ws281x RPi.GPIO
```

### 可选依赖（开发环境）
```bash
pip install flask flask-socketio
```

## 使用方法

### 1. 启动服务器
```bash
cd dome_v6.2
python app.py
```

### 2. 功能流程
1. **服务器启动**：自动启动邀请检测线程
2. **等待玩家**：持续检测HC-SR04传感器
3. **人员靠近**：距离≤150cm时播放呼吸灯动画
4. **游戏开始**：玩家开始游戏时自动停止邀请检测
5. **游戏结束**：游戏结束后自动恢复邀请检测

### 3. 测试功能
```bash
python test_integration.py
```

## 配置参数

### 传感器配置
```python
TRIG = 23              # HC-SR04触发引脚
ECHO = 24              # HC-SR04回声引脚
trigger_distance = 150 # 触发距离（厘米）
```

### 动画配置
```python
animation_interval = 3  # 动画重复间隔（秒）
step_delay = 0.008     # 呼吸动画步进延迟
```

### LED配置
```python
INVITE_LED_COUNT = 120 # LED灯珠数量
INVITE_LED_PIN = 18    # LED数据引脚
```

## 环境检测

系统会自动检测运行环境：

- **树莓派环境**：启用真实传感器和LED控制
- **开发环境**：使用模拟功能，便于开发和测试

### 环境检测逻辑
```python
try:
    import RPi.GPIO as GPIO
    from rpi_ws281x import PixelStrip, Color
    IS_RPI_ENV = True
except ImportError:
    IS_RPI_ENV = False
```

## 动画效果

### 呼吸灯动画
- 使用7种柔和彩虹色
- 渐亮渐灭效果
- 随机颜色选择
- 平滑过渡

### 颜色列表
```python
soft_colors = [
    Color(255, 128, 128),  # 柔红
    Color(255, 165, 100),  # 柔橙
    Color(255, 255, 128),  # 柔黄
    Color(144, 238, 144),  # 柔绿
    Color(128, 224, 224),  # 柔青
    Color(173, 216, 230),  # 柔蓝
    Color(216, 160, 240),  # 柔紫
]
```

## 故障排除

### 常见问题

1. **传感器无响应**
   - 检查GPIO连接
   - 确认传感器供电正常
   - 检查TRIG/ECHO引脚配置

2. **LED不亮**
   - 检查数据线连接
   - 确认5V供电稳定
   - 检查LED数量配置

3. **权限错误**
   ```bash
   sudo python app.py
   ```

4. **模块导入错误**
   ```bash
   pip install --upgrade rpi_ws281x RPi.GPIO
   ```

### 调试模式
```python
# 在app.py中启用详细日志
print(f"🔍 当前距离：{dist} cm")
print("✅ 检测到人员靠近，开始播放邀请动画")
```

## 性能优化

### 线程管理
- 邀请检测运行在独立的后台线程
- 使用daemon线程确保程序退出时自动清理
- 游戏状态变化时自动启停检测线程

### 资源管理
- 自动清理GPIO资源
- LED灯带状态管理
- 内存使用优化

## 扩展功能

### 自定义动画
可以修改 `soft_breathing_once()` 函数来创建不同的动画效果：

```python
def custom_animation():
    # 自定义动画逻辑
    pass
```

### 多传感器支持
可以扩展支持多个HC-SR04传感器：

```python
sensors = [
    {'trig': 23, 'echo': 24},
    {'trig': 25, 'echo': 26}
]
```

### 配置热重载
可以添加配置文件支持，无需重启即可修改参数。

## 许可证

本项目遵循原有项目的许可证条款。 