import json
import socket
from flask_socketio import SocketIO, emit
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
import random
import threading
import time
import led_controller



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


# 房间结构示例：
# rooms = {
#     "room1": {
#         "host": "player1",
#         "players": {
#             "player1": {"ready": False, "score": 0},
#             "player2": {"ready": False, "score": 0}
#         },
#         "game_active": False,
#         "current_level": 1,
#         "target_sequence": [],
#         "answers_received": {},  # { player: [sequence] }
#         "all_answered": False
#     }
# }
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




# 树莓派处理模拟
def simulate_raspberry_processing_multi(room, level, sequence):
    # 播放序列
    led_controller.play_sequence(sequence, light_duration_per_color=level_duration_list[level-1][1], off_duration_between_colors=level_duration_list[level-1][2])

    # led_controller.play_sequence(sequence, light_duration_per_color=0.8, off_duration_between_colors=0.2)
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
    data = request.json
    mode = data.get('mode')  # 'single' or 'multi'
    username = session.get('username', 'tourist')

    if not username or mode not in ['single', 'multi']:
        return jsonify({'error': 'Invalid input'}), 400

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
    return render_template('single.html', player_name=username, game_mode='single')


@app.route('/multi')
def multi_player():
    username = session.get('username', 'tourist')
    return render_template('multi.html', player_name=username, game_mode='multi')
    # return f"欢迎 {username} 进入【多人模式】页面！"

@app.route('/')
def index():
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
waiting_for_start = False
waiting_thread = None
waiting_stop_event = None

# 修改run_invite_animation流程，集成等待start动画

def invite_and_wait_start():
    """
    先靠近检测，检测到人后进入动画循环，等待start或超时。
    """
    global waiting_for_start, waiting_thread, waiting_stop_event
    while True:
        led_controller.run_invite_animation()  # 靠近检测+一次动画
        # 进入等待start动画
        waiting_for_start = True
        waiting_stop_event = threading.Event()
        result = led_controller.wait_for_start_with_animation(timeout=120, stop_event=waiting_stop_event)
        waiting_for_start = False
        if result:
            print("用户点击start，进入游戏流程。")
            break  # 进入游戏
        else:
            print("超时未点击start，重新等待靠近检测。")
            continue  # 回到靠近检测

@app.route('/api/game/start', methods=['POST'])
def start_game():
    """开始新游戏（等待动画机制）"""
    global waiting_for_start, waiting_stop_event
    if not waiting_for_start:
        return jsonify({'status': 'not_ready', 'msg': '请先靠近感应区并等待动画'}), 400
    # 用户点击start，通知动画线程停止
    if waiting_stop_event:
        waiting_stop_event.set()
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
    # 先启动Flask服务，再后台线程运行等待动画机制
    threading.Thread(target=invite_and_wait_start, daemon=True).start()
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug = True, debug = True)
