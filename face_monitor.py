import cv2
import time
import requests 
import subprocess 
import os
from time import sleep
from gpiozero import AngularServo, Device
from gpiozero.pins.pigpio import PiGPIOFactory
from mfrc522 import SimpleMFRC522

# ==========================================
# [網路設定] 請確認這跟 app.py 顯示的一樣
# ==========================================
PC_SERVER_URL = 'http://192.168.1.xxx:5000' # <--- ⚠️ 請務必確認這裡的 IP！

# ==========================================
# [黑名單設定]
# ==========================================
BLOCK_LIST = [
    "31.13.87.36",  # Facebook
    "31.13.87.174", # Instagram
    "34.110.155.89" # Dcard
]

# ==========================================
# [硬體設定]
# ==========================================
try:
    Device.pin_factory = PiGPIOFactory()
    print(">>> 成功連接 pigpio 服務！")
except Exception as e:
    print("!!! 錯誤: 無法連接 pigpio 服務，請輸入: sudo pigpiod")
    exit()

MIN_PULSE = 0.0005
MAX_PULSE = 0.0025
servo1 = AngularServo(17, min_angle=0, max_angle=180, min_pulse_width=MIN_PULSE, max_pulse_width=MAX_PULSE)
reader = SimpleMFRC522()

is_firewall_locked = False 

def control_firewall(should_block):
    global is_firewall_locked
    if should_block == is_firewall_locked: return

    if should_block:
        print(">>> 🚫 [防火牆] 啟動封鎖！")
        action = "-I" 
    else:
        print(">>> 🟢 [防火牆] 解除封鎖！")
        action = "-D" 

    for ip in BLOCK_LIST:
        try:
            cmd = f"sudo iptables {action} FORWARD -d {ip} -j DROP"
            subprocess.run(cmd, shell=True, check=True)
        except: pass
    is_firewall_locked = should_block

def execute_punishment(reason):
    print(f">>> ⚠️ 觸發 [{reason}]！執行處罰！")
    servo1.angle = 120
    sleep(0.2)
    servo1.angle = 0
    sleep(0.3)

# ==========================================
# [載入模型 & 開啟相機]
# ==========================================
servo1.angle = 0
sleep(0.5)
control_firewall(False) 

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
face_xml = os.path.join(BASE_DIR, 'haarcascade_frontalface_default.xml')
eye_xml = os.path.join(BASE_DIR, 'haarcascade_eye.xml')

face_cascade = cv2.CascadeClassifier(face_xml)
eye_cascade = cv2.CascadeClassifier(eye_xml)

print(">>> 正在開啟相機 (強制 V4L2 模式)...")

# ---------------------------------------------------------
# [關鍵修正] 加入 cv2.CAP_V4L2 參數
# ---------------------------------------------------------
cap = cv2.VideoCapture(0, cv2.CAP_V4L2)

# 如果 0 打不開，嘗試 1 (有時候 video0 是 metadata)
if not cap.isOpened():
    print(">>> 嘗試切換至 video1...")
    cap = cv2.VideoCapture(1, cv2.CAP_V4L2)

# 設定解析度 (VNC 建議低解析度，跑起來比較順)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print(">>> ❌ 嚴重錯誤：無法開啟相機！請檢查 USB 連接。")
else:
    print(">>> ✅ 相機已開啟！")

eye_closed_start = None
last_poll_time = 0 
last_rfid_check_time = 0
last_nfc_placed_state = False
last_tag_detect_time = 0      
NFC_TIMEOUT = 2.0             
is_in_focus_mode = False

print(f">>> 系統啟動，連線目標: {PC_SERVER_URL}")

try:
    while True: 
        current_time = time.time()
        is_quiz_violation = False
        is_eye_violation = False
        is_phone_missing_violation = False
        
        # [A] RFID
        if current_time - last_rfid_check_time > 0.2:
            try:
                (status, TagType) = reader.READER.MFRC522_Request(reader.READER.PICC_REQIDL)
                if status == reader.READER.MI_OK:
                    (status, uid) = reader.READER.MFRC522_Anticoll()
                    if status == reader.READER.MI_OK:
                        last_tag_detect_time = current_time 
            except: pass
            last_rfid_check_time = current_time

        is_currently_placed = (current_time - last_tag_detect_time) < NFC_TIMEOUT
        
        if is_currently_placed != last_nfc_placed_state:
            try:
                requests.post(f"{PC_SERVER_URL}/api/update-nfc-status", 
                              json={"placed": is_currently_placed}, timeout=0.5)
                print(f">>> [NFC] {'放置中' if is_currently_placed else '已移除'}")
            except: pass
            last_nfc_placed_state = is_currently_placed

        # [B] 網路輪詢
        if current_time - last_poll_time > 1.0:
            try:
                resp = requests.get(f"{PC_SERVER_URL}/api/pi-poll", timeout=1)
                if resp.status_code == 200:
                    data = resp.json()
                    is_in_focus_mode = data.get("focus_mode", False)
                    control_firewall(is_in_focus_mode)
                    if data.get("command") == "PUNISH":
                        is_quiz_violation = True
            except: pass
            last_poll_time = current_time

        if is_in_focus_mode and not is_currently_placed:
            is_phone_missing_violation = True

        # [C] 影像辨識 + 畫面顯示
        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(100, 100))
                
                if len(faces) > 0:
                    (x, y, w, h) = faces[0]
                    cv2.rectangle(frame, (x, y), (x+w, y+h), (255, 0, 0), 2)
                    
                    roi_gray = gray[y:y+h, x:x+w]
                    eyes = eye_cascade.detectMultiScale(roi_gray, 1.1, 5, minSize=(30, 30))
                    
                    if len(eyes) == 0:
                        # 閉眼
                        if eye_closed_start is None: eye_closed_start = time.time()
                        duration = time.time() - eye_closed_start
                        cv2.putText(frame, f"CLOSED: {duration:.1f}s", (x, y-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                        
                        if duration > 3.0: 
                            is_eye_violation = True 
                    else:
                        # 張眼
                        eye_closed_start = None
                        cv2.putText(frame, "OPEN", (x, y-10), 
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    eye_closed_start = None
                    cv2.putText(frame, "NO FACE", (20, 50), 
                                cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 255), 2)

                # 顯示畫面
                cv2.imshow("Monitor View", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

        # [D] 執行處罰
        if is_quiz_violation:
            execute_punishment("答錯")
        elif is_phone_missing_violation:
            print(">>> ⚠️ 專注中！手機遺失！")
            servo1.angle = 120
            sleep(0.2)
            servo1.angle = 0
            sleep(0.3)
        elif is_eye_violation:
            execute_punishment("閉眼")
            eye_closed_start = None 

        time.sleep(0.01)

except KeyboardInterrupt:
    print("\n程式結束，解鎖防火牆...")
    control_firewall(False)
finally:
    reader.GPIO.cleanup()
    servo1.close()
    if cap.isOpened(): cap.release()
    cv2.destroyAllWindows()