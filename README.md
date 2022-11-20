# tracker

# 시스템요구사항
* 서버
    * Jetson Nano
    * JetPack 4.5(Ubuntu 18.04)
* 클라이언트
    * 크롬 웹브라우저

# 소스
* 위치 : github : http://github.com/lightvil/tracker.git
* 실행할 준비
    * 
    ```
    # Serial Console 비활성화
    #    (/dev/ttyTHS1, PIN6: GND, PIN8:TX, PIN10 RX)
    # Arduio가 9600-N81
    systemctl stop nvgetty
    systemctl disable nvgetty
    udevadm trigger
    sudo usermod -a -G dialout $USER # /dev/ttyTHS1를 사용할 수 있게.
    #
    # REBOOT
    #

    # python3(3.6, 우분투 18.04)에 꼭 필요한 것들을 먼저 설치하자
    # serial 라이브러리 설치
    sudo apt-get install python3-pip
    python3 -m pip install --upgrade pip
  
    sudo apt-get install python3-venv
    sudo apt-get install python3-serial
    sudo apt-get install python-gevent python-greenlet
  
    pythop3 -m pip install wheel
    python3 -m pip install asyncio
    python3 -m pip install dill futures greenlet gevent await
    python3 -m pip install gevent-websocket
    python3 -m pip install cython
    python3 -m pip install scikit-build
    python3 -m pip install numpy # numpy를 설치하려면 CYthon, scikit-build 가 있어야 한다.
    python3 -m pip install opencv-python # 상당한 시간이 걸림
    python3 -m pip install opencv-contrib-python # for opencv imshow() Error
    python3 -m pip install pyserial              # for serial.Serial Class
    python3 -m pip install Flask
    python3 -m pip install pyopenssl
    python3 -m pip install flask-socketio
  

    #
    # tracker를 위한 가상환경을 생성
    #
    python3 -m venv venv
    # 위에서 생성한 가상환경으로 전환
    source venv /bin/activate
     
    # 필요한 패키지 설치
    pip install -r requirements.txt
  
    # 샐행
    ./tracker.sh start
    ```

* 패키지를 추가 하였다면 변경 내역을 push 해 둔다.
    ```
    pip freeze > requirements.txt
  
    git add requirements.txt
    git commit -m "패키지 추가"
    git push
    ```

# 모터제어를 위한 arduio
* 사용보드 : Arduino UNO R3
* 전원 : 5V4A
* 사용핀
    1. 5V: 전원용 5V
    1. GND: 전원용 GND핀 <--> JETSON 6 (GND)
    1. 0: UART RX        <--> JETSON 8 (TX)
    1. 1: UART TX        <--> JETSON 10(RX)
* 스케치 : `sketch_servo.ino` 참고

# Gyroscope : Arduio 33 Nano BLE
* 스케치 파일 : `sketch_ble_gyro.ino` 참고

# Flask : https
* SSL 키 생성 
    * Private 인증서 생성 : `openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365`
    * `app.py`에 적용