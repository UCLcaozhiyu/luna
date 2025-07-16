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

# ========== 强化的邀请检测状态管理类 ==========
class InviteDetectionManager:
    def __init__(self):
        self.active = False
        self.game_started = False
        self.threads = set()  # 存储所有活跃线程
        self.lock = threading.RLock()  # 可重入锁
        self.stop_event = threading.Event()  # 线程停止事件
        
    def start_detection(self):
        """启动邀请检测"""
        with self.lock:
            print("🔄 请求启动邀请检测...")
            
            # 首先停止所有现有线程
            self._stop_all_threads()
            
            # 重置状态
            self.active = True
            self.game_started = False
            self.stop_event.clear()
            
            # 创建新线程
            thread = threading.Thread(target=self._detection_thread, daemon=True)
            thread.start()
            self.threads.add(thread)
            
            print(f"🚀 邀请检测已启动，当前活跃线程数: {len(self.threads)}")
    
    def stop_detection(self):
        """停止邀请检测"""
        with self.lock:
            print("🛑 请求停止邀请检测...")
            
            # 设置停止标志
            self.active = False
            self.game_started = True
            self.stop_event.set()
            
            # 立即清空LED
            clear_invite_strip()
            
            # 停止所有线程
            self._stop_all_threads()
            
            print(f"⏹️ 邀请检测已停止，剩余线程数: {len(self.threads)}")
    
    def _stop_all_threads(self):
        """内部函数：停止所有线程"""
        # 设置停止信号
        self.stop_event.set()
        
        # 等待所有线程结束
        for thread in list(self.threads):
            if thread.is_alive():
                thread.join(timeout=0.5)  # 等待0.5秒
            self.threads.discard(thread)
        
        print(f"🧹 清理完成，线程数: {len(self.threads)}")
    
    def _detection_thread(self):
        """检测线程主函数"""
        thread_id = threading.current_thread().ident
        print(f"🎯 邀请检测线程启动 (ID: {thread_id})")
        
        trigger_distance = 150
        animation_interval = 3
        last_play_time = 0
        detected = False
        
        try:
            while self.active and not self.game_started and not self.stop_event.is_set():
                # 检查停止条件
                if self.stop_event.wait(0.1):  # 等待0.1秒或直到stop_event被设置
                    break
                
                try:
                    dist = get_distance()
                    if IS_RPI_ENV:
                        print(f"🔍 距离: {dist}cm (线程{thread_id})")
                    
                    if dist and dist <= trigger_distance:
                        if not detected:
                            print(f"✅ 检测到人员靠近 (线程{thread_id})")
                            if self._safe_play_animation():
                                last_play_time = time.time()
                                detected = True
                        elif time.time() - last_play_time >= animation_interval:
                            print(f"🔁 循环播放动画 (线程{thread_id})")
                            if self._safe_play_animation():
                                last_play_time = time.time()
                    else:
                        if detected:
                            print(f"👋 人员离开 (线程{thread_id})")
                            clear_invite_strip()
                            detected = False
                            
                except Exception as e:
                    print(f"检测错误 (线程{thread_id}): {e}")
                    time.sleep(1)
                    
        except Exception as e:
            print(f"线程异常 (线程{thread_id}): {e}")
        finally:
            clear_invite_strip()
            with self.lock:
                current_thread = threading.current_thread()
                self.threads.discard(current_thread)
            print(f"🎮 邀请检测线程结束 (ID: {thread_id})")
    
    def _safe_play_animation(self):
        """安全播放动画"""
        if self.stop_event.is_set() or not self.active or self.game_started:
            return False
        
        if not IS_RPI_ENV:
            # 模拟动画，支持中断
            for i in range(10):
                if self.stop_event.wait(0.05):  # 等待0.05秒或停止事件
                    print("🛑 模拟动画被中断")
                    return False
            print("🌈 模拟动画播放完成")
        else:
            # 真实动画
            soft_breathing_once_safe(self.stop_event)
        
        return True

# 全局管理器实例
invite_manager = InviteDetectionManager()

# ========== 距离检测函数 ==========
def get_distance():
    """获取HC-SR04传感器检测的距离"""
    if not IS_RPI_ENV:
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
        
        while GPIO.input(ECHO) == 0:
            pulse_start = time.time()
            if pulse_start > timeout:
                return None

        while GPIO.input(ECHO) == 1:
            pulse_end = time.time()
            if pulse_end > timeout:
                return None

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

