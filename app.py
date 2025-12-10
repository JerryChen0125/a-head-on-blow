import os
import json
import tempfile
import socket
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from google import genai
from google.genai.errors import APIError

app = Flask(__name__)
CORS(app)

# --- 全域變數 ---
motor_command_queue = []
current_nfc_status = False   # 手機是否放著
is_focus_mode_active = False # 是否正在倒數計時 (專注模式)

# --- Gemini 設定 ---
client = None
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    try:
        client = genai.Client(api_key=api_key)
        print(">>> Gemini Client 初始化成功")
    except Exception as e:
        print(f"初始化 Gemini 失敗: {e}")
else:
    print("警告：未設定 GEMINI_API_KEY")

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

# --- API ---
@app.route('/', methods=['GET'])
def serve_html():
    return send_from_directory(os.getcwd(), 'LSA GUI.html')

@app.route('/api/analyze-ppt', methods=['POST'])
def analyze_ppt():
    if not client: return jsonify({"error": "Gemini Client 未初始化"}), 500
    if 'ppt_file' not in request.files: return jsonify({"error": "未收到檔案"}), 400
    uploaded_file = request.files['ppt_file']
    if uploaded_file.filename == '': return jsonify({"error": "空檔案"}), 400
    file_extension = os.path.splitext(uploaded_file.filename)[1].lower()
    try:
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file_path = temp_file.name
            uploaded_file.save(temp_file_path)
        file_object = client.files.upload(file=temp_file_path) 
        prompt = """
        請根據提供的檔案內容，為簡報者或學習者生成 3 個多選題 (選擇題)。
        嚴格以 JSON 格式回傳，格式範例如下 (請務必使用 "q" 作為問題欄位)：
        [
          {
            "q": "這裡放考題的第一個問題描述",
            "options": ["選項 A", "選項 B", "選項 C", "選項 D"],
            "correctAnswerIndex": 0
          }
        ]
        """
        target_model = 'gemini-2.5-flash'
        response = client.models.generate_content(model=target_model, contents=[prompt, file_object])
        json_text = response.text.strip()
        if json_text.startswith('```json'): json_text = json_text.strip('```json').strip()
        if json_text.startswith('```'): json_text = json_text.rstrip('```').strip()
        return jsonify(json.loads(json_text))
    except Exception as e:
        return jsonify({"error": f"處理失敗: {str(e)}"}), 500
    finally:
        if 'file_object' in locals() and file_object:
            try: client.files.delete(name=file_object.name)
            except: pass
        if 'temp_file_path' in locals() and os.path.exists(temp_file_path):
            try: os.remove(temp_file_path)
            except: pass

@app.route('/api/check-eye-penalty', methods=['GET'])
def check_eye_penalty():
    if os.path.exists("eye_penalty.flag"):
        try: os.remove("eye_penalty.flag"); return jsonify({"triggered": True})
        except: pass
    return jsonify({"triggered": False})

@app.route('/api/trigger-motor', methods=['POST'])
def trigger_motor():
    motor_command_queue.append("PUNISH")
    print(f">>> [Network] 收到處罰請求 (堆積: {len(motor_command_queue)})")
    return jsonify({"status": "queued"})

# === [修改] 樹梅派輪詢 API ===
# 現在會回傳「是否在專注模式」
@app.route('/api/pi-poll', methods=['GET'])
def pi_poll():
    cmd = "NONE"
    if len(motor_command_queue) > 0:
        cmd = motor_command_queue.pop(0)
    
    return jsonify({
        "command": cmd,
        "focus_mode": is_focus_mode_active  # 告訴樹梅派現在是不是專注時間
    })

@app.route('/api/update-nfc-status', methods=['POST'])
def update_nfc_status():
    global current_nfc_status
    data = request.get_json()
    is_placed = data.get('placed', False)
    if current_nfc_status != is_placed:
        print(f">>> [NFC] 狀態更新: {'已放置' if is_placed else '已移除'}")
    current_nfc_status = is_placed
    return jsonify({"status": "updated"})

@app.route('/api/get-nfc-status', methods=['GET'])
def get_nfc_status():
    return jsonify({
        "placed": current_nfc_status,
        "focus_mode": is_focus_mode_active
    })

# === [新增] 設定專注模式狀態 ===
@app.route('/api/set-focus-mode', methods=['POST'])
def set_focus_mode():
    global is_focus_mode_active
    data = request.get_json()
    is_focus_mode_active = data.get('active', False)
    print(f">>> [System] 專注模式已 {'開啟' if is_focus_mode_active else '關閉'}")
    return jsonify({"status": "success", "mode": is_focus_mode_active})

if __name__ == '__main__':
    my_ip = get_local_ip()
    print("="*60)
    print(f"✅ 伺服器已啟動 (Wi-Fi 模式)！")
    print(f"👉 請務必去修改樹梅派程式，將目標 IP 改為: http://{my_ip}:5000")
    print("="*60)
    app.run(host='0.0.0.0', port=5000, debug=True)