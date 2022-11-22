import asyncio
import cv2
import numpy as np
import os
import serial
import types
from threading import Thread, Event
from time import sleep


def gstreamer_pipeline(
    sensor_id=0,
    sensor_mode=3,
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=30,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d sensor-mode=%d ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            sensor_mode,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
)


class TrackerCamera:
    __ENCODE_PARAM = [int(cv2.IMWRITE_JPEG_QUALITY), 90]

    __PWM_X = 32
    __PWM_Z = 35

    __CAMERA_LEFT = 0
    __CAMERA_RIGHT = 1
    __LEFT = 'left'
    __RIGHT = 'right'
    __AXIS_X = 'x'
    __AXIS_Z = 'z'

    def __init__(self):
        self.__capture_thread = None
        self.__capture_thread_event = None
        self.__serial_thread = None
        self.__serial_thread_event = None
        self.__sources = {
            self.__LEFT: None,
            self.__RIGHT: None
        }
        self.__images = {
            self.__LEFT: None,
            self.__RIGHT: None
        }
        self.__coordinates = {
            self.__LEFT: 0,
            self.__RIGHT: 0
        }
        self.__serial_port = None

    def __get_serial_port(self):
        # GPIO UART라면 "/dev/ttyTHS1"
        for i in range(0, 5):
            __device_name = '/dev/ttyUSB' + str(i)
            if os.path.exists(__device_name):
                return __device_name
        return None

    def init_serial(self):
        self.__serial_port = serial.Serial(
            port=self.__get_serial_port(),
            baudrate=9600,
            bytesize=serial.EIGHTBITS,
            parity=serial.PARITY_NONE,
            stopbits=serial.STOPBITS_ONE,
        )
        print('SERIAL PORT OPENED')
        print(self.__serial_port)
        self.__write_line("x90")
        self.__write_line("z90")

    def __write_line(self, __line : str):
        if self.__serial_port is not None:
            if __line.endswith('\n'):
                print("WRITING TO SERIAL: " + __line)
                self.__serial_port.write(__line.encode())
            else:
                print("WRITING TO SERIAL: " + __line + '\n')
                self.__serial_port.write(__line.encode())
                self.__serial_port.write(b'\n')

    def release_serial(self):
        self.__serial_port.close()
        self.__serial_port = None

    def init_video(self):
        #self.__sources[self.__LEFT] = cv2.VideoCapture(0)
        #self.__sources[self.__RIGHT] = cv2.VideoCapture(1)
        self.__sources[self.__LEFT] = cv2.VideoCapture(
            gstreamer_pipeline(
                sensor_id=0,
                sensor_mode=3,
                flip_method=0,
                display_height=540,
                display_width=960,
            )
        )
        self.__sources[self.__RIGHT] = cv2.VideoCapture(
            gstreamer_pipeline(
                sensor_id=1,
                sensor_mode=3,
                flip_method=0,
                framerate=30,
                display_height=540,
                display_width=960,
            )
        )
        print(self.__sources)

    def release_video(self):
        if self.__sources[self.__LEFT] is not None:
            self.__sources[self.__LEFT].release()
        if self.__sources[self.__RIGHT] is not None:
            self.__sources[self.__RIGHT].release()

    def release(self):
        self.release_video()
        self.release_serial()

    # x 축 각도
    # z 축 각도
    #   int : -90 ~ 90(또는 0 ~ 180)
    def rotate_to(self, axis : str, angle : int):
        if axis == 'c':
            self.__write_line('x90')
            self.__write_line('z90')
        elif axis == 'x' or axis == 'z':
            __line = axis + str(angle)
            self.__write_line(__line)

    # x 축 각도 증분
    # z 축 각도 증분
    #   int
    def rotate(self, delta_x : int, delta_z : int):
        pass

    def get_coordinates(self):
        return self.__coordinates

    def process_serial_input(self):
        # 읽을 데이터가 없으면 그냥 돌아간다.
        if self.__serial_port.in_waiting <= 0:
            return
        __result = []
        __line = self.__serial_port.readline().decode()
        print("READ FROM SERIAL: " + __line)
        __axis = None
        __angle = 0
        for c in __line:
            if c == 'X' or c == 'Z':
                if __axis is not None:
                    __result.append((__axis, __angle))
                __axis = c
                __angle = 0
                continue
            if __axis is not None:
                if c.isdigit():
                    __angle = __angle * 10 + ord(c) - ord('0')
                else:
                    if c != 'X' or c != 'Z':
                        if __axis is not None:
                            __result.append((__axis, __angle))
                        __axis = None
                        __angle = 0
                    else:
                        if __axis is not None:
                            __result.append((__axis, __angle))
                        __axis = c
                        __angle = 0
        for axis, angle in __result:
            self.__coordinates[axis.lower()] = angle
            # TODO FIRE ANGEL CHANGED EVENT HERE

    def __serial_thread_loop(self):
        print("ENTERING LOOP OF SERIAL THREAD")
        while True:
            if self.__serial_thread_event is not None and self.__serial_thread_event.isSet():
                break
            if self.__serial_port is None:
                sleep(500)
                continue
            self.process_serial_input()
        print("END OF SERIAL THREAD")
    #
    # VIDEO CAPTURE
    #
    async def __capture_left(self):
        ret, frame = self.__sources[self.__LEFT].read()
        result, frame = cv2.imencode('.jpg', frame, self.__ENCODE_PARAM)
        return np.array(frame).tobytes()

    async def __capture_right(self):
        ret, frame = self.__sources[self.__RIGHT].read()
        result, frame = cv2.imencode('.jpg', frame, self.__ENCODE_PARAM)
        return np.array(frame).tobytes()

    async def __do_capture(self):
        __result = await asyncio.gather(
            self.__capture_left(),
            self.__capture_right()
        )
        return __result

    def __capture_thread_loop(self):
        print("INIT SERIAL PORT")
        self.init_serial()
        print("INIT VIDEO CAPTURES")
        self.init_video()
        print("GET NEW EVENT LOOP")
        __loop = asyncio.new_event_loop()
        __count = 0
        print("ENTERING LOOP")
        while True:
            if self.__capture_thread_event is not None and self.__capture_thread_event.isSet():
                break
            # Async COROUTINE __do_capture()를 호출하여 캡처
            capture_result = __loop.run_until_complete(self.__do_capture())
            __count = __count + 1
            # TODO
            #  UPDATE IMAGE AND FIRE EVENT
            self.__images[self.__LEFT] = capture_result[0]
            self.__images[self.__RIGHT] = capture_result[1]
            if __count < 2:
                print("ITERATION: " + str(__count))
                print(self.__images)
                #  멈추지 않아야...
                # self.stop_capture()
            sleep(10)
        print("LOOP ENDS, CLOSING LOOP")
        __loop.close()

    def start_capture(self):
        self.__capture_thread_event = Event()
        self.__capture_thread = Thread(target=self.__capture_thread_loop, )
        self.__capture_thread.start()
        self.__serial_thread_event = Event()
        self.__serial_thread = Thread(target=self.__serial_thread_loop, )
        self.__serial_thread.start()

    def stop_capture(self):
        self.__capture_thread_event.set()
        self.__serial_thread_event.set()

    def wait_for_capture_thread(self):
        self.__capture_thread.join()
        self.__serial_thread.join()

    #
    # channel : string : x | y
    #
    def get_images(self):
        print(self.__images[self.__LEFT].shape())
        print(self.__images[self.__RIGHT].shape())
        return self.__images[self.__LEFT], self.__images[self.__RIGHT]

    def init_pwm(self):
        pass

    def release_pwm(self):
        pass
