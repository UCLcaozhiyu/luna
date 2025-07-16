import json
import socket
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import random
import threading
import time
import led_controller

# 添加HC-SR04传感器支持
try:
    import RPi.GPIO as GPIO
    from rpi_ws281x import PixelStrip, Color
    IS_RPI_ENV = True
    print("Raspberry Pi环境检测成功，启用HC-SR04传感器和LED动画")
except ImportError:
    IS_RPI_ENV = False
    print("非Raspberry Pi环境，传感器功能将被模拟")

# ========== HC-SR04 传感器设置 ==========
if IS_RPI_ENV:
    TRIG = 23
    ECHO = 24
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)

# ========== 邀请动画LED设置 ==========
if IS_RPI_ENV:
    INVITE_LED_COUNT = 120
    INVITE_LED_PIN = 18
    invite_strip = PixelStrip(INVITE_LED_COUNT, INVITE_LED_PIN, 800000, 10, False, 255, 0)
    invite_strip.begin()

# ========== 明亮柔和彩虹色列表 ==========
soft_colors = [
    Color(255, 128, 128),  # 柔红
    Color(255, 165, 100),  # 柔橙
    Color(255, 255, 128),  # 柔黄
    Color(144, 238, 144),  # 柔绿
    Color(128, 224, 224),  # 柔青
    Color(173, 216, 230),  # 柔蓝
    Color(216, 160, 240),  # 柔紫
] if IS_RPI_ENV else []

# ========== 邀请检测状态 ==========
invite_detection_active = False
game_started = False
invite_thread = None
FORCE_STOP_INVITE = False  # 🔧 新增：强制停止邀请检测的开关

# ========== 距离检测函数 ==========
def get_distance():
    """获取HC-SR04传感器检测的距离"""
    if not IS_RPI_ENV:
        # 模拟距离检测
        return random.uniform(50, 200)
    
    try:
        GPIO.output(TRIG, False)
        time.sleep(0.0002)
        GPIO.output(TRIG, True)
        time.sleep(0.00001)
        GPIO.output(TRIG, False)

        timeout = time.time() + 0.05
        pulse_start = None
        pulse_end = None
        
        # 等待ECHO引脚变为高电平
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            if pulse_start > timeout:
                return None

        # 等待ECHO引脚变为低电平
        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if pulse_end > timeout:
                return None

        # 确保两个时间戳都已获取
        if pulse_start is None or pulse_end is None:
            return None

        duration = pulse_end - pulse_start
        distance = duration * 34300 / 2
        return round(distance, 2)
        
    except Exception as e:
        print(f"距离检测错误: {e}")
        return None

# ========== LED 亮度调节 ==========
def apply_brightness(base_color, brightness_scale):
    """应用亮度调节到LED灯带"""
    if not IS_RPI_ENV:
        return
    
    r = ((base_color >> 16) & 0xFF) * brightness_scale // 255
    g = ((base_color >> 8) & 0xFF) * brightness_scale // 255
    b = (base_color & 0xFF) * brightness_scale // 255
    color = Color(r, g, b)
    for i in range(invite_strip.numPixels()):
        invite_strip.setPixelColor(i, color)
    invite_strip.show()

# ========== 呼吸灯动画 ==========
def soft_breathing_once(step_delay=0.008):
    """播放一次呼吸灯动画"""
    global FORCE_STOP_INVITE  # 🔧 新增
    
    if not IS_RPI_ENV:
        print("🌈 模拟LED: 播放呼吸灯动画")
        # 🔧 修改：模拟动画时也检查强制停止
        for i in range(10):
            if FORCE_STOP_INVITE:
                print("🛑 模拟动画被强制停止")
                return
            time.sleep(0.05)
        return
    
    color = random.choice(soft_colors)
    for b in range(0, 256, 8):  # 渐亮
        # 🔧 新增：检查强制停止
        if FORCE_STOP_INVITE:
            print("🛑 呼吸灯动画被强制停止")
            return
        apply_brightness(color, b)
        time.sleep(step_delay)
    
    time.sleep(0.1)
    
    for b in range(255, -1, -8):  # 渐灭
        # 🔧 新增：检查强制停止
        if FORCE_STOP_INVITE:
            print("🛑 呼吸灯动画被强制停止")
            return
        apply_brightness(color, b)
        time.sleep(step_delay)

