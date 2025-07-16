
from flask import Flask,render_template,session
from flask_socketio import SocketIO
import led_controller

app=Flask(__name__)
app.config['SECRET_KEY']='dome_secret'
socketio=SocketIO(app,async_mode='threading',cors_allowed_origins="*")

ACTIVE_COUNT=0  # 当前在游戏中的玩家数量

def increment_active():
    global ACTIVE_COUNT
    ACTIVE_COUNT+=1
    if ACTIVE_COUNT>0:
        led_controller.stop_breathing()
    print(f"ACTIVE_COUNT={ACTIVE_COUNT}")

def decrement_active():
    global ACTIVE_COUNT
    ACTIVE_COUNT=max(0,ACTIVE_COUNT-1)
    print(f"ACTIVE_COUNT={ACTIVE_COUNT}")
    if ACTIVE_COUNT==0:
        led_controller.start_breathing()

@app.route('/')
def home():
    decrement_active()  # 回首页视为退出
    return render_template('mode_selection.html')

@app.route('/mode_selection')
def mode_selection():
    decrement_active()
    return render_template('mode_selection.html')

@app.route('/single')
def single_player():
    increment_active()
    username=session.get('username','tourist')
    return render_template('single.html',player_name=username,game_mode='single')

@app.route('/multi')
def multi_player():
    increment_active()
    username=session.get('username','tourist')
    return render_template('multi.html',player_name=username,game_mode='multi')

@socketio.on('disconnect')
def on_disconnect():
    print("[socket] client disconnected")
    decrement_active()

if __name__=='__main__':
    # 启动默认呼吸灯
    led_controller.start_breathing()
    socketio.run(app,host='0.0.0.0',port=5000,allow_unsafe_werkzeug=True,debug=True)