# ========== 安全的呼吸灯动画 ==========
def soft_breathing_once_safe(stop_event, step_delay=0.008):
    """播放一次呼吸灯动画（可安全中断）"""
    if not IS_RPI_ENV:
        return
    
    color = random.choice(soft_colors)
    
    # 渐亮
    for b in range(0, 256, 8):
        if stop_event.is_set():
            print("🛑 呼吸灯动画被中断（渐亮阶段）")
            return
        apply_brightness(color, b)
        time.sleep(step_delay)
    
    if stop_event.wait(0.1):  # 中间暂停也检查停止事件
        print("🛑 呼吸灯动画被中断（中间暂停）")
        return
    
    # 渐灭
    for b in range(255, -1, -8):
        if stop_event.is_set():
            print("🛑 呼吸灯动画被中断（渐灭阶段）")
            return
        apply_brightness(color, b)
        time.sleep(step_delay)

# ========== 清空邀请动画灯带 ==========
def clear_invite_strip():
    """清空邀请动画的LED灯带"""
    if not IS_RPI_ENV:
        # 减少模拟环境的日志输出
        return
    
    for i in range(invite_strip.numPixels()):
        invite_strip.setPixelColor(i, Color(0, 0, 0))
    invite_strip.show()

# ========== 兼容性函数 ==========
def start_invite_detection():
    """启动邀请检测（兼容性函数）"""
    invite_manager.start_detection()

def stop_invite_detection():
    """停止邀请检测（兼容性函数）"""
    invite_manager.stop_detection()


app = Flask(__name__)
app.config['SECRET_KEY'] = 'simon_game_secret'

# 初始化 SocketIO
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# 难度等级配置
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
user_sessions = {}
rooms = {}
user_sids = {}  # { username: sid }

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
    for username, sid in user_sids.items():
        if sid == request.sid:
            print(f"将要删除用户 {username}")
            for room in list(rooms.keys()):
                if username in rooms[room]['players']:
                    del rooms[room]['players'][username]
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

@socketio.on('join_room')
def join_room(data):
    print("socket[join_room]with data:", data)
    username = data.get('username')
    room = data.get('room', 'default_room')

    print(f"{username} 加入 {room}")

    if room in rooms and rooms[room]['game_active']:
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
    time.sleep(1)
    room = data['room']
    if room in rooms:
        room_data = rooms[room]
        if room_data['host'] == data['username']:
            room_data['game_active'] = True
            room_data['current_level'] = 1
            room_data['target_sequence'] = game_state.generate_sequence(1)

            threading.Thread(target=simulate_raspberry_processing_multi, args=(room,room_data['current_level'], room_data['target_sequence'],)).start()

            socketio.emit('game_started', {
                'level': room_data['current_level'],
                'sequence': room_data['target_sequence']
            })

def update_user_score(room, username, score_change):
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

        if len(room_data['answers_received']) == len(room_data['players']):
            socketio.emit('write_messageBox', {
                'message': 'Observe the light!'
            })
            evaluate_all_answers(room)
        else:
            socketio.emit('write_messageBox', {
                'message': 'Waiting for other players...'
            }, to=request.sid)

def evaluate_all_answers(room):
    room_data = rooms[room]
    correct_sequence = room_data['target_sequence']

    for user, ans in room_data['answers_received'].items():
        if ans == correct_sequence:
            room_data['players'][user]['score'] += 10 + (room_data['current_level'] * 10)
            update_user_score(room, user, room_data['players'][user]['score'])

    room_data['current_level'] += 1
    room_data['answers_received'] = {}

    if room_data['current_level'] > 5:
        end_game(room)
    else:
        time.sleep(1)
        print("[evaluate_all_answers]进入第{0}关".format(room_data['current_level']))
        next_seq = game_state.generate_sequence(room_data['current_level'])
        room_data['target_sequence'] = next_seq
        threading.Thread(target=simulate_raspberry_processing_multi, args=(room,room_data['current_level'], next_seq,)).start()

def end_game(room):
    print("[end_game]游戏结束")
    room_data = rooms[room]
    socketio.emit('game_over', {
        'scores': {u: p['score'] for u, p in room_data['players'].items()}
    })

    if room in rooms:
        del rooms[room]
    
    start_invite_detection()

def simulate_raspberry_processing_multi(room, level, sequence):
    led_controller.play_sequence(sequence, light_duration_per_color=level_duration_list[level-1][1], off_duration_between_colors=level_duration_list[level-1][2])
    print(f"树莓派序列处理完成: {sequence}")
    if room not in rooms:
        print("[simulate_raspberry_processing_multi]房间不存在")
        return
    room_data = rooms[room]

    notify_frontend({
        'status': 'ready_for_input',
        'level': room_data['current_level'],
        'sequence': sequence
    })