# ========== 清空邀请动画灯带 ==========
def clear_invite_strip():
    """清空邀请动画的LED灯带"""
    if not IS_RPI_ENV:
        print("💡 模拟LED: 清空邀请动画灯带")
        return
    
    for i in range(invite_strip.numPixels()):
        invite_strip.setPixelColor(i, Color(0, 0, 0))
    invite_strip.show()

# ========== 邀请检测线程 ==========
def invite_detection_thread():
    """后台线程：检测人员靠近并播放邀请动画"""
    global invite_detection_active, game_started, FORCE_STOP_INVITE  # 🔧 新增
    
    print("🎯 邀请检测线程启动...")
    trigger_distance = 150
    animation_interval = 3
    last_play_time = 0
    detected = False

    # 🔧 修改：添加强制停止检查
    while invite_detection_active and not game_started and not FORCE_STOP_INVITE:
        try:
            # 🔧 新增：检查强制停止标志
            if FORCE_STOP_INVITE:
                print("🛑 收到强制停止信号，立即退出")
                break
                
            dist = get_distance()
            if IS_RPI_ENV:
                print(f"🔍 当前距离：{dist} cm")

            if dist and dist <= trigger_distance:
                if not detected:
                    print("✅ 检测到人员靠近，开始播放邀请动画")
                    # 🔧 新增：播放前再检查一次
                    if FORCE_STOP_INVITE:
                        break
                    soft_breathing_once()
                    last_play_time = time.time()
                    detected = True
                elif time.time() - last_play_time >= animation_interval:
                    print("🔁 持续检测到人员，循环播放邀请动画")
                    # 🔧 新增：播放前再检查一次
                    if FORCE_STOP_INVITE:
                        break
                    soft_breathing_once()
                    last_play_time = time.time()
            else:
                if detected:
                    print("👋 人员离开，停止邀请动画")
                    clear_invite_strip()
                    detected = False

            time.sleep(0.1)
        except Exception as e:
            print(f"邀请检测线程错误: {e}")
            time.sleep(1)
    
    print("🎮 邀请检测线程结束")
    clear_invite_strip()

# ========== 启动邀请检测 ==========
def start_invite_detection():
    """启动邀请检测后台线程"""
    global invite_detection_active, game_started, invite_thread, FORCE_STOP_INVITE  # 🔧 新增
    
    # 🔧 新增：重置强制停止标志
    FORCE_STOP_INVITE = False
    invite_detection_active = True
    game_started = False
    invite_thread = threading.Thread(target=invite_detection_thread, daemon=True)
    invite_thread.start()
    print("🚀 邀请检测已启动")

# ========== 停止邀请检测 ==========
def stop_invite_detection():
    """停止邀请检测"""
    global invite_detection_active, game_started, invite_thread, FORCE_STOP_INVITE  # 🔧 新增
    
    print("🛑 正在停止邀请检测...")
    
    # 🔧 修改：设置所有停止标志
    invite_detection_active = False
    game_started = True
    FORCE_STOP_INVITE = True  # 🔧 新增：强制停止！
    
    # 立即清空LED灯带，停止动画
    clear_invite_strip()
    
    # 等待线程结束（最多等待1秒）
    if invite_thread and invite_thread.is_alive():
        invite_thread.join(timeout=1.0)
        if invite_thread.is_alive():
            print("⚠️ 邀请检测线程未能在1秒内停止，但已设置停止标志")
        else:
            print("✅ 邀请检测线程已成功停止")
    
    print("⏹️ 邀请检测已停止")


app = Flask(__name__)
app.config['SECRET_KEY'] = 'simon_game_secret'

# 初始化 SocketIO
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# 难度等级配置
# level,light_duration_per_color,off_duration_between_colors
level_duration_list = [
    (1, 1, 0.5),
    (2, 1, 0.49),
    (3, 0.9, 0.48),
    (4, 0.9, 0.47),
    (5, 0.8, 0.46),
    (6, 0.8, 0.45),
    (7, 0.7, 0.44),
    (8, 0.7, 0.43),
    (9, 0.6, 0.42),
    (10, 0.6, 0.41),
    (11, 0.5, 0.40)
]

