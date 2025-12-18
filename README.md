# 蠅頭痛擊
## Concept Development
我們每個組員都很容易分心，讀書時若手機放旁邊會造成讀書五分鐘滑手機一小時的情況，讀書效率極低。而且在這個競爭激烈的時代，若我們繼續維持這個壞習慣，會導致我們連書本目錄都讀不完，為此我們設計一套讓使用者可以提升專注力的系統。系統會自動偵測使用者有無分心，若分心時將觸發懲罰。

沿用大二下計算機組織的課程成果-機械手臂，加上可偵測NFC的RFID板，以及偵測人臉與動作的鏡頭，利用實體接線、Python與Raspberry pi 4(Model B)內建的NetworkManager建立無線區域網路，實現Windows與Raspberry pi的無線直連。


## Implementation Resources
* 機械手臂(MG996R-180度、冰棒棍和齒輪組成)
> 實體圖片 :

<img width="494" height="648" src="https://github.com/user-attachments/assets/c6d3f539-2ad5-4aea-9c66-a62ae3916117" />


* Raspberry pi 4
* 電池盒/電池
* 麵包板
* 鏡頭
* 杜邦線
* 蒼蠅拍
* 熱熔膠/熱熔膠槍
* RFID/感應卡



## Existing Library/Software
* Python : (3.13.5)
* OpenCV : (4.12.0.88)
* gpiozero : (2.0.1)
* pigpio : (1.78)
* API服務 : (gemini-2.5-flash)


## Implementation Process
> 架構圖 :
<img width="541" height="212" alt="LSA期末專案 drawio (2)" src="https://github.com/user-attachments/assets/56c78b81-6436-4268-a663-dc96c74223a4" />

> MG996R 腳位對照表 :

| MG996R | 樹莓派腳位(Physical Pin) | 功能(BCM GPIO) |
| :--- | :--- | :--- |
| Servo 1 | Pin 11 | GPIO 17 |
> RC522 腳位對照表 :

| RC522 | 樹莓派腳位 (Physical Pin) | 功能 (BCM GPIO) | 備註 |
| :--- | :--- | :--- | :--- |
| SDA(SS) | Pin 24 | GPIO 8 | 片選訊號 |
| SCK | Pin 23 | GPIO 11 | 時鐘 |
| MOSI | Pin 19 | GPIO 10 | 資料輸入 |
| MISO | Pin 21 | GPIO 9 | 資料輸出 |
| IRQ | (不接) | | 中斷 (用不到) |
| GND | Pin 6 | Ground | 接地 |
| RST | Pin 22 | GPIO 25 | 重置腳 |
| 3.3V | Pin 1 | 3.3V Power | 別接 5V |
> 整體線路圖 :