# -------------------------- 主页 --------------------------
@app.route('/mode_selection')
def mode_selection():
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
    data = request.json
    mode = data.get('mode')
    username = session.get('username', 'tourist')

    if not username or mode not in ['single', 'multi']:
        return jsonify({'error': 'Invalid input'}), 400

    # 🔧 强制停止邀请检测
    print(f"🎮 用户 {username} 选择了 {mode} 模式，强制停止邀请检测")
    stop_invite_detection()
    
    # 额外确保停止
    time.sleep(0.2)  # 给停止操作一些时间

    session['player_name'] = username
    session['game_mode'] = mode

    return jsonify({
        'redirect': '/single' if mode == 'single' else '/multi',
        'username': username,
        'mode': mode
    })

@app.route('/single')
def single_player():
    username = session.get('username', 'tourist')
    # 双重保险，确保停止
    stop_invite_detection()
    print(f"📄 单人游戏页面加载，用户: {username}")
    return render_template('single.html', player_name=username, game_mode='single')

@app.route('/multi')
def multi_player():
    username = session.get('username', 'tourist')
    # 双重保险，确保停止
    stop_invite_detection()
    print(f"📄 多人游戏页面加载，用户: {username}")
    return render_template('multi.html', player_name=username, game_mode='multi')

@app.route('/')
def index():
    start_invite_detection()
    return render_template('mode_selection.html')

# ---------------------------- 单人模式 ---------------------------------
class GameState:
    def __init__(self):
        self.current_level = 1
        self.target_sequence = []
        self.player_sequence = []
        self.player_score = 0
        self.game_active = False

    def generate_sequence(self, level=None):
        level = level or self.current_level
        colors = ['red', 'blue', 'green', 'yellow']
        seq_length = min(2 + level, 10)
        self.target_sequence = random.choices(colors, k=seq_length)
        print("生成新序列:", self.target_sequence)
        self.player_sequence = []
        return self.target_sequence

    def reset_game(self):
        self.current_level = 1
        self.player_score = 0   
        self.game_active = False
        self.target_sequence = []
        self.player_sequence = []

    def check_sequence(self, player_sequence):
        print("对比玩家输入序列:", player_sequence)
        print("目标序列:", self.target_sequence)
        if player_sequence == self.target_sequence:
            self.player_score += 10 + (self.current_level * 10)
            self.current_level += 1
            return True
        self.game_active = False
        return False

game_state = GameState()

@app.route('/api/game/start', methods=['POST'])
def start_game():
    """开始新游戏"""
    stop_invite_detection()
    print("🎮 单人游戏开始，邀请检测已停止")
    
    game_state.reset_game()
    game_state.game_active = True
    sequence = game_state.generate_sequence()

    time.sleep(1)
    threading.Thread(target=simulate_raspberry_processing, args=(game_state.current_level, sequence,)).start()

    return jsonify({
        'status': 'started',
        'level': game_state.current_level,
        'sequence': sequence,
        'score': game_state.player_score
    })

@app.route('/api/game/check', methods=['POST'])
def check_sequence():
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
        start_invite_detection()
        return jsonify({
            'result': 'incorrect',
            'final_score': game_state.player_score,
            'max_level': game_state.current_level - 1
        })

@app.route('/api/game/sequence', methods=['GET'])
def get_sequence():
    time.sleep(1)
    level = request.args.get('level', type=int, default=game_state.current_level)
    sequence = game_state.generate_sequence(level)
    threading.Thread(target=simulate_raspberry_processing, args=(level, sequence,)).start()

    return jsonify({
        'sequence': sequence,
        'level': level
    })

@app.route('/api/game/reset', methods=['POST'])
def reset_game():
    game_state.reset_game()
    start_invite_detection()
    return jsonify({'status': 'reset', 'score': 0, 'level': 1})

def simulate_raspberry_processing(level, sequence):
    led_controller.play_sequence(sequence, light_duration_per_color=level_duration_list[level-1][1], off_duration_between_colors=level_duration_list[level-1][2])
    print(f"树莓派序列处理完成: {sequence}")

    notify_frontend({
        'status': 'ready_for_input',
        'level': game_state.current_level,
        'sequence': sequence
    })

def notify_frontend(message):
    socketio.emit('game_update', message)
    print(f"已通过WebSocket发送通知到前端: {message}")

if __name__ == '__main__':
    # 启动邀请检测
    start_invite_detection()
    print("🎮 西蒙游戏服务器启动中...")
    print("📡 邀请检测已激活，等待玩家靠近...")
    
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug = True, debug = True)