# ------------------ 多人模式 -------------------------
# 用户名存储
user_sessions = {}
# 房间状态管理
rooms = {}
# 全局变量
user_sids = {}  # { username: sid }

# 连接事件处理
@socketio.on('connect')
def handle_connect():
    print("socket[connect]without data, Client connected", request.sid)

@socketio.on('register_user')
def handle_register_user(data):
    print("socket[register_user]with data:", data)
    username = data.get('username')
    if username:
        user_sids[username] = request.sid
        print(f"SID 注册成功: {username} -> {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    print("socket[disconnect]without data,Client disconnected:", request.sid)
    # 查找该 sid 对应的用户名
    for username, sid in user_sids.items():
        if sid == request.sid:
            print(f"将要删除用户 {username}")
            for room in list(rooms.keys()):
                if username in rooms[room]['players']:
                    del rooms[room]['players'][username]
                    # 如果是房主，则更新房主或删除空房间
                    if rooms[room]['host'] == username:
                        remaining = list(rooms[room]['players'].keys())
                        if remaining:
                            rooms[room]['host'] = remaining[0]
                        else:
                            del rooms[room]
                            print(f"已删除空房间: {room}")
                            break
                socketio.emit('update_players', {
                    'players': rooms[room]['players'],
                    'host': rooms[room]['host']
                })

            print(f"User {username} 已从所有房间中移除")
            user_sids.pop(username, None)
            break

# 加入房间
@socketio.on('join_room')
def join_room(data):
    print("socket[join_room]with data:", data)
    username = data.get('username')
    room = data.get('room', 'default_room')

    print(f"{username} 加入 {room}")

    if room in rooms and rooms[room]['game_active']:
        # 游戏已经开始，不允许加入
        socketio.emit('join_denied', {
            'message': '游戏已经开始，无法加入'
        }, to=request.sid)
        return

    if room not in rooms:
        rooms[room] = {
            'host': username,
            'players': {},
            'game_active': False,
            'current_level': 1,
            'target_sequence': [],
            'answers_received': {},
            'all_answered': False
        }

    rooms[room]['players'][username] = {'ready': False, 'score': 0}

    # 更新房间信息
    socketio.emit('update_players', {
        'players': rooms[room]['players'],
        'host': rooms[room]['host']
    })

@socketio.on('set_ready')
def handle_set_ready(data):
    print("socket[set_ready]with data:", data)
    username = data['username']
    room = data['room']
    if room in rooms:
        room_data = rooms[room]
        if username in room_data['players']:
            room_data['players'][username]['ready'] = True

            socketio.emit('update_players', {
                'players': rooms[room]['players'],
                'host': rooms[room]['host']
            })

@socketio.on('start_game')
def handle_start_game(data):
    print("socket[start_game]with data:", data)
    # 延迟2s再开始
    time.sleep(1)
    room = data['room']
    if room in rooms:
        room_data = rooms[room]
        if room_data['host'] == data['username']:
            room_data['game_active'] = True
            room_data['current_level'] = 1
            room_data['target_sequence'] = game_state.generate_sequence(1)

            # 模拟树莓派处理线程
            threading.Thread(target=simulate_raspberry_processing_multi, args=(room,room_data['current_level'], room_data['target_sequence'],)).start()

            socketio.emit('game_started', {
                'level': room_data['current_level'],
                'sequence': room_data['target_sequence']
            })

def update_user_score(room, username, score_change):
    """
    更新指定用户的分数，并广播给房间所有人
    :param room: 房间名
    :param username: 用户名
    :param score_change: 要增加的分数
    """
    if room in rooms and username in rooms[room]['players']:
        rooms[room]['players'][username]['score'] += score_change
        socketio.emit('update_score', {
            'username': username,
            'score': rooms[room]['players'][username]['score']
        })

@socketio.on('submit_answer')
def handle_submit_answer(data):
    print("socket[submit_answer]with data:", data)
    username = data['username']
    room = data['room']
    answer = data['answer']

    if room in rooms:
        room_data = rooms[room]
        room_data['answers_received'][username] = answer

        # 判断是否全部回答完成
        if len(room_data['answers_received']) == len(room_data['players']):
            # 告诉其他用户开始查看led灯
            socketio.emit('write_messageBox', {
                'message': 'Observe the light!'
            })
            evaluate_all_answers(room)
        else:
            # 告诉用户还需要等待其他人
            socketio.emit('write_messageBox', {
                'message': 'Waiting for other players...'
            }, to=request.sid)

# 评估所有回答，更新分数，并进入下一轮
def evaluate_all_answers(room):
    room_data = rooms[room]
    correct_sequence = room_data['target_sequence']

    for user, ans in room_data['answers_received'].items():
        if ans == correct_sequence:
            room_data['players'][user]['score'] += 10 + (room_data['current_level'] * 10)
            update_user_score(room, user, room_data['players'][user]['score'])
        else:
            pass

    # 更新关卡和状态
    room_data['current_level'] += 1
    room_data['answers_received'] = {}

    if room_data['current_level'] > 5:
        # 游戏结束
        end_game(room)
    else:
        # 延迟2s
        time.sleep(1)
        # 进入下一关
        print("[evaluate_all_answers]进入第{0}关".format(room_data['current_level']))
        next_seq = game_state.generate_sequence(room_data['current_level'])
        room_data['target_sequence'] = next_seq
        threading.Thread(target=simulate_raspberry_processing_multi, args=(room,room_data['current_level'], next_seq,)).start()

# 游戏结束广播
def end_game(room):
    print("[end_game]游戏结束")
    room_data = rooms[room]
    socketio.emit('game_over', {
        'scores': {u: p['score'] for u, p in room_data['players'].items()}
    })

    # 删除房间
    if room in rooms:
        del rooms[room]
    
    # 重新启动邀请检测
    start_invite_detection()

# 树莓派处理模拟
def simulate_raspberry_processing_multi(room, level, sequence):
    # 播放序列
    led_controller.play_sequence(sequence, light_duration_per_color=level_duration_list[level-1][1], off_duration_between_colors=level_duration_list[level-1][2])

    print(f"树莓派序列处理完成: {sequence}")
    if room not in rooms:
        print("[simulate_raspberry_processing_multi]房间不存在")
        return
    room_data = rooms[room]

    # 通知前端：树莓派已完成序列显示，现在可以开始输入
    notify_frontend({
        'status': 'ready_for_input',
        'level': room_data['current_level'],
        'sequence': sequence
    })

# -------------------------- 主页 --------------------------
@app.route('/mode_selection')
def mode_selection():
    # 进入模式选择页面时重新启动邀请检测
    start_invite_detection()
    return render_template('mode_selection.html')

@app.route('/api/save_username', methods=['POST'])
def save_username():
    data = request.json
    username = data.get('username')

    if not username or len(username.strip()) == 0:
        return jsonify({'error': '用户名不能为空'}), 400

    session['username'] = username
    user_sessions[username] = {'score': 0, 'level': 1}

    return jsonify({
        'status': 'success',
        'username': username
    })

@app.route('/api/select_mode', methods=['POST'])
def select_mode():
    """选择游戏模式 - 立即停止邀请检测"""
    global FORCE_STOP_INVITE  # 🔧 新增
    
    data = request.json
    mode = data.get('mode')  # 'single' or 'multi'
    username = session.get('username', 'tourist')

    if not username or mode not in ['single', 'multi']:
        return jsonify({'error': 'Invalid input'}), 400

    # 🔧 新增：简单粗暴，立即强制停止！
    print(f"🎮 用户 {username} 选择了 {mode} 模式，强制停止邀请检测！")
    FORCE_STOP_INVITE = True
    stop_invite_detection()

    # 保存用户名和模式（可选）
    session['player_name'] = username
    session['game_mode'] = mode

    # 返回对应的页面路径
    return jsonify({
        'redirect': '/single' if mode == 'single' else '/multi',
        'username': username,
        'mode': mode
    })

@app.route('/single')
def single_player():
    username = session.get('username', 'tourist')
    # 进入单人游戏页面时停止邀请检测
    stop_invite_detection()
    return render_template('single.html', player_name=username, game_mode='single')

@app.route('/multi')
def multi_player():
    username = session.get('username', 'tourist')
    # 进入多人游戏页面时停止邀请检测
    stop_invite_detection()
    return render_template('multi.html', player_name=username, game_mode='multi')

@app.route('/')
def index():
    # 返回主页时重新启动邀请检测
    start_invite_detection()
    return render_template('mode_selection.html')

# ---------------------------- 单人模式 ---------------------------------

# 游戏状态管理
class GameState:
    def __init__(self):
        self.current_level = 1
        self.target_sequence = []
        self.player_sequence = []
        self.player_score = 0
        self.game_active = False

    def generate_sequence(self, level=None):
        """生成新的颜色序列"""
        level = level or self.current_level
        colors = ['red', 'blue', 'green', 'yellow']
        seq_length = min(2 + level, 10)  # 序列长度随关卡增加
        self.target_sequence = random.choices(colors, k=seq_length)
        print("生成新序列:", self.target_sequence)
        self.player_sequence = []
        return self.target_sequence

    def reset_game(self):
        """重置游戏状态"""
        self.current_level = 1
        self.player_score = 0   
        self.game_active = False
        self.target_sequence = []
        self.player_sequence = []

    def check_sequence(self, player_sequence):
        """验证玩家序列并更新分数"""
        print("对比玩家输入序列:", player_sequence)
        print("目标序列:", self.target_sequence)
        if player_sequence == self.target_sequence:
            # 计算分数：基础分 + 关卡加成
            self.player_score += 10 + (self.current_level * 10)
            self.current_level += 1
            return True
        self.game_active = False
        return False

# 全局游戏状态实例
game_state = GameState()

# API端点实现
@app.route('/api/game/start', methods=['POST'])
def start_game():
    """开始新游戏"""
    # 确保邀请检测已停止
    stop_invite_detection()
    
    game_state.reset_game()
    game_state.game_active = True
    sequence = game_state.generate_sequence()

    # 延迟2s
    time.sleep(1)

    # 模拟树莓派处理线程
    threading.Thread(target=simulate_raspberry_processing, args=(game_state.current_level, sequence,)).start()

    return jsonify({
        'status': 'started',
        'level': game_state.current_level,
        'sequence': sequence,
        'score': game_state.player_score
    })

@app.route('/api/game/check', methods=['POST'])
def check_sequence():
    """验证玩家输入的序列"""
    if not game_state.game_active:
        return jsonify({'error': 'Game not active'}), 400

    data = request.json
    player_sequence = data.get('playerSequence', [])

    if game_state.check_sequence(player_sequence):
        return jsonify({
            'result': 'correct',
            'score': game_state.player_score,
            'nextLevel': game_state.current_level
        })
    else:
        # 游戏结束，重新启动邀请检测
        start_invite_detection()
        return jsonify({
            'result': 'incorrect',
            'final_score': game_state.player_score,
            'max_level': game_state.current_level - 1
        })

@app.route('/api/game/sequence', methods=['GET'])
def get_sequence():
    """获取指定关卡的新序列"""
    # 延迟1s
    time.sleep(1)

    level = request.args.get('level', type=int, default=game_state.current_level)
    sequence = game_state.generate_sequence(level)

    # 模拟树莓派处理线程
    threading.Thread(target=simulate_raspberry_processing, args=(level, sequence,)).start()

    return jsonify({
        'sequence': sequence,
        'level': level
    })

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    """重置游戏状态"""
    game_state.reset_game()
    # 重新启动邀请检测
    start_invite_detection()
    return jsonify({'status': 'reset', 'score': 0, 'level': 1})

# 树莓派处理模拟
def simulate_raspberry_processing(level, sequence):

    # 播放序列
    led_controller.play_sequence(sequence, light_duration_per_color=level_duration_list[level-1][1], off_duration_between_colors=level_duration_list[level-1][2])
    print(f"树莓派序列处理完成: {sequence}")

    # 通知前端：树莓派已完成序列显示，现在可以开始输入
    notify_frontend({
        'status': 'ready_for_input',
        'level': game_state.current_level,
        'sequence': sequence
    })

def notify_frontend(message):
    """通过WebSocket向前端发送实时通知"""
    socketio.emit('game_update', message)
    print(f"已通过WebSocket发送通知到前端: {message}")

if __name__ == '__main__':
    # 启动邀请检测
    start_invite_detection()
    print("🎮 西蒙游戏服务器启动中...")
    print("📡 邀请检测已激活，等待玩家靠近...")
    
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug = True, debug = True)
