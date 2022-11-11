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
    # python3(3.6, 우분투 18.04)에 꼭 필요한 것들을 먼저 설치하자
    python3 -m pip install cython
    python3 -m pip install scikit-build
    python3 -m pip install numpy # numpy를 설치하려면 CYthon, scikit-build 가 있어야 한다.
    python3 -m pip install opencv-python
    
    # tracker를 위한 가상환경을 생성
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