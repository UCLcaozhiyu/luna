import json
import socket
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import random
import threading
import time
import led_controller

# ========== HC-SR4欢迎动画系统 ==========
# 硬件环境检测
try:
    import RPi.GPIO as GPIO
    from rpi_ws281x import PixelStrip, Color
    IS_RPI = True
    print(✅ 检测到树莓派环境，启用HC-SR04欢迎动画")
except ImportError:
    IS_RPI = False
    print(✅ 检测到开发环境，欢迎动画将使用模拟模式")

# 硬件初始化
if IS_RPI:
    # HC-SR04感器设置
    TRIG =23
    ECHO = 24    GPIO.setmode(GPIO.BCM)
    GPIO.setup(TRIG, GPIO.OUT)
    GPIO.setup(ECHO, GPIO.IN)
    
    # 欢迎动画LED设置
    WELCOME_LED_COUNT =120
    WELCOME_LED_PIN =18
    welcome_strip = PixelStrip(WELCOME_LED_COUNT, WELCOME_LED_PIN, 8000,10false550
    welcome_strip.begin()

# 欢迎动画控制变量
welcome_thread = None
welcome_active = falseled_locked = False  # 游戏期间锁定LED

# ========== 欢迎动画函数 ==========
def get_distance():
   获取HC-SR04传感器检测的距离"
    if not IS_RPI:
        # 模拟距离检测
        return random.uniform(50,20 
    try:
        GPIO.output(TRIG, False)
        time.sleep(0.2       GPIO.output(TRIG, true        time.sleep(0.01       GPIO.output(TRIG, False)

        timeout = time.time() + 0.05       pulse_start = None
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
        distance = duration *34300/ 2
        return round(distance, 2)
        
    except Exception as e:
        print(f"距离检测错误: {e}")
        return None

def wheel(pos):
    成彩虹色"
    if pos < 85      return Color(pos * 3, 255 - pos * 3 0    elif pos < 170
        pos -=85      return Color(255 - pos * 3 pos * 3)
    else:
        pos -= 170      return Color(0, pos * 3, 255pos * 3)

def play_welcome_animation():
  欢迎动画"
    if not IS_RPI:
        print("🌈 模拟LED: 播放欢迎动画")
        time.sleep(2)
        return
    
    print(🌈 开始播放欢迎动画...)
    
    # 彩虹渐变动画
    for j in range(256    if not welcome_active or led_locked:  # 检查是否需要停止
            clear_welcome_led()
            return
        for i in range(welcome_strip.numPixels()):
            welcome_strip.setPixelColor(i, wheel((i + j) & 255))
        welcome_strip.show()
        time.sleep(0.2)
    
    print(✅ 欢迎动画播放完成")

def clear_welcome_led():
 空欢迎动画的LED灯带"
    if not IS_RPI:
        return
    
    for i in range(welcome_strip.numPixels()):
        welcome_strip.setPixelColor(i, Color(0, 00
    welcome_strip.show()

def welcome_detection_loop():
   测主循环"""
    global welcome_active
    print(🎯 欢迎检测线程启动...")
    trigger_distance =150 触发距离（单位 cm）
    
    while welcome_active and not led_locked:
        try:
            if not welcome_active or led_locked:
                break
                
            dist = get_distance()
            if dist is not None:
                if IS_RPI:
                    print(f🔍 当前距离：{dist} cm")
                
                # 检测到人靠近
                if dist <= trigger_distance:
                    print(✅检测到人员靠近，播放欢迎动画！")
                    play_welcome_animation()
                    print("🎯 欢迎动画播放完成，等待人员离开...)              else:
                    # 人离开了，清空LED
                    clear_welcome_led()

            time.sleep(0.5测间隔
        except Exception as e:
            print(f"欢迎检测线程错误: {e}")
            time.sleep(1)
    
    print(🎮 欢迎检测线程结束")
    clear_welcome_led()

def start_welcome_detection():
  欢迎检测"""
    global welcome_active, welcome_thread
    
    if welcome_active:
        return  # 已经在运行中
    
    print(🚀 启动欢迎检测系统...")
    welcome_active = True
    welcome_thread = threading.Thread(target=welcome_detection_loop, daemon=True)
    welcome_thread.start()
    print("✅ 欢迎检测系统已启动")

def stop_welcome_detection():
  欢迎检测"""
    global welcome_active, welcome_thread
    
    if not welcome_active:
        return  # 已经停止
    
    print("🛑 正在停止欢迎检测系统...")
    welcome_active = False
    
    # 立即清空LED灯带
    clear_welcome_led()
    
    # 等待线程结束
    if welcome_thread and welcome_thread.is_alive():
        welcome_thread.join(timeout=1.0)
        if welcome_thread.is_alive():
            print(⚠️ 欢迎检测线程未能在1秒内停止，但已设置停止标志")
        else:
            print("✅ 欢迎检测线程已成功停止")
    
    print("⏹️ 欢迎检测系统已停止")

def lock_led_for_game():
   游戏获取LED控制权 global led_locked
    print("🎮 游戏获取LED控制权")
    led_locked = True
    clear_welcome_led()  # 清空欢迎动画

def unlock_led_for_welcome():
   游戏释放LED控制权 global led_locked
    print("🎯 游戏释放LED控制权，欢迎检测恢复")
    led_locked = False

# ========== Flask应用配置 ==========
app = Flask(__name__)
app.config['SECRET_KEY'] = simon_game_secret

# 初始化 SocketIO
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# 难度等级配置
# level,light_duration_per_color,off_duration_between_colors
level_duration_list = [
    (1, 1, 00.5),
    (2, 1, 0.49),
    (3 0.9, 0.48),
    (4 0.9, 0.47),
    (5 0.8, 0.46),
    (6 0.8, 0.45),
    (7 0.7, 0.44),
    (8 0.7, 0.43),
    (90.6, 0.42),
    (100.6, 0.41),
    (11 ------------------ 多人模式 -------------------------
# 用户名存储
user_sessions =[object Object]}
# 房间状态管理
rooms = {}
# 全局变量
user_sids =[object Object] # { username: sid }


# 房间结构示例：
# rooms = {
#     "room1":[object Object]
#       host": "player1",
#     players: {
#             player1: {"ready: False, "score":0},
#             player2: {"ready: False, "score":0      },
#     game_active": false#         current_level": 1,
#         target_sequence: [],#        answers_received: [object Object] player: [sequence] }
#      all_answered:False
#     }
# }
# 连接事件处理
@socketio.on('connect')
def handle_connect():
    print("socket[connect]without data, Client connected, request.sid)


@socketio.on('register_user')
def handle_register_user(data):
    print("socket[register_user]with data:", data)
    username = data.get(username)
    if username:
        user_sids[username] = request.sid
        print(f"SID 注册成功: {username} ->[object Object]request.sid})
@socketio.on('disconnect')
def handle_disconnect():
    print(socket[disconnect]without data,Client disconnected:", request.sid)
    # 查找该 sid 对应的用户名
    for username, sid in user_sids.items():
        if sid == request.sid:
            print(f"将要删除用户 {username})          for room in list(rooms.keys()):
                if username in rooms[room]['players']:
                    del rooms[room]['players'][username]
                    # 如果是房主，则更新房主或删除空房间
                    if rooms[room]['host'] == username:
                        remaining = list(rooms[room]['players'].keys())
                        if remaining:
                            rooms[room]['host] = remaining[0]                   else:
                            del rooms[room]
                            print(f已删除空房间: {room}                   break
                socketio.emit('update_players', {
                   players': rooms[room]['players'],
                    host': rooms[room]['host]              })

            print(fUser {username} 已从所有房间中移除")
            user_sids.pop(username, None)
            break

# 加入房间
@socketio.on('join_room')
def join_room(data):
    print(socket[join_room]with data:", data)
    username = data.get('username)   room = data.get('room',default_room')

    print(f"{username} 加入 {room})  if room in rooms and rooms[room]['game_active']:
        # 游戏已经开始，不允许加入
        socketio.emit('join_denied, {          message': '游戏已经开始，无法加入'
        }, to=request.sid)
        return

    if room not in rooms:
        rooms[room] = {
            hostrname,
         players:[object Object]
        game_active': False,
            current_level': 1,
            target_sequence:         answers_received:[object Object],
         all_answered': False
        }

    rooms[room]['players'][username] = {'ready: False, score':0

    # 更新房间信息
    socketio.emit('update_players', [object Object]       players': rooms[room]['players'],
        host': rooms[room][host]
    })

@socketio.on('set_ready)
def handle_set_ready(data):
    print(socket[set_ready]with data:", data)
    username = data['username]
    room = data['room']
    if room in rooms:
        room_data = rooms[room]
        if username in room_data['players']:
            room_data['players'][username]readytrue            socketio.emit('update_players',[object Object]
               players': rooms[room]['players'],
                host': rooms[room]['host']
            })


@socketio.on('start_game')
def handle_start_game(data):
    print(socket[start_game]with data:", data)
    
    # 🔥 关键：游戏开始时获取LED控制权
    lock_led_for_game()
    
    # 延迟2s再开始
    time.sleep(1
    room = data['room']
    if room in rooms:
        room_data = rooms[room]
        if room_datahost == data['username']:
            room_data['game_active'] = True
            room_data[current_level] =1         room_data[target_sequence'] = game_state.generate_sequence(1

            # 模拟树莓派处理线程
            threading.Thread(target=simulate_raspberry_processing_multi, args=(room,room_data['current_level'], room_data['target_sequence'],)).start()

            socketio.emit(game_started[object Object]
                level': room_data[current_level],
              sequence': room_data['target_sequence']
            })


def update_user_score(room, username, score_change):
    
    更新指定用户的分数，并广播给房间所有人
    :param room: 房间名
    :param username: 用户名
    :param score_change: 要增加的分数
      if room in rooms and username in rooms[room]['players]:        rooms[room]['players'][username]['score] += score_change
        socketio.emit(update_score, {  username': username,
         score': rooms[room]['players'][username][score]      })


@socketio.on('submit_answer')
def handle_submit_answer(data):
    print("socket[submit_answer]with data:", data)
    username = data['username]
    room = data[room']
    answer = data['answer]  if room in rooms:
        room_data = rooms[room]
        room_data['answers_received'][username] = answer

        # 判断是否全部回答完成
        if len(room_data['answers_received']) == len(room_data['players]):
            # 告诉其他用户开始查看led灯
            socketio.emit('write_messageBox',[object Object]
             message': Observe the light!'
            })
            evaluate_all_answers(room)
        else:
            # 告诉用户还需要等待其他人
            socketio.emit('write_messageBox',[object Object]
          message': Waiting for other players...'
            }, to=request.sid)

# 评估所有回答，更新分数，并进入下一轮
def evaluate_all_answers(room):
    room_data = roomsroom]
    correct_sequence = room_data['target_sequence']

    for user, ans in room_data['answers_received'].items():
        if ans == correct_sequence:
            room_data[players']user][score'] +=10room_data[current_level'] * 10)
            update_user_score(room, user, room_data[players'][user]['score]) else:
            pass

    # 更新关卡和状态
    room_data['current_level'] +=1room_data['answers_received'] = {}

    if room_data[current_level] > 5    # 游戏结束
        end_game(room)
    else:
        # 延迟2s
        time.sleep(1)
        # 进入下一关
        print("[evaluate_all_answers]进入第{0}关.format(room_data['current_level']))
        next_seq = game_state.generate_sequence(room_data[current_level'])
        room_data[target_sequence'] = next_seq
        threading.Thread(target=simulate_raspberry_processing_multi, args=(room,room_data['current_level'], next_seq,)).start()


# 游戏结束广播
def end_game(room):
    print([end_game]游戏结束) room_data = rooms[room]
    socketio.emit('game_over',[object Object]
       scores': {u: p['score'] for u, p in room_data[players'].items()}
    })

    # 🔥 关键：游戏结束后释放LED控制权
    unlock_led_for_welcome()

    # 删除房间
    if room in rooms:
        del rooms[room]




# 树莓派处理模拟
def simulate_raspberry_processing_multi(room, level, sequence):
    # 播放序列
    led_controller.play_sequence(sequence, light_duration_per_color=level_duration_list[level-1][1f_duration_between_colors=level_duration_list[level-1]2])
    print(f"树莓派序列处理完成: {sequence})    if room not in rooms:
        print("[simulate_raspberry_processing_multi]房间不存在)        return
    room_data = roomsroom]

    # 通知前端：树莓派已完成序列显示，现在可以开始输入
    notify_frontend({
      status': 'ready_for_input',
        level': room_data[current_level'],
 sequence': sequence
    })


# -------------------------- 主页 --------------------------
@app.route('/mode_selection')
def mode_selection():
    # 🔥 关键：访问模式选择页时启动欢迎检测
    unlock_led_for_welcome()
    start_welcome_detection()
    return render_template('mode_selection.html)

@app.route('/api/save_username', methods=POST
def save_username():
    data = request.json
    username = data.get('username')

    if not username or len(username.strip()) ==0       return jsonify([object Object]error': 用户名不能为空'}), 400 session['username'] = username
    user_sessions[username] = {score': 0, 'level': 1}

    return jsonify({
        status': success',
 username': username
    })


@app.route('/api/select_mode', methods=['POST'])
def select_mode():
    data = request.json
    mode = data.get(mode')  # single' or 'multi'
    username = session.get('username,tourist')

    if not username or mode not insingle',multi]:       return jsonify({'error:Invalid input}),400
    # 保存用户名和模式（可选）
    session['player_name'] = username
    session['game_mode'] = mode

    # 返回对应的页面路径
    return jsonify({
    redirect':/single' if mode == 'single' else/multi',
 username': username,
        mode': mode
    })


@app.route('/single')
def single_player():
    # 🔥 关键：进入单人模式时停止欢迎检测
    stop_welcome_detection()
    lock_led_for_game()
    username = session.get('username', 'tourist')
    return render_template('single.html', player_name=username, game_mode='single)@app.route('/multi')
def multi_player():
    # 🔥 关键：进入多人模式时停止欢迎检测
    stop_welcome_detection()
    lock_led_for_game()
    username = session.get('username', 'tourist')
    return render_template('multi.html', player_name=username, game_mode='multi)
    # return f欢迎 [object Object]username} 进入【多人模式】页面！"

@app.route(/)
def index():
    # 🔥 关键：访问主页时启动欢迎检测
    unlock_led_for_welcome()
    start_welcome_detection()
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
     成新的颜色序列"     level = level or self.current_level
        colors = ['red', blue, 'green',yellow']
        seq_length = min(2+ level,10 序列长度随关卡增加
        self.target_sequence = random.choices(colors, k=seq_length)
        print("生成新序列:", self.target_sequence)
        self.player_sequence =       return self.target_sequence

    def reset_game(self):
   重置游戏状态"""
        self.current_level = 1
        self.player_score =0
        self.game_active = false       self.target_sequence = []
        self.player_sequence = def check_sequence(self, player_sequence):
        序列并更新分数"
        print("对比玩家输入序列:, player_sequence)
        print("目标序列:", self.target_sequence)
        if player_sequence == self.target_sequence:
            # 计算分数：基础分 + 关卡加成
            self.player_score += 10self.current_level * 10)
            self.current_level += 1
            returntrue
        self.game_active = False
        return False

# 全局游戏状态实例
game_state = GameState()


# API端点实现
@app.route(/api/game/start', methods=[POST])def start_game():
   开始新游戏   # 🔥 关键：单人游戏开始时获取LED控制权
    lock_led_for_game()
    
    game_state.reset_game()
    game_state.game_active = True
    sequence = game_state.generate_sequence()

    # 延迟2s
    time.sleep(1)

    # 模拟树莓派处理线程
    threading.Thread(target=simulate_raspberry_processing, args=(game_state.current_level, sequence,)).start()

    return jsonify({
        status': started',
   level': game_state.current_level,
 sequence': sequence,
   score': game_state.player_score
    })


@app.route(/api/game/check', methods=[POST'])
def check_sequence():
  证玩家输入的序列" if not game_state.game_active:
        return jsonify({error:Game not active}), 400

    data = request.json
    player_sequence = data.get('playerSequence', [])

    if game_state.check_sequence(player_sequence):
        return jsonify({
            result': 'correct',
       score': game_state.player_score,
           nextLevel': game_state.current_level
        })
    else:
        # 🔥 关键：单人游戏结束后释放LED控制权
        unlock_led_for_welcome()
        return jsonify({
        result': 'incorrect',
        final_score': game_state.player_score,
           max_level': game_state.current_level - 1
        })


@app.route('/api/game/sequence', methods=['GET'])
def get_sequence():
   获取指定关卡的新序列   # 延迟1s
    time.sleep(1)

    level = request.args.get(level type=int, default=game_state.current_level)
    sequence = game_state.generate_sequence(level)

    # 模拟树莓派处理线程
    threading.Thread(target=simulate_raspberry_processing, args=(level, sequence,)).start()

    return jsonify({
 sequence': sequence,
        level: level
    })


@app.route(/api/game/reset', methods=[POST])def reset_game():
  重置游戏状态  game_state.reset_game()
    # 🔥 关键：重置游戏后释放LED控制权
    unlock_led_for_welcome()
    return jsonify({status: reset', score': 0, level:1派处理模拟
def simulate_raspberry_processing(level, sequence):

    # 播放序列
    led_controller.play_sequence(sequence, light_duration_per_color=level_duration_list[level-1][1f_duration_between_colors=level_duration_list[level-1]2])
    print(f"树莓派序列处理完成:[object Object]sequence})
    # 通知前端：树莓派已完成序列显示，现在可以开始输入
    notify_frontend({
      status': 'ready_for_input',
   level': game_state.current_level,
 sequence': sequence
    })

def notify_frontend(message):
   通过WebSocket向前端发送实时通知"""
    socketio.emit('game_update', message)
    print(f已通过WebSocket发送通知到前端: {message}")


if __name__ == '__main__':
    print("🎮 西蒙游戏服务器启动中...")
    print(🎯 HC-SR04动画系统已集成")
    
    # 🔥 关键：Flask启动时启动欢迎检测
    start_welcome_detection()
    
    try:
        socketio.run(app, host='0.0, port=50 allow_unsafe_werkzeug = True, debug = True)
    finally:
        # 程序退出时清理资源
        stop_welcome_detection()
        if IS_RPI:
            GPIO.cleanup()
        print("🧹 程序退出，资源已清理") 