![2684D8CF-08D4-4537-A986-77E6828CC25C](https://github.com/user-attachments/assets/c243d1ce-2f53-4934-a699-39e7248431d4)



## Knowledge from Lecture
* iptables(阻擋下列IP連線)
  * Facebook : 31.13.87.36
  * Instagram : 31.13.87.174
  * X : 172.66.0.227 / 162.159.140.229
  * 動漫瘋 : 104.18.2.197 / 104.18.3.197
>電腦透過樹莓派對外連線，要使指令生效則須將規則寫在 FORWARD 上。指令 : `sudo iptables -A FORWARD -d [目標IP] -j DROP `，將目標IP替換成上述列出的 IP 。
* 建立網卡(用 NetworkManager 建立熱點連線)
  * 建立連線設定 : `sudo nmcli con add type wifi ifname wlan0 con-name "MyHotspot" autoconnect yes ssid "Pi_Filter"`
  * 設定加密模式與密碼 (WPA2A) : `sudo nmcli con modify "MyHotspot" 802-11-wireless.mode ap 802-11-wireless.band bg ipv4.method shared wifi-sec.key-mgmt wpa-psk wifi-sec.psk "12345678"`
  * 將樹莓派的 IP 固定為 192.168.4.1 (或是其他你喜歡的網段) : `sudo nmcli con modify "MyHotspot" ipv4.addresses 192.168.4.1/24`
  * 啟動熱點 : `sudo nmcli con up "MyHotspot"`

## Installation
* 電腦上 :
  * 安裝 Web API 相關套件 : `pip install flask flask-cors`
  * 安裝 Gemini API 開發套件 : `pip install google-generativeai`
  * 每次開啟 PowerShell 需輸入 : `$env:GEMINI_API_KEY = "你的API_KEY"`
  > GEMINI_API_KEY 可上 Google AI Studio ，左下方點選Get API key 來創建獲取。
* 樹莓派上 : 
  * OpenCV 視窗 : `sudo apt install libgl1`
  * OpenCV : `sudo apt install python3-opencv`
  * 編譯 Pigpio (解決馬達抖動) : `sudo apt install build-essential unzip`
  * iptables指令參考 (在實作中是腳本控制，位於face_monitor.py) :
     * `sudo iptables -A FORWARD -d 31.13.87.36 -j DROP`
     * `sudo iptables -A FORWARD -d 31.13.87.174 -j DROP`
     * `sudo iptables -A FORWARD -d 104.18.2.197 -j DROP`
     * `sudo iptables -A FORWARD -d 104.18.3.197 -j DROP`
     * `sudo iptables -A FORWARD -d 172.66.0.227 -j DROP`
     * `sudo iptables -A FORWARD -d 162.159.140.229 -j DROP`


## Usage
* 倒數計時器 : 在瀏覽器中開啟LSA GUI.html，在左側區塊設定讀書時間，並按下開始倒數。
* 檢測有無放置手機 : 在手機跟手機殼間放入感應卡，並將手機置於RFID上。
* AI生成題目 : 在瀏覽器中開啟LSA GUI.html，在右側區塊上傳讀書內容的PDF檔，並按下啟動AI分析。
* 鏡頭辨識動作 : 自動檢測使用者眼部。
* 機械手臂互動 : 觸發懲罰機制會自動執行。
* 網頁阻擋 : 倒數計時器開始後，電腦無法連線上FB/IG/X/動漫瘋，倒數結束後恢復連線。
> 簡易的運作流程圖 :

![photo_6197028030606150867_x](https://github.com/user-attachments/assets/8e17be24-e369-43c5-b803-bdb1e7ee1749)


## Challenge
一、 樹莓派環境與硬體層面
1. Python 版本過新導致套件災難

&emsp;困難：樹莓派 OS 預設為 Python 3.13 (非常新)，導致 pigpio、opencv-python 等硬體控制庫無法透過 pip 正常編譯安裝，環境一直報錯。<br>
>解決方案：放棄純 pip 安裝，改用系統級套件 (sudo apt install python3-opencv ...)。
建立虛擬環境時加上 -system-site-packages 參數，讓虛擬環境能繼承系統安裝好的穩定版驅動。

二、 跨裝置通訊與網路架構
1. USB 轉 TTL (Serial) 連線失敗

&emsp;困難：最初嘗試用 USB 線傳輸訊號，但遇到 Windows 驅動程式問題 (COM port not found, Access Denied)，且不穩定。<br>
>解決方案：放棄 Serial，改用網路架構。讓 PC 當 Server (Flask)，Pi 當 Client (Requests)，透過 HTTP API 溝通。<br>

2. 乙太網路直連不穩

&emsp;困難：改用網路線直連後，發生 Link is Down/Up 頻繁斷線，速度掉到 10Mbps，Ping 丟包率高。<br>
>解決方案：發現是樹莓派 4 的 EEE (節能乙太網路) 與 Windows 網卡衝突。
使用 ethtool --set-eee eth0 eee off 強制關閉節能模式。
最終為了展示穩定性，決定改用 Wi-Fi 區域網路取代實體線路。

三、軟體邏輯與前後端整合
1. 懲罰邏輯衝突

&emsp;困難：同時有「答錯題」、「閉眼」、「手機拿走」三種懲罰，容易造成馬達指令打架。<br>
>解決方案：在樹莓派建立優先級邏輯：答錯(單次) > 手機遺失(持續) > 閉眼(單次)。

四、 防火牆控制功能(iptables)
1. 如何控制 Windows 上網

&emsp;困難：原本想用網路線做 Gateway 控制，但設定繁瑣且線路不穩。<br>
>解決方案：改用邏輯控制：樹莓派透過 subprocess 執行 iptables 指令。
針對目標伺服器 IP (FB/IG/X/動漫瘋) 攔截轉發流量。


## 可延伸、改進方向
* 懲罰裝置升級
* 改進手機放置區的設計
* 設計避免使用者逃跑、提醒使用者暫停過久的隨身裝置



## Expenses
* RFID(含感應卡) : NT$150
* 齒輪 : NT$33
* 伺服馬達MG996R(三顆) : NT$297
* 電池座 : NT$10
* 麵包板 : NT$30
* 冰棒棍(兩包) : NT$64
* 熱熔膠槍 : NT$220
* 熱熔膠 : NT$45
* 蒼蠅拍 : NT$10
> 總花費約 : NT$859


## Job Assignment
| 組員 | 工作內容 |
| :--- | :--- |
| 陳章銓 | 電路設計 / 腳本設計 |
| 蔡瑋哲 | iptables設計 / GUI設計 / 上台報告 |
| 邱奕禓 | 主體發想 / 上台報告 |
| 蔡佳誼 | 主體發想 / ppt製作 / 上台報告 |
| 張詠筑 | 友情客串 DEMO |



## References
* [機械手臂雛型參考](https://projecthub.arduino.cc/milespeterson101/arduino-robotic-arm-8b8601?_gl=1*1j361wp*_up*MQ..*_ga*MTEyNzU2NDk1Ni4xNzQyMjY1NjU5*_ga_NEXN8H46L5*MTc0MjI2NTY1OS4xLjAuMTc0MjI2NTY1OS4wLjAuMTI5MjYxODA5MQ)

* [認識GPIO腳位](https://dic.vbird.tw/iot_pi/unit06.php)

* [RFID與樹莓派整合](https://micro.rohm.com/tw/deviceplus/connect/integrate-rfid-module-raspberry-pi/)

* [iptables上課講義參考](https://hackmd.io/@ncnu-opensource/book/https%3A%2F%2Fhackmd.io%2F%40jMUBFtWoRvenRfXiggZ8Tg%2FHk438Ruaee)



# 感謝BT以及助教們的意見提供跟技術指導 !